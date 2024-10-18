import re
from django.db import models
from datetime import timedelta
from django.utils import timezone
from typing import List, Dict


class Limit:
    def __init__(self, name:str, value:int):
        self.name = name
        self.value = value

    @staticmethod
    def memory_max(max_bytes: int) -> "Limit":
        return Limit(name="MemoryMax", value=max_bytes)
    
    @staticmethod
    def cpu_quota(usec_per_sec: int) -> "Limit":
        return Limit(name="CPUQuotaPerSecUSec", value=usec_per_sec)
    
    @staticmethod
    def to_json(*args: "Limit") -> List[Dict]:
        return [dict(name=a.name, value=a.value) for a in args]
    

class Policy(models.Model):
    class Meta:
        verbose_name_plural = "Policies"

    is_base_policy = models.BooleanField(default=False, null=False, editable=False)

    name = models.CharField(max_length=255, unique=True)
    domain = models.CharField(max_length=1024)
    description = models.TextField(max_length=1024, blank=True)

    penalty_constraints = models.JSONField()
    penalty_duration = models.DurationField(null=True)

    repeated_offense_scalar = models.FloatField(null=True)
    repeated_offense_lookback = models.DurationField(null=True)
    grace_period = models.DurationField(null=True)

    query = models.TextField(max_length=1024, blank=False, null=False)
    query_parameters = models.JSONField(null=True)


class BasePolicyManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_base_policy=True)


class BasePolicy(Policy):
    class Meta:
        proxy = True
    
    objects =  BasePolicyManager()

    def save(self, **kwargs):
        self.is_base_policy = True
        query = f'systemd_unit_cpu_usage_ns{{instance=~"{self.domain}}}"'
        self.query_params = {"raw": query}
        return super().save(**kwargs)


class UsagePolicyManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_base_policy=False)


class UsagePolicy(Policy):
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
    last_applied = models.JSONField()

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
