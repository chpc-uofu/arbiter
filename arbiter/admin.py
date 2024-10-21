from django.contrib import admin
from arbiter import models


@admin.register(models.Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "domain", "is_base_policy"]