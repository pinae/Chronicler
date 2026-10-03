from django.db import models

from chronicle.models import Beat, Chronicle, Player, Utterance
from schemas.models import Schema, Step


class HypothesisStatus(models.TextChoices):
    LIVE = "live"
    COMPLETE = "complete"
    REFUTED = "refuted"
    PRUNED = "pruned"
    MERGED = "merged"


class Hypothesis(models.Model):
    """A partial match of a schema against the chronicle. Time-indexed through created_at_t,
    status_changed_at_t and the t of its fills, so the lattice at any t is a filter."""

    chronicle = models.ForeignKey(Chronicle, related_name="hypotheses", on_delete=models.CASCADE)
    schema = models.ForeignKey(Schema, on_delete=models.PROTECT)
    binding = models.JSONField()  # {"T": 17, "V": 9, "S": null}  (null = open)
    weight = models.FloatField()
    status = models.CharField(max_length=20, choices=HypothesisStatus, default=HypothesisStatus.LIVE)
    created_at_t = models.PositiveIntegerField()
    status_changed_at_t = models.PositiveIntegerField(null=True, blank=True)
    refuted_by = models.ForeignKey(Beat, null=True, blank=True, related_name="+", on_delete=models.SET_NULL)
    voiced_by = models.ForeignKey(Player, null=True, blank=True, related_name="+", on_delete=models.SET_NULL)
    voiced_in = models.ForeignKey(
        Utterance, null=True, blank=True, related_name="+", on_delete=models.SET_NULL
    )
    refines = models.ForeignKey(
        "self", null=True, blank=True, related_name="refinements", on_delete=models.SET_NULL
    )
    # Empty: the unfiltered lattice over every beat. Set: the lattice of what this player has seen.
    for_player = models.ForeignKey(Player, null=True, blank=True, related_name="+", on_delete=models.CASCADE)
    # Merging never deletes: the merged hypothesis points to the one that absorbed it.
    merged_into = models.ForeignKey(
        "self", null=True, blank=True, related_name="absorbed", on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name_plural = "hypotheses"

    def __str__(self) -> str:
        roles = ", ".join(
            f"{role}={entity if entity is not None else '?'}" for role, entity in self.binding.items()
        )
        return f"{self.schema.slug}({roles}) {self.status}"


class StepFill(models.Model):
    """Which beat filled which step of which hypothesis. Time-indexed via beat.t."""

    hypothesis = models.ForeignKey(Hypothesis, related_name="fills", on_delete=models.CASCADE)
    step = models.ForeignKey(Step, on_delete=models.PROTECT)
    beat = models.ForeignKey(Beat, related_name="+", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.step} filled at t={self.beat.t}"
