from django.db import models


class LLMCall(models.Model):
    """Every language-model request and its response (concept §8.4). An identical request is
    answered from this table, which makes evaluation runs reproducible and re-runs free."""

    request_hash = models.CharField(max_length=64, unique=True)
    model = models.CharField(max_length=100)
    endpoint = models.CharField(max_length=50)
    request = models.JSONField()
    response = models.JSONField()
    server_version = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "LLM call"

    def __str__(self) -> str:
        return f"{self.endpoint} {self.model} {self.request_hash[:12]}"
