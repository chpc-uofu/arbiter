from datetime import timedelta
from dataclasses import dataclass, asdict

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

from arbiter3.arbiter.utils import get_uid, split_port
from arbiter3.arbiter.query import Q, increase, sum_by, sum_over_time
from arbiter3.arbiter.conf import WARDEN_PORT, PROMETHEUS_CONNECTION, WARDEN_JOB
from arbiter3.arbiter.prop import CPU_QUOTA, MEMORY_MAX

Limits = dict[str, any]
UNSET_LIMIT = -1



@dataclass
class QueryParameters:
    cpu_threshold: float  # seconds
    mem_threshold: int   # bytes
    proc_whitelist: str | None = None  # prom matcher regex
    user_whitelist: str | None = None  # prom matcher regex
    use_pss_metric : bool = False

    def json(self):
        return asdict(self)


@dataclass
class QueryData:
    query: str
    params: QueryParameters | None
    is_raw_query : bool = False

    def json(self):
        json_params = self.params.json() if self.params else None

        return {"query": self.query, "params": json_params, "is_raw_query": self.is_raw_query}

    @staticmethod
    def raw_query(query: str, params = None) -> "QueryData":
        return QueryData(query=query, params=params, is_raw_query=True)
    
    @staticmethod
    def base_query(base_policy) -> "QueryData":

        query = Q('cgroup_warden_cpu_usage_seconds').like(instance=base_policy.domain)
        params = None
        
        if stored_params := base_policy.query_data.get("params"):
            whitelist = stored_params.get("user_whitelist")
            
            if whitelist:
                query = query.not_like(username=whitelist)
            params = QueryParameters(0, 0, user_whitelist=whitelist)

        return QueryData(query=str(query), params=params, is_raw_query=True)

    @staticmethod
    def build_query(lookback: timedelta, domain: str, params: QueryParameters) -> "QueryData":
        """
        Unaccounted for cpu usage should not be counted against a user. This can happen 
        when a process starts and ends in-between a polling period, or for some other reason.
        Arbiter2 opted to ignore this usage, as it may have been whitelisted usage anyways.

        We calculate this delta in usage between the unit cpu usage and the sum of all of the
        processes. We can then assign this value as a 'unknown' process for display purposes.

        If we have a process whitelist, we thus calculate violations __only__ with the 
        whitelisted usage.

        We do not want to whitelist memory usage, as that cannot be 'taken' back.  
        """

        like_filters = {'instance':domain}
        notlike_filters = dict()

        lookback = int(lookback.total_seconds())

        if params.user_whitelist:
            notlike_filters['username'] = params.user_whitelist

        if params.proc_whitelist:
            notlike_filters['proc'] = params.proc_whitelist
            cpu_query = sum_by(
                increase(
                    Q('cgroup_warden_proc_cpu_usage_seconds').like(**like_filters).not_like(**notlike_filters).over(f'{lookback}s')
                ) / lookback > params.cpu_threshold, 
                "username", "instance", "cgroup", "job"
            )
        else:
            cpu_query = increase(Q('cgroup_warden_cpu_usage_seconds').like(**like_filters).not_like(**notlike_filters).over(f'{lookback}s')) / lookback > params.cpu_threshold

        granularity = 30

        datapoints = lookback // granularity

        if datapoints:
            mem_range = f'{lookback}s:{granularity}s'
        else:
            datapoints = lookback
            mem_range = f'{lookback}s:1s'

        if params.proc_whitelist:
            mem_metric = 'cgroup_warden_proc_memory_pss_bytes' #if params.use_pss_metric else 'cgroup_warden_proc_memory_usage_bytes'
        else:
            mem_metric = 'cgroup_warden_memory_usage_bytes'

        mem_query = sum_by(
            sum_over_time(
                Q(mem_metric).like(**like_filters).not_like(**notlike_filters).over(mem_range)
            ) / datapoints, 
            "username", "instance", "cgroup", "job"
        ) > params.mem_threshold

        if params.mem_threshold and params.cpu_threshold:
            query = cpu_query.lor(mem_query)
        elif params.cpu_threshold:
            query = cpu_query
        elif params.mem_threshold:
            query = mem_query
        else:
            query = None

        return QueryData(query=str(query), params=params, is_raw_query=False)


class Policy(models.Model):
    class Meta:
        verbose_name_plural = "Policies"
        permissions = [
            ("arbiter_view", "Arbiter Viewer"),
            ("arbiter_administrator", "Arbiter Administrator"),
        ]

    is_base_policy = models.BooleanField(default=False, null=False, editable=False)

    name = models.CharField(max_length=255, unique=True, help_text="Name of the policy")
    domain = models.CharField(max_length=1024, help_text="regex for the hostname/instance where this policy is in affect")
    lookback = models.DurationField(
        default=timedelta(minutes=15), 
        help_text="How far back arbiter evaluates user's usage (e.g. if a user's average usage is above the threshold(s) for this amount of time, they will be in violation)"
        )
    
    description = models.TextField(max_length=1024, blank=True, help_text="optional description for the purpose/overview of this policy")
    penalty_constraints: Limits = models.JSONField(null=False, help_text="The limits that will be applied at each tier of penalty . Repeated violation ups the penalty tier.")
    penalty_duration = models.DurationField(null=True, default=timedelta(minutes=15), help_text="how long a user will be in penalty status upon violation (can scale depending on other settings)")

    repeated_offense_scalar = models.FloatField(
        null=True, 
        default=1.0, 
        help_text="How much a penalty's duration scales each repeated violation (e.g. if set to 1.0 the duration will double the second repeat violation and triple for the third repeat violation)"
        )
    
    repeated_offense_lookback = models.DurationField(
        null=True, 
        default=timedelta(hours=3),
        help_text="How far back arbiter looks at violation history (e.g. if set to 3 hours and the current violator has 2 violations in the past 3 hours, the user will be in tier 2 penalty status and with a proportionally scaled duration )"
        )
    
    grace_period = models.DurationField(null=True, default=timedelta(minutes=5), help_text="for how long after leaving penalty status the user is unable to violate this policy for")

    query_data = models.JSONField()
    active = models.BooleanField(default=True, help_text="Whether or not this policy gets evaluated")
    watcher_mode = models.BooleanField(default=False, help_text="If set, the policy will only report/email violations and not enforce limits")

    def __str__(self):
        return f'{self.name}'

    @property
    def query(self):
        query_str = self.query_data.get("query", None)

        return query_str

    @property
    def cpu_threshold(self):
        return self.query_data.get("params", {}).get("cpu_threshold")

    @property
    def mem_threshold(self):
        return self.query_data.get("params", {}).get("mem_threshold")
    
    @property
    def proc_whitelist(self):
        return self.query_data.get("params", {}).get("proc_whitelist")

    @property
    def affected_hosts(self):
        up_query = f"up{{job=~'{WARDEN_JOB}', instance=~'{self.domain}'}} > 0"
        result = PROMETHEUS_CONNECTION.query(up_query)
        return [split_port(r.metric["instance"]) for r in result]


class BasePolicy(Policy):
    class Meta:
        proxy = True

    class BasePolicyManager(models.Manager):
        def get_queryset(self):
            return super().get_queryset().filter(is_base_policy=True)

    objects = BasePolicyManager()

    def save(self, **kwargs):
        self.is_base_policy = True
        
        self.query_data = QueryData.base_query(self).json()
        return super().save(**kwargs)


class UsagePolicy(Policy):

    class UsagePolicyManager(models.Manager):
        def get_queryset(self):
            return super().get_queryset().filter(is_base_policy=False)

    objects = UsagePolicyManager()

    class Meta:
        proxy = True

    def save(self, **kwargs):
        self.is_base_policy = False
        return super().save(**kwargs)


class Target(models.Model):
    class Meta:
        verbose_name_plural = "Targets"
        constraints = [
            models.UniqueConstraint(
                fields=["host", "username"], name="unique_target"
            ),
        ]

    unit = models.CharField(max_length=255)
    port = models.IntegerField(null=True)
    host = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    limits: Limits = models.JSONField(default=dict)

    def update_limit(self, propname, propvalue):
        if propvalue == UNSET_LIMIT:
            self.limits.pop(propname, None)
        else:
            self.limits[propname] = propvalue

    def update_limits(self, limits: Limits):
        for propname, propvalue in limits.items():
            self.update_limit(propname, propvalue)

    @property
    def endpoint(self):
        return f'{self.host}:{self.port or WARDEN_PORT}'

    @property
    def instance(self):
        return f"{self.host}{f':{self.port}' if self.port else ''}"

    @property
    def uid(self):
        return get_uid(self.unit)

    def __str__(self) -> str:
        return f"{self.username}@{self.host}"


class Violation(models.Model):
    is_base_status = models.BooleanField(default=False, editable=False)

    target = models.ForeignKey(Target, on_delete=models.CASCADE)
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE)
    expiration = models.DateTimeField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    offense_count = models.IntegerField(default=1, null=True)

    @property
    def duration(self) -> timedelta:
        return self.expiration - self.timestamp

    @property
    def limits(self) -> Limits:
        tiers = self.policy.penalty_constraints['tiers']

        if self.policy.is_base_policy:
            return tiers[0]

        penalty_tier = min(self.offense_count-1, len(tiers)-1)
        return tiers[penalty_tier]
    
    @property
    def penalty_tier(self) -> int: 
        tiers = self.policy.penalty_constraints['tiers']
        return min(self.offense_count-1, len(tiers)-1)

    @property
    def expired(self) -> bool:
        if not self.expiration:
            return False
        return self.expiration < timezone.now()

    def __str__(self):
        return f'{self.target} - {self.policy}'


class Event(models.Model):
    class EventTypes(models.TextChoices):
        APPLY = ("Apply", "Limit Applied on a Target")
        EVALUATION = ("Eval", "Policies Evaluated")

    type = models.CharField(max_length=255, choices=EventTypes.choices)
    timestamp = models.DateTimeField(auto_now=True)
    data = models.JSONField()   
    
# class ArbUser(User):
#     class Meta:
#         permissions = [
#             ("view_dashboard","can see user usage/violations on dashboard"),
#             ("execute_command","execute commands"),
#         ]
