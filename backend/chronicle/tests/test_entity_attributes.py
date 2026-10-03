from dataclasses import dataclass, field

import pytest

from chronicle.beat_log import BeatDraft
from chronicle.entity_view import AttributeFact, attributes_at, project_attributes, rebuild_entity_attributes
from chronicle.models import Chronicle, Entity, EntityAttribute, Utterance


@dataclass
class PlainBeat:
    t: int
    pred: str
    args: dict
    tags: list = field(default_factory=list)

    @property
    def is_quarantined(self):
        return "quarantined" in self.tags


def entity(entity_id):
    return {"entity": entity_id}


def literal(value):
    return {"literal": value}


@pytest.fixture
def session(db):
    return Chronicle.objects.create(kind="session", title="The Steward")


@pytest.fixture
def utterance(session):
    return Utterance.objects.create(chronicle=session, order=1, text="…")


@pytest.fixture
def make_entity(session):
    def make(name, kind="character"):
        return Entity.objects.create(chronicle=session, kind=kind, canonical_name=name, introduced_at_t=1)

    return make


@pytest.fixture
def append(session, utterance):
    def append_beat(pred, **args):
        return session.append(BeatDraft(pred=pred, args=args, source_utterance=utterance))

    return append_beat


def stored_rows(chronicle):
    rows = EntityAttribute.objects.filter(entity__chronicle=chronicle)
    return sorted((row.entity_id, row.key, repr(row.value), row.source_beat_id) for row in rows)


def test_is_beat_creates_an_attribute_with_its_source_beat(session, append, make_entity):
    aldric = make_entity("Aldric")

    beat = append("is", who=entity(aldric.id), trait=literal("nervous"))

    [row] = EntityAttribute.objects.filter(entity=aldric)
    assert (row.key, row.value, row.source_beat) == ("is", literal("nervous"), beat)


def test_an_entity_can_have_several_traits(session, append, make_entity):
    aldric = make_entity("Aldric")

    append("is", who=entity(aldric.id), trait=literal("nervous"))
    append("is", who=entity(aldric.id), trait=literal("loyal"))

    values = [row.value for row in EntityAttribute.objects.filter(entity=aldric, key="is")]
    assert sorted(value["literal"] for value in values) == ["loyal", "nervous"]


def test_restating_a_fact_moves_its_source_to_the_latest_beat(session, append, make_entity):
    aldric = make_entity("Aldric")
    append("is", who=entity(aldric.id), trait=literal("nervous"))

    restated = append("is", who=entity(aldric.id), trait=literal("nervous"))

    [row] = EntityAttribute.objects.filter(entity=aldric)
    assert row.source_beat == restated


def test_location_is_replaced_by_the_latest_is_at_beat(session, append, make_entity):
    aldric = make_entity("Aldric")
    kitchen, cellar = make_entity("Kitchen", "place"), make_entity("Cellar", "place")
    append("is_at", who=entity(aldric.id), where=entity(kitchen.id))

    moved = append("is_at", who=entity(aldric.id), where=entity(cellar.id))

    [row] = EntityAttribute.objects.filter(entity=aldric, key="is_at")
    assert (row.value, row.source_beat) == (entity(cellar.id), moved)


def test_has_beats_accumulate_possessions(session, append, make_entity):
    aldric = make_entity("Aldric")
    key, letter = make_entity("Key", "object"), make_entity("Letter", "object")

    append("has", who=entity(aldric.id), what=entity(key.id))
    append("has", who=entity(aldric.id), what=entity(letter.id))

    assert EntityAttribute.objects.filter(entity=aldric, key="has").count() == 2


def test_beats_that_do_not_describe_state_leave_the_view_alone(session, append, make_entity):
    mira, aldric = make_entity("Mira"), make_entity("Aldric")

    append("trusts", who=entity(mira.id), whom=entity(aldric.id))

    assert stored_rows(session) == []


def test_quarantined_beat_never_changes_the_view(session, append, make_entity):
    aldric = make_entity("Aldric")

    append("becomes", who=entity(aldric.id), trait=literal("steward"))

    assert stored_rows(session) == []


def test_rebuilding_from_scratch_yields_the_incrementally_maintained_rows(session, append, make_entity):
    aldric, mira = make_entity("Aldric"), make_entity("Mira")
    kitchen, cellar = make_entity("Kitchen", "place"), make_entity("Cellar", "place")
    key = make_entity("Key", "object")
    append("is_at", who=entity(aldric.id), where=entity(kitchen.id))
    append("is", who=entity(aldric.id), trait=literal("nervous"))
    append("has", who=entity(mira.id), what=entity(key.id))
    append("is_at", who=entity(aldric.id), where=entity(cellar.id))
    append("is", who=entity(aldric.id), trait=literal("nervous"))
    incremental = stored_rows(session)

    rebuild_entity_attributes(session)

    assert stored_rows(session) == incremental
    assert len(incremental) == 3


def test_projection_is_a_pure_function_of_the_beats():
    beats = [
        PlainBeat(1, "is_at", {"who": entity(7), "where": entity(20)}),
        PlainBeat(2, "is", {"who": entity(7), "trait": literal("nervous")}),
        PlainBeat(3, "is_at", {"who": entity(7), "where": entity(21)}),
        PlainBeat(4, "is", {"who": entity(7), "trait": literal("calm")}, tags=["quarantined"]),
    ]

    facts = project_attributes(beats)

    assert sorted(facts, key=lambda fact: fact.key) == [
        AttributeFact(entity_id=7, key="is", value=literal("nervous"), source_t=2),
        AttributeFact(entity_id=7, key="is_at", value=entity(21), source_t=3),
    ]


def test_attributes_as_of_t_are_projected_from_the_beats_up_to_t(session, append, make_entity):
    aldric = make_entity("Aldric")
    kitchen, cellar = make_entity("Kitchen", "place"), make_entity("Cellar", "place")
    append("is_at", who=entity(aldric.id), where=entity(kitchen.id))
    append("is", who=entity(aldric.id), trait=literal("nervous"))
    append("is_at", who=entity(aldric.id), where=entity(cellar.id))

    assert attributes_at(session, 2) == [
        AttributeFact(entity_id=aldric.id, key="is_at", value=entity(kitchen.id), source_t=1),
        AttributeFact(entity_id=aldric.id, key="is", value=literal("nervous"), source_t=2),
    ]
    assert attributes_at(session, 0) == []
