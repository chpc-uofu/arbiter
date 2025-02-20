from django.contrib import admin
from arbiter3.arbiter import models


@admin.register(models.Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "domain", "is_base_policy"]


@admin.register(models.Violation)
class ViolationAdmin(admin.ModelAdmin):
    list_display = ["target", "policy",
                    "timestamp", "expiration", "is_base_status"]


@admin.register(models.Target)
class TargetAdmin(admin.ModelAdmin):
    list_display = ["username", "host"]
