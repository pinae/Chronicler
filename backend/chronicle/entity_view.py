"""The entity attribute view: entity state projected from `is`, `has` and `is_at` beats.

`is_at` holds one value (a new location replaces the old one); `has` and `is` hold one row per value
(an entity can have several possessions and traits). The latest beat stating a fact is its source.
"""

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from django.db import transaction

from chronicle.models import Beat, Chronicle, EntityAttribute

STATE_ROLE_BY_PREDICATE = {"is": "trait", "has": "what", "is_at": "where"}
SINGLE_VALUED_KEYS = {"is_at"}


class BeatLike(Protocol):
    t: int
    pred: str
    args: Any

    @property
    def is_quarantined(self) -> bool: ...


@dataclass(frozen=True)
class AttributeFact:
    entity_id: int
    key: str
    value: Mapping[str, Any]
    source_t: int


def attribute_fact(beat: BeatLike) -> AttributeFact | None:
    if beat.is_quarantined or beat.pred not in STATE_ROLE_BY_PREDICATE:
        return None
    subject = beat.args["who"]["entity"]
    value = beat.args[STATE_ROLE_BY_PREDICATE[beat.pred]]
    return AttributeFact(entity_id=subject, key=beat.pred, value=value, source_t=beat.t)


def slot(entity_id: int, key: str, value: Mapping[str, Any]) -> tuple[Any, ...]:
    """Facts in the same slot replace each other."""
    if key in SINGLE_VALUED_KEYS:
        return (entity_id, key)
    return (entity_id, key, json.dumps(value, sort_keys=True))


def project_attributes(beats: Iterable[BeatLike]) -> list[AttributeFact]:
    facts: dict[tuple[Any, ...], AttributeFact] = {}
    for beat in sorted(beats, key=lambda beat: beat.t):
        fact = attribute_fact(beat)
        if fact is not None:
            facts[slot(fact.entity_id, fact.key, fact.value)] = fact
    return sorted(facts.values(), key=lambda fact: fact.source_t)


def attributes_at(chronicle: Chronicle, t: int) -> list[AttributeFact]:
    return project_attributes(chronicle.beats.filter(t__lte=t))


def update_entity_attributes(beat: Beat) -> None:
    """Apply one newly appended beat to the stored view."""
    fact = attribute_fact(beat)
    if fact is None:
        return
    fact_slot = slot(fact.entity_id, fact.key, fact.value)
    for row in EntityAttribute.objects.filter(entity_id=fact.entity_id, key=fact.key):
        if slot(row.entity_id, row.key, row.value) == fact_slot:
            row.value, row.source_beat = fact.value, beat
            row.save()
            return
    EntityAttribute.objects.create(entity_id=fact.entity_id, key=fact.key, value=fact.value, source_beat=beat)


def rebuild_entity_attributes(chronicle: Chronicle) -> None:
    with transaction.atomic():
        EntityAttribute.objects.filter(entity__chronicle=chronicle).delete()
        beats = list(chronicle.beats.all())
        beat_by_t = {beat.t: beat for beat in beats}
        EntityAttribute.objects.bulk_create(
            EntityAttribute(
                entity_id=fact.entity_id, key=fact.key, value=fact.value, source_beat=beat_by_t[fact.source_t]
            )
            for fact in project_attributes(beats)
        )
