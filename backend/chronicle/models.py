from typing import TYPE_CHECKING, Any

from django.db import models, transaction
from django.db.models import Q

if TYPE_CHECKING:
    from chronicle.beat_log import BeatDraft


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

    def append(self, draft: "BeatDraft", t: int | None = None) -> "Beat":
        """Append a beat at the next `t`; an explicit `t` must be exactly that next value."""
        # Imported here because the beat log builds on the models defined in this module.
        from chronicle.beat_log import append_beat

        return append_beat(self, draft, t)


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


class SourceKind(models.TextChoices):
    NARRATION = "narration"
    ACTION = "action"
    CLAIM = "claim"


UNKNOWN_PREDICATE = "unknown"
QUARANTINE_TAG = "quarantined"


class ImmutableBeat(Exception):
    """Beats are append-only: a correction is a new beat, never an edit."""


class Beat(models.Model):
    """One formal fact about the narrated world. `t` is its position in the chronicle, from 1."""

    chronicle = models.ForeignKey(Chronicle, related_name="beats", on_delete=models.CASCADE)
    t = models.PositiveIntegerField()
    pred = models.CharField(max_length=50)
    args = models.JSONField()
    tags = models.JSONField(default=list, blank=True)
    source_utterance = models.ForeignKey(Utterance, related_name="beats", on_delete=models.PROTECT)
    source_kind = models.CharField(max_length=20, choices=SourceKind)
    text = models.TextField(blank=True)
    confidence = models.FloatField(default=1.0)
    # The predicate as ingested, kept when it was not in the vocabulary and the beat was quarantined.
    original_pred = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["t"]
        constraints = [
            models.UniqueConstraint(fields=["chronicle", "t"], name="beat_t_unique_per_chronicle"),
            models.CheckConstraint(
                condition=Q(source_kind__in=SourceKind.values), name="beat_source_kind_is_known"
            ),
        ]

    def __str__(self) -> str:
        return f"t={self.t} {self.pred}: {shorten(self.text)}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding:
            raise ImmutableBeat(f"beat t={self.t} is already stored and cannot change")
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ImmutableBeat(f"beat t={self.t} cannot be deleted")

    @property
    def is_quarantined(self) -> bool:
        return QUARANTINE_TAG in self.tags
