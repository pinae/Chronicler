from typing import Any

from django.db import models, transaction
from django.db.models import Q


def shorten(text: str, max_length: int = 50) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(" ", 1)[0] + "…"


class ChronicleKind(models.TextChoices):
    SESSION = "session"
    LITERATURE = "literature"
    MEDIA = "media"


class EntityKind(models.TextChoices):
    CHARACTER = "character"
    OBJECT = "object"
    PLACE = "place"
    FACTION = "faction"
    SECRET = "secret"
    SOURCE = "source"


# Literature and media have one implicit audience member; sessions have one player per human.
IMPLICIT_AUDIENCE = {ChronicleKind.LITERATURE: "reader", ChronicleKind.MEDIA: "public"}


class Chronicle(models.Model):
    """One story-world record: a play session, a literary work, or a media corpus about one event."""

    kind = models.CharField(max_length=20, choices=ChronicleKind)
    title = models.CharField(max_length=200)
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(kind__in=ChronicleKind.values), name="chronicle_kind_is_known"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.kind})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        is_new = self._state.adding
        with transaction.atomic():
            super().save(*args, **kwargs)
            if is_new:
                self.create_implicit_audience()

    def create_implicit_audience(self) -> None:
        audience_name = IMPLICIT_AUDIENCE.get(ChronicleKind(self.kind))
        if audience_name:
            self.players.create(name=audience_name, implicit=True)


class Player(models.Model):
    """One audience member. Sessions: one per human at the table.
    Literature / media: exactly one implicit row ('reader' / 'public'), created with the chronicle."""

    chronicle = models.ForeignKey(Chronicle, related_name="players", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    implicit = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name


class Entity(models.Model):
    """A character, object, place, faction, secret or source referenced by beats."""

    chronicle = models.ForeignKey(Chronicle, related_name="entities", on_delete=models.CASCADE)
    kind = models.CharField(max_length=20, choices=EntityKind)
    canonical_name = models.CharField(max_length=200)
    aliases = models.JSONField(default=list, blank=True)
    introduced_at_t = models.PositiveIntegerField()

    class Meta:
        verbose_name_plural = "entities"
        constraints = [
            models.CheckConstraint(condition=Q(kind__in=EntityKind.values), name="entity_kind_is_known"),
        ]

    def __str__(self) -> str:
        return f"{self.canonical_name} ({self.kind})"


class Utterance(models.Model):
    """One thing said at the table, one paragraph of prose, or one article passage."""

    chronicle = models.ForeignKey(Chronicle, related_name="utterances", on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    # Neither speaker set means the GM or the narrator is speaking.
    speaker_player = models.ForeignKey(Player, null=True, blank=True, on_delete=models.SET_NULL)
    speaker_entity = models.ForeignKey(Entity, null=True, blank=True, on_delete=models.SET_NULL)
    text = models.TextField()
    source = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["chronicle", "order"], name="utterance_order_unique_per_chronicle"
            ),
            models.CheckConstraint(
                condition=Q(speaker_player__isnull=True) | Q(speaker_entity__isnull=True),
                name="utterance_has_at_most_one_speaker",
            ),
        ]

    def __str__(self) -> str:
        return f"#{self.order} {shorten(self.text)}"
