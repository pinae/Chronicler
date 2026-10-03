from django.db import models

from chronicle.models import Chronicle


class UsageEvent(models.Model):
    """One interaction with the GM/writer interface: raw material for the RQ2 study."""

    view = models.CharField(max_length=100)
    chronicle = models.ForeignKey(
        Chronicle, null=True, blank=True, related_name="+", on_delete=models.SET_NULL
    )
    t = models.PositiveIntegerField(null=True, blank=True)
    params = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.view} at {self.created_at:%Y-%m-%d %H:%M}"
