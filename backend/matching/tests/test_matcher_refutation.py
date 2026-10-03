import pytest

from matching.engine import Fill, HypothesisState, IncrementalMatcher
from matching.models import Hypothesis
from matching.store import StoredMatcher
from matching.tests.betrayal_world import (
    ALDRIC,
    MIRA,
    RONAN,
    WORLD,
    beat,
    betrayal,
    entity,
    harms,
    trusts,
    world_with_facts,
)
from schemas.library import load_library


def kills(t, who, whom):
    return beat(t, "kills", who=entity(who), whom=entity(whom))


def aldric_betrays_mira(*fills, s_entity=None):
    return HypothesisState(
        schema=betrayal(), binding={"T": ALDRIC, "V": MIRA, "S": s_entity}, created_at_t=1, fills=list(fills)
    )


class TestContradictions:
    def test_beat_matching_a_contradiction_of_an_open_step_refutes(self):
        hypothesis = aldric_betrays_mira(Fill("trust", 1))
        matcher = IncrementalMatcher([betrayal()], [hypothesis])

        result = matcher.step(kills(5, RONAN, ALDRIC), WORLD)

        assert (hypothesis.status, hypothesis.refuted_by_t, hypothesis.status_changed_at_t) == (
            "refuted",
            5,
            5,
        )
        assert hypothesis in result.changed

    def test_contradiction_of_a_step_already_filled_does_not_refute(self):
        hypothesis = aldric_betrays_mira(Fill("trust", 1), Fill("harm", 3))
        matcher = IncrementalMatcher([betrayal()], [hypothesis])

        matcher.step(kills(5, RONAN, ALDRIC), WORLD)

        assert hypothesis.status == "live"

    def test_contradiction_about_an_unbound_role_does_not_refute(self):
        someone_betrays_mira = HypothesisState(
            schema=betrayal(), binding={"T": None, "V": MIRA, "S": None}, created_at_t=1
        )
        matcher = IncrementalMatcher([betrayal()], [someone_betrays_mira])

        matcher.step(kills(5, RONAN, ALDRIC), WORLD)

        assert someone_betrays_mira.status == "live"

    def test_refuted_hypothesis_takes_no_further_fills(self):
        hypothesis = aldric_betrays_mira(Fill("trust", 1))
        matcher = IncrementalMatcher([betrayal()], [hypothesis])
        matcher.step(kills(5, RONAN, ALDRIC), WORLD)

        matcher.step(trusts(6, MIRA, ALDRIC), WORLD)

        assert hypothesis.fill_ts("trust") == [1]


class TestConstraintViolations:
    def test_violating_distinct_refutes_the_hypothesis(self):
        matcher = IncrementalMatcher([betrayal()])

        [self_betrayal] = matcher.step(trusts(2, MIRA, MIRA), world_with_facts()).new

        assert (self_betrayal.status, self_betrayal.refuted_by_t, self_betrayal.status_changed_at_t) == (
            "refuted",
            2,
            2,
        )

    def test_harm_the_traitor_did_not_know_about_refutes(self):
        hypothesis = aldric_betrays_mira(Fill("trust", 1))
        matcher = IncrementalMatcher([betrayal()], [hypothesis])

        matcher.step(harms(4, ALDRIC, MIRA), world_with_facts(first_known={(ALDRIC, 4): 6}))

        assert hypothesis.status == "refuted"

    def test_victim_who_knew_of_the_harm_before_any_reveal_refutes(self):
        hypothesis = aldric_betrays_mira(Fill("trust", 1))
        matcher = IncrementalMatcher([betrayal()], [hypothesis])
        victim_present = {(ALDRIC, 4): 4, (MIRA, 4): 4}

        matcher.step(harms(4, ALDRIC, MIRA), world_with_facts(first_known=victim_present))

        assert hypothesis.status == "refuted"

    def test_secret_harm_keeps_the_hypothesis_live(self):
        hypothesis = aldric_betrays_mira(Fill("trust", 1))
        matcher = IncrementalMatcher([betrayal()], [hypothesis])

        matcher.step(harms(4, ALDRIC, MIRA), world_with_facts(first_known={(ALDRIC, 4): 4}))

        assert hypothesis.status == "live"

    def test_learning_of_the_harm_at_the_reveal_completes_instead_of_refuting(self):
        hypothesis = aldric_betrays_mira(Fill("trust", 1), Fill("access", 2), Fill("harm", 4))
        matcher = IncrementalMatcher([betrayal()], [hypothesis])
        knowledge = {(ALDRIC, 4): 4, (MIRA, 4): 9}

        matcher.step(
            beat(9, "learns", who=entity(MIRA), what={"beat": 4}), world_with_facts(first_known=knowledge)
        )

        assert (hypothesis.status, hypothesis.status_changed_at_t) == ("complete", 9)

    def test_without_chronicle_facts_constraints_are_not_checked(self):
        matcher = IncrementalMatcher([betrayal()])

        [self_betrayal] = matcher.step(trusts(2, MIRA, MIRA), WORLD).new

        assert self_betrayal.status == "live"


@pytest.mark.django_db
def test_stored_refutation_points_to_the_refuting_beat(chronicle, entity_factory, beat_factory):
    load_library()
    mira, aldric, ronan = entity_factory(), entity_factory(), entity_factory()
    StoredMatcher(chronicle).step(beat_factory("trusts", who=mira, whom=aldric))

    murder = beat_factory("kills", who=ronan, whom=aldric)
    StoredMatcher(chronicle).step(murder)

    hypothesis = Hypothesis.objects.get()
    assert (hypothesis.status, hypothesis.refuted_by, hypothesis.status_changed_at_t) == (
        "refuted",
        murder,
        2,
    )
