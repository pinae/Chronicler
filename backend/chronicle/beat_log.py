"""Appending beats to a chronicle: the only way beats come into existence."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from django.db import transaction
from django.db.models import Max

from chronicle.beat_args import referenced_beat_ts, referenced_entity_ids
from chronicle.models import (
    QUARANTINE_TAG,
    UNKNOWN_PREDICATE,
    Beat,
    Chronicle,
    Entity,
    SourceKind,
    Utterance,
)
from schemas.vocabulary import UnknownPredicate, default_vocabulary


@dataclass(frozen=True)
class BeatDraft:
    """A beat as the ingester proposes it, before it has a `t`."""

    pred: str
    args: Mapping[str, Any]
    source_utterance: Utterance
    source_kind: str = SourceKind.NARRATION
    text: str = ""
    tags: Sequence[str] = ()
    confidence: float = 1.0


class AppendError(ValueError):
    pass


class NonConsecutiveTime(AppendError):
    pass


class InvalidReference(AppendError):
    pass


@dataclass(frozen=True)
class CanonicalPredicate:
    pred: str
    tags: list[str]
    original_pred: str = ""


def append_beat(chronicle: Chronicle, draft: BeatDraft, t: int | None = None) -> Beat:
    with transaction.atomic():
        # Lock the chronicle so concurrent appends cannot claim the same t.
        Chronicle.objects.select_for_update().get(pk=chronicle.pk)
        next_t = next_free_t(chronicle)
        if t is not None and t != next_t:
            raise NonConsecutiveTime(f"the next beat of this chronicle is t={next_t}, not t={t}")
        if draft.source_kind not in SourceKind.values:
            raise AppendError(f"unknown source kind '{draft.source_kind}'")
        canonical = canonical_predicate(draft)
        check_references(chronicle, draft, next_t)
        return Beat.objects.create(
            chronicle=chronicle,
            t=next_t,
            pred=canonical.pred,
            args=dict(draft.args),
            tags=canonical.tags,
            source_utterance=draft.source_utterance,
            source_kind=draft.source_kind,
            text=draft.text,
            confidence=draft.confidence,
            original_pred=canonical.original_pred,
        )


def next_free_t(chronicle: Chronicle) -> int:
    latest_t = chronicle.beats.aggregate(latest=Max("t"))["latest"]
    return (latest_t or 0) + 1


def canonical_predicate(draft: BeatDraft) -> CanonicalPredicate:
    """Validate against the vocabulary; an unknown predicate quarantines the beat instead of failing."""
    try:
        default_vocabulary().validate_args(draft.pred, draft.args)
    except UnknownPredicate:
        return CanonicalPredicate(UNKNOWN_PREDICATE, [*draft.tags, QUARANTINE_TAG], draft.pred)
    return CanonicalPredicate(draft.pred, list(draft.tags))


def check_references(chronicle: Chronicle, draft: BeatDraft, beat_t: int) -> None:
    if draft.source_utterance.chronicle_id != chronicle.pk:
        raise InvalidReference(
            f"source utterance #{draft.source_utterance.order} belongs to another chronicle"
        )
    entity_ids = referenced_entity_ids(draft.args)
    known_ids = set(
        Entity.objects.filter(chronicle=chronicle, pk__in=entity_ids).values_list("pk", flat=True)
    )
    foreign_ids = sorted(entity_ids - known_ids)
    if foreign_ids:
        raise InvalidReference(f"entity {foreign_ids[0]} is not part of this chronicle")
    later_ts = sorted(t for t in referenced_beat_ts(draft.args) if not 1 <= t < beat_t)
    if later_ts:
        raise InvalidReference(f"beat t={later_ts[0]} does not precede the new beat t={beat_t}")
