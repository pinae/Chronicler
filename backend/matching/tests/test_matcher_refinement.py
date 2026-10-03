import pytest

from matching.engine import Fill, HypothesisState, IncrementalMatcher
from matching.models import Hypothesis
from matching.store import StoredMatcher
from matching.tests.betrayal_world import ALDRIC, KEY, MIRA, RONAN, WORLD, beat, betrayal, entity, trusts
from schemas.library import load_library


def helps(t, who, whom):
    return beat(t, "helps", who=entity(who), whom=entity(whom))


def steals(t, who, what, victim):
    return beat(t, "steals", who=entity(who), what=entity(what), **{"from": entity(victim)})


def hypothesis(t_entity, v_entity, s_entity=None, fills=(), created_at_t=1):
    return HypothesisState(
        schema=betrayal(),
        binding={"T": t_entity, "V": v_entity, "S": s_entity},
        created_at_t=created_at_t,
        fills=list(fills),
    )


def test_extending_the_binding_creates_a_child_that_refines_the_parent():
    someone_betrays_mira = hypothesis(None, MIRA)
    matcher = IncrementalMatcher([betrayal()], [someone_betrays_mira])

    result = matcher.step(helps(3, ALDRIC, MIRA), WORLD)

    [child] = result.new
    assert child.binding == {"T": ALDRIC, "V": MIRA, "S": None}
    assert child.refines is someone_betrays_mira
    assert child.fills == [Fill("trust", 3)]
    assert child.created_at_t == 3


def test_parent_stays_live_and_unchanged():
    someone_betrays_mira = hypothesis(None, MIRA)
    matcher = IncrementalMatcher([betrayal()], [someone_betrays_mira])

    result = matcher.step(helps(3, ALDRIC, MIRA), WORLD)

    assert someone_betrays_mira.is_live
    assert someone_betrays_mira.binding == {"T": None, "V": MIRA, "S": None}
    assert someone_betrays_mira.fills == []
    assert someone_betrays_mira not in result.changed


def test_child_carries_the_parents_fills_plus_the_new_one():
    aldric_betrays_mira = hypothesis(ALDRIC, MIRA, fills=[Fill("trust", 1)])
    matcher = IncrementalMatcher([betrayal()], [aldric_betrays_mira])

    [child] = matcher.step(steals(4, ALDRIC, KEY, MIRA), WORLD).new

    assert child.binding == {"T": ALDRIC, "V": MIRA, "S": KEY}
    assert child.fills == [Fill("trust", 1), Fill("harm", 4)]
    assert aldric_betrays_mira.fill_ts("harm") == []


def test_fill_that_does_not_extend_the_binding_fills_the_hypothesis_itself():
    aldric_betrays_mira = hypothesis(ALDRIC, MIRA)
    matcher = IncrementalMatcher([betrayal()], [aldric_betrays_mira])

    result = matcher.step(helps(3, ALDRIC, MIRA), WORLD)

    assert result.new == []
    assert aldric_betrays_mira.fill_ts("trust") == [3]


def test_a_beat_the_child_already_takes_creates_no_second_child():
    someone_betrays_mira = hypothesis(None, MIRA)
    matcher = IncrementalMatcher([betrayal()], [someone_betrays_mira])
    [child] = matcher.step(helps(3, ALDRIC, MIRA), WORLD).new

    result = matcher.step(helps(5, ALDRIC, MIRA), WORLD)

    assert result.new == []
    assert child.fill_ts("trust") == [3, 5]


def test_another_extension_creates_another_child():
    someone_betrays_mira = hypothesis(None, MIRA)
    matcher = IncrementalMatcher([betrayal()], [someone_betrays_mira])
    matcher.step(helps(3, ALDRIC, MIRA), WORLD)

    [second_child] = matcher.step(helps(4, RONAN, MIRA), WORLD).new

    assert second_child.binding["T"] == RONAN
    assert second_child.refines is someone_betrays_mira


def test_a_refinement_is_not_seeded_a_second_time():
    someone_betrays_mira = hypothesis(None, MIRA)
    matcher = IncrementalMatcher([betrayal()], [someone_betrays_mira])

    result = matcher.step(trusts(3, MIRA, ALDRIC), WORLD)

    [child] = result.new
    assert child.refines is someone_betrays_mira


@pytest.mark.django_db
def test_stored_child_refers_to_its_parent(chronicle, entity_factory, beat_factory):
    load_library()
    mira, aldric, key = entity_factory(), entity_factory(), entity_factory(kind="secret")
    StoredMatcher(chronicle).step(beat_factory("trusts", who=mira, whom=aldric))

    StoredMatcher(chronicle).step(beat_factory("steals", who=aldric, what=key, **{"from": mira}))

    parent = Hypothesis.objects.get(binding__S=None)
    child = Hypothesis.objects.get(refines=parent)
    assert child.binding == {"T": aldric.id, "V": mira.id, "S": key.id}
    assert child.created_at_t == 2
    assert sorted(fill.step.step_id for fill in child.fills.all()) == ["harm", "trust"]
