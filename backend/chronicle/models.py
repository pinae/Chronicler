import secrets
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

    def visible_to(self, player: "Player | None", t: int) -> "models.QuerySet[Beat]":
        """The beats an audience knew at time t: one player's view, or with `None` the table view
        (common knowledge: beats every player of the chronicle knew)."""
        known_by_then = Q(grants__t__lte=t)
        if player is not None:
            return self.beats.filter(known_by_then, grants__player=player).distinct().order_by("t")
        player_count = self.players.count()
        if player_count == 0:
            return self.beats.none()
        knowing_players = models.Count("grants__player", filter=known_by_then, distinct=True)
        return self.beats.annotate(knowing_players=knowing_players).filter(knowing_players=player_count)

    def append(self, draft: "BeatDraft", t: int | None = None) -> "Beat":
        """Append a beat at the next `t`; an explicit `t` must be exactly that next value."""
        # Imported here because the beat log builds on the models defined in this module.
        from chronicle.beat_log import append_beat

        return append_beat(self, draft, t)


def new_pseudonym() -> str:
    return f"player-{secrets.token_hex(4)}"


class Player(models.Model):
    """One audience member. Sessions: one per human at the table.
    Literature / media: exactly one implicit row ('reader' / 'public'), created with the chronicle."""

    chronicle = models.ForeignKey(Chronicle, related_name="players", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    implicit = models.BooleanField(default=False)
    # A recorded table may be studied only once every human at it agreed (RQ2, WP-056).
    consent_given_at = models.DateTimeField(null=True, blank=True)
    # Stands in for the name in every study export; random, so it reveals nothing.
    pseudonym = models.CharField(max_length=20, unique=True, default=new_pseudonym, editable=False)

    def __str__(self) -> str:
        return self.name


class Entity(models.Model):
    """A character, object, place, faction, secret or source referenced by beats."""

    chronicle = models.ForeignKey(Chronicle, related_name="entities", on_delete=models.CASCADE)
    kind = models.CharField(max_length=20, choices=EntityKind)
    canonical_name = models.CharField(max_length=200)
    # Stable short name for fixtures, ground truth and URLs, e.g. "aldric".
    slug = models.SlugField(max_length=100, blank=True)
    aliases = models.JSONField(default=list, blank=True)
    introduced_at_t = models.PositiveIntegerField()

    class Meta:
        verbose_name_plural = "entities"
        constraints = [
            models.CheckConstraint(condition=Q(kind__in=EntityKind.values), name="entity_kind_is_known"),
            models.UniqueConstraint(
                fields=["chronicle", "slug"], condition=~Q(slug=""), name="entity_slug_unique_per_chronicle"
            ),
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

    def known_by_chars_at(self, t: int) -> "models.QuerySet[Entity]":
        return Entity.objects.filter(knowledge__beat=self, knowledge__t__lte=t).distinct()

    def known_by_players_at(self, t: int) -> "models.QuerySet[Player]":
        return Player.objects.filter(knowledge__beat=self, knowledge__t__lte=t).distinct()


class EntityAttribute(models.Model):
    """Derived view of entity state (`is`, `has`, `is_at`), rebuilt from beats. Keeps provenance."""

    entity = models.ForeignKey(Entity, related_name="attributes", on_delete=models.CASCADE)
    key = models.CharField(max_length=100)
    value = models.JSONField()
    source_beat = models.ForeignKey(Beat, related_name="+", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.key} = {self.value}"


class ImmutableGrant(Exception):
    """Scope grants are append-only: knowledge is gained, never edited."""


class ScopeGrant(models.Model):
    """Append-only: 'subject knows beat since t'. Scope at t = the grants with grant.t <= t."""

    beat = models.ForeignKey(Beat, related_name="grants", on_delete=models.CASCADE)
    character = models.ForeignKey(
        Entity, null=True, blank=True, related_name="knowledge", on_delete=models.CASCADE
    )
    player = models.ForeignKey(
        Player, null=True, blank=True, related_name="knowledge", on_delete=models.CASCADE
    )
    t = models.PositiveIntegerField()
    # The `learns` beat through which the knowledge was gained, if any.
    via_beat = models.ForeignKey(Beat, null=True, blank=True, related_name="+", on_delete=models.SET_NULL)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(character__isnull=True, player__isnull=False)
                | Q(character__isnull=False, player__isnull=True),
                name="scope_grant_names_exactly_one_subject",
            ),
        ]

    def __str__(self) -> str:
        subject = self.character or self.player
        return f"{subject} knows t={self.beat.t} since t={self.t}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding:
            raise ImmutableGrant("scope grants cannot change once stored")
        super().save(*args, **kwargs)


class Verdict(models.TextChoices):
    VERIFIED = "verified"
    FALSE = "false"
    UNVERIFIED = "unverified"
    MISLEADING = "misleading"


class FactLabel(models.Model):
    """An external factuality verdict on a beat, usually a claim (RQ4). Written by annotators and
    fact-check imports, never by the engine: the engine measures narratives, it does not judge truth."""

    beat = models.ForeignKey(Beat, related_name="fact_labels", on_delete=models.CASCADE)
    verdict = models.CharField(max_length=20, choices=Verdict)
    labeler = models.CharField(max_length=200)  # who judged: an annotator or a fact-checking source
    note = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["beat", "labeler"], name="one_fact_label_per_labeler_and_beat"),
        ]

    def __str__(self) -> str:
        return f"t={self.beat.t}: {self.verdict} ({self.labeler})"
