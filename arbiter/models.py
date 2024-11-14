from datetime import timedelta
from dataclasses import dataclass, asdict

from django.db import models
from django.utils import timezone

from arbiter.utils import get_uid


Limits = dict[str, any]
UNSET_LIMIT = -1
CPU_QUOTA = "CPUQuotaPerSecUSec"
MEMORY_MAX = "MemoryMax"


@dataclass
class QueryParameters:
    cpu_threshold: int  # nanoseconds
    mem_threshold: int  # bytes
    proc_whitelist: str | None = None # prom matcher regex
    user_whitelist: str | None = None # prom matcher regex

    def json(self):
        return asdict(self)


@dataclass
class QueryData:
    query: str
    params: QueryParameters | None

    def json(self):
        json_params = self.params.json() if self.params else None
        return {"query": self.query, "params": json_params}

    @staticmethod
    def raw_query(query:str) -> "QueryData":
        return QueryData(query=query, params=None)
    
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

        filters = f'instance=~"{domain}"'

        lookback = f'{int(lookback.total_seconds())}s'

        if params.user_whitelist:
            filters += f', user!~"{params.user_whitelist}"'

        if params.proc_whitelist:
            cpu_query = f'sum by (username, instance, unit) (rate(systemd_unit_proc_cpu_usage_ns{{{filters}, proc!~"{params.proc_whitelist}"}}[{lookback}]) / {params.cpu_threshold}) > 1.0'
        else:
            cpu_query = f'sum by (username, instance, unit) (rate(systemd_unit_cpu_usage_ns{{{filters}}}[{lookback}]) / {params.cpu_threshold}) > 1.0'

        mem_query = f'sum by (username, instance, unit) (avg_over_time(systemd_unit_memory_current_bytes{{{filters}}}[{lookback}]) / {params.mem_threshold}) > 1.0'

        if params.mem_threshold and params.cpu_threshold:
            query = f'({cpu_query}) or ({mem_query})'
        elif params.cpu_threshold:
            query = cpu_query
        elif params.mem_threshold:
            query = mem_query
        else:
            query = None
        
        return QueryData(query=query, params=params)


class Policy(models.Model):
    class Meta:
        verbose_name_plural = "Policies"

    is_base_policy = models.BooleanField(default=False, null=False, editable=False)

    name = models.CharField(max_length=255, unique=True)
    domain = models.CharField(max_length=1024)
    lookback = models.DurationField(default=timedelta(minutes=15))
    description = models.TextField(max_length=1024, blank=True)
    penalty_constraints: Limits = models.JSONField(null=False)
    penalty_duration = models.DurationField(null=True, default=timedelta(minutes=15))

    repeated_offense_scalar = models.FloatField(null=True, default=1.0)
    repeated_offense_lookback = models.DurationField(null=True, default=timedelta(hours=3))
    grace_period = models.DurationField(null=True, default=timedelta(minutes=5))

    query_data = models.JSONField()
    active  = models.BooleanField(default=True, help_text="Whether or not this policy gets evaluated")

    @property
    def query(self):
        query_str = self.query_data.get("query", None)

        return query_str



class BasePolicy(Policy):
    class Meta:
        proxy = True

    class BasePolicyManager(models.Manager):
        def get_queryset(self):
            return super().get_queryset().filter(is_base_policy=True)
        
    objects =  BasePolicyManager()

    def save(self, **kwargs):
        self.is_base_policy = True
        query = f'systemd_unit_cpu_usage_ns{{instance=~"{self.domain}"}}'
        self.query_data = QueryData.raw_query(query).json()
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
                fields=["unit", "host", "username"], name="unique_target"
            ),
        ]

    unit = models.CharField(max_length=255)
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
