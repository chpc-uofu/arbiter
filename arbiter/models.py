import re
from django.db import models
from datetime import timedelta
from django.utils import timezone
from typing import List, Dict
from dataclasses import dataclass, asdict
from arbiter.utils import cores_to_nsec, gib_to_bytes


@dataclass
class Limit:
    name: str
    value: int

    UNSET_LIMIT = -1

    def json(self):
        return asdict(self)

    @staticmethod
    def memory_max(max_bytes: int) -> "Limit":
        return Limit(name="MemoryMax", value=max_bytes)
    
    @staticmethod
    def cpu_quota(usec_per_sec: int) -> "Limit":
        return Limit(name="CPUQuotaPerSecUSec", value=usec_per_sec)
    
    @staticmethod
    def to_json(*limits: "Limit") -> dict:
        return {l.name: l.value for l in limits}
    
    @staticmethod
    def from_json(json : dict) -> list["Limit"]:
        limits = []
        for name, value in json.items():
            limits.append(Limit(name=name, value=value))

        return limits
    
    @staticmethod
    def compare(limit1, limit2):
        if limit1.value < limit2.value:
            return limit1
        else:
            return limit2

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

    CPU_METRIC = 'systemd_unit_proc_cpu_usage_ns'
    MEM_METRIC = 'systemd_unit_proc_memory_bytes'

    def json(self):
        json_params = self.params.json() if self.params else None
        return {"query": self.query, "params": json_params}

    @staticmethod
    def raw_query(query:str) -> "QueryData":
        return QueryData(query=query, params=None)
    
    @staticmethod
    def build_query(lookback: timedelta, domain: str, params: QueryParameters) -> "QueryData":
        
        sum_by_labels = 'unit, instance, username'

        filters = f'instance=~"{domain}"'

        lookback = f'{int(lookback.total_seconds())}s'
        
        if params.user_whitelist:
            filters += f', user!~"{params.user_whitelist}"'
        
        if params.proc_whitelist:
            proc_filter = filters + f', proc=~"{params.proc_whitelist}"'
            cpu_proc = f"systemd_unit_proc_cpu_usage_ns{{{proc_filter}}}[{lookback}]"
            cpu_offset = f"(sum by ({sum_by_labels}) (rate({cpu_proc})))"
            mem_proc = f"systemd_unit_proc_memory_bytes{{{proc_filter}}}[{lookback}]"
            mem_offset = f"(sum by ({sum_by_labels}) (avg_over_time({mem_proc})))"

        if params.cpu_threshold is not None:
            cpu_unit = f'systemd_unit_cpu_usage_ns{{ {filters} }}[{lookback}]'
            cpu_total = f'(sum by ({sum_by_labels}) (rate({cpu_unit})))'
            if params.proc_whitelist:
                cpu = f'(({cpu_total} - {cpu_offset}) / {cores_to_nsec(params.cpu_threshold)}) > 1.0'
            else:
                cpu = f'({cpu_total} / {cores_to_nsec(params.cpu_threshold)}) > 1.0'

        if params.mem_threshold is not None:
            mem_unit = f'systemd_unit_memory_bytes{{{filters}}}[{lookback}]'
            mem_total = f'(sum by ({sum_by_labels}) (avg_over_time({mem_unit})))'
            if params.proc_whitelist:
                mem = f'(({mem_total} - {mem_offset}) / {gib_to_bytes(params.mem_threshold)}) > 1.0'
            else:
                mem = f'({mem_total} / {gib_to_bytes(params.mem_threshold)}) > 1.0'

        if params.mem_threshold and params.cpu_threshold:
            query = f'{cpu} or {mem}'
        elif params.cpu_threshold:
            query = cpu
        elif params.mem_threshold:
            query = mem
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
    penalty_constraints = models.JSONField(null=False)
    penalty_duration = models.DurationField(null=True, default=timedelta(minutes=15))

    repeated_offense_scalar = models.FloatField(null=True, default=1.0)
    repeated_offense_lookback = models.DurationField(null=True, default=timedelta(hours=3))
    grace_period = models.DurationField(null=True, default=timedelta(minutes=5))

    query_data = models.JSONField()

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
        query = f'systemd_unit_cpu_usage_ns{{instance=~"{self.domain}}}"'
        self.query_params = {"raw": query}
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
    uid = models.IntegerField(null=True)
    last_applied = models.JSONField(default=dict)

    def save(self, **kwargs):
        match = re.search(r"user-(\d+)\.slice", self.unit)
        if match:
            self.uid = int(match.group(1))
        return super().save(**kwargs)

    def __str__(self) -> str:
        return f"{self.username}@{self.host}"


class Violation(models.Model): #TODO violation
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


class Event(models.Model):
    class EventTypes(models.TextChoices):
        APPLY = ("Apply", "Limit Applied on a Target")
        EVALUATION = ("Eval", "Policies Evaluated")

    type = models.CharField(max_length=255, choices=EventTypes.choices)
    timestamp = models.DateTimeField(auto_now=True)
    data = models.JSONField()
