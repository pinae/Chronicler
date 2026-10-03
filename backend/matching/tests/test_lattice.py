import pytest

from matching.lattice import Lattice
from matching.tests.story_runs import matched_story

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def at_most_four_live_betrayals(settings):
    """With four live hypotheses per schema the steward story also exercises pruning (t=11)."""
    settings.MATCHER_MAX_LIVE_PER_SCHEMA = 4


def slugs(chronicle):
    return dict(chronicle.entities.values_list("pk", "slug"))


def describe(lattice, chronicle):
    """The lattice in terms that do not depend on database ids, so two chronicles can be compared."""
    slug_of = slugs(chronicle)
    by_id = {hypothesis.id: hypothesis for hypothesis in lattice.hypotheses}

    def name(hypothesis):
        binding = ",".join(
            f"{role}={slug_of.get(entity)}" for role, entity in sorted(hypothesis.binding.items())
        )
        fills = ",".join(f"{fill.step_id}@{fill.beat_t}" for fill in sorted(hypothesis.fills, key=repr))
        return f"{hypothesis.schema}({binding}) [{fills}] from t={hypothesis.created_at_t}"

    def parent(reference):
        return name(by_id[reference]) if reference else None

    return sorted(
        (
            name(hypothesis),
            hypothesis.status,
            round(hypothesis.weight, 6),
            hypothesis.status_changed_at_t,
            hypothesis.refuted_by_t,
            parent(hypothesis.refines_id),
            parent(hypothesis.merged_into_id),
        )
        for hypothesis in lattice.hypotheses
    )


def find(lattice, chronicle, **binding_slugs):
    ids = {slug: pk for pk, slug in slugs(chronicle).items()}
    wanted = {role: ids.get(slug) for role, slug in binding_slugs.items()}
    return next(hypothesis for hypothesis in lattice.hypotheses if hypothesis.binding == wanted)


def test_lattice_before_the_first_beat_is_empty():
    chronicle = matched_story("steward")

    assert Lattice.at(chronicle, 0).hypotheses == ()


def test_hypotheses_created_after_t_are_not_in_the_lattice_at_t():
    chronicle = matched_story("steward")

    lattice = Lattice.at(chronicle, 6)

    assert {hypothesis.created_at_t for hypothesis in lattice.hypotheses} == {2, 3, 4}


def test_fills_and_weight_are_those_up_to_t():
    chronicle = matched_story("steward")

    at_10 = find(Lattice.at(chronicle, 10), chronicle, T="aldric", V="mira", S="seal")
    at_20 = find(Lattice.at(chronicle, 20), chronicle, T="aldric", V="mira", S="seal")

    assert sorted((fill.step_id, fill.beat_t) for fill in at_10.fills) == [
        ("access", 7),
        ("trust", 2),
        ("trust", 8),
    ]
    assert at_10.weight == pytest.approx(-2.0 + 2 * 0.5 + 1.0)
    assert at_20.weight == pytest.approx(-2.0 + 3 * 0.5 + 1.0 + 1.5 + 0.5)


def test_status_is_the_one_held_at_t():
    chronicle = matched_story("steward")

    before_reveal = find(Lattice.at(chronicle, 21), chronicle, T="aldric", V="mira", S="seal")
    after_reveal = find(Lattice.at(chronicle, 22), chronicle, T="aldric", V="mira", S="seal")

    assert (before_reveal.status, before_reveal.status_changed_at_t) == ("live", None)
    assert (after_reveal.status, after_reveal.status_changed_at_t) == ("complete", 22)


def test_steward_exercises_every_kind_of_lattice_change():
    chronicle = matched_story("steward")

    lattice = Lattice.at(chronicle, 24)

    status_by_binding = {
        tuple(slugs(chronicle).get(entity) for entity in hypothesis.binding.values()): (
            hypothesis.status,
            hypothesis.status_changed_at_t,
        )
        for hypothesis in lattice.hypotheses
    }
    assert status_by_binding == {
        ("aldric", "mira", None): ("refuted", 24),
        ("ronan", "mira", None): ("refuted", 9),
        ("edda", "mira", None): ("refuted", 14),
        ("aldric", "mira", "seal"): ("complete", 22),
        ("edda", "mira", "ledger"): ("refuted", 14),
        ("mira", "aldric", None): ("pruned", 11),
    }
    refined = find(lattice, chronicle, T="aldric", V="mira", S="seal")
    assert refined.refines_id == find(lattice, chronicle, T="aldric", V="mira", S=None).id


def test_lattice_at_20_after_the_whole_story_equals_the_lattice_of_the_story_run_to_20():
    """The replay guarantee (concept §4): the lattice at any t is a filter, not a snapshot."""
    whole_story = matched_story("steward")
    first_twenty_beats = matched_story("steward", until_t=20)

    assert describe(Lattice.at(whole_story, 20), whole_story) == describe(
        Lattice.at(first_twenty_beats, 20), first_twenty_beats
    )


def test_live_hypotheses_are_those_live_at_t():
    chronicle = matched_story("steward")

    live = Lattice.at(chronicle, 20).live()

    assert sorted(hypothesis.created_at_t for hypothesis in live) == [2, 7]
