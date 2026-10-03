from django.contrib import admin

from gm_ui.models import UsageEvent
from narrative_engine.read_only_admin import ReadOnlyAdmin


@admin.register(UsageEvent)
class UsageEventAdmin(ReadOnlyAdmin):
    list_display = ["view", "chronicle", "t", "params", "created_at"]
    list_filter = ["view"]
