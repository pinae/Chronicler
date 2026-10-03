import pytest

from matching.engine import Fill, HypothesisState, IncrementalMatcher, MatcherConfig, weight_of
from matching.models import Hypothesis
from matching.store import StoredMatcher
from matching.tests.betrayal_world import ALDRIC, KEY, MIRA, WORLD, beat, betrayal, entity, harms, trusts
from schemas.definitions import SchemaDefinition
from schemas.library import load_library

PRIOR = -2.0
TRUST, ACCESS, HARM, BENEFIT, REVEAL = 0.5, 1.0, 1.5, 0.5, 3.0


def aldric_betrays_mira(*fills):
    return HypothesisState(
        schema=betrayal(), binding={"T": ALDRIC, "V": MIRA, "S": KEY}, created_at_t=1, fills=list(fills)
    )


def test_weight_is_the_prior_plus_the_weights_of_filled_steps():
    fills = [Fill("trust", 1), Fill("access", 2), Fill("harm", 3)]

    assert weight_of(betrayal(), fills, repeat_cap=3) == PRIOR + TRUST + ACCESS + HARM


def test_repeatable_step_counts_once_per_fill_up_to_the_cap():
    four_trusts = [Fill("trust", t) for t in [1, 2, 3, 4]]

    assert weight_of(betrayal(), four_trusts, repeat_cap=3) == PRIOR + 3 * TRUST
    assert weight_of(betrayal(), four_trusts, repeat_cap=2) == PRIOR + 2 * TRUST


def test_optional_step_adds_its_weight():
    assert weight_of(betrayal(), [Fill("benefit", 5)], repeat_cap=3) == PRIOR + BENEFIT


def test_matcher_weighs_hypotheses_with_its_configured_cap():
    matcher = IncrementalMatcher([betrayal()], config=MatcherConfig(repeatable_fill_cap=1))
    for t in [1, 2, 3]:
        matcher.step(trusts(t, MIRA, ALDRIC), WORLD)

    [hypothesis] = matcher.live()

    assert matcher.weight(hypothesis) == PRIOR + TRUST


def test_hypothesis_completes_when_its_last_required_step_is_filled():
    hypothesis = aldric_betrays_mira(Fill("trust", 1), Fill("access", 2), Fill("harm", 3))
    matcher = IncrementalMatcher([betrayal()], [hypothesis])

    matcher.step(beat(9, "learns", who=entity(MIRA), what={"beat": 3}), WORLD)

    assert hypothesis.status == "complete"
    assert hypothesis.status_changed_at_t == 9


def test_optional_step_is_not_needed_for_completion():
    hypothesis = aldric_betrays_mira(Fill("trust", 1), Fill("access", 2))
    matcher = IncrementalMatcher([betrayal()], [hypothesis])

    matcher.step(harms(3, ALDRIC, MIRA), WORLD)

    assert hypothesis.status == "live"
    assert hypothesis.fill_ts("benefit") == []


def test_completed_hypothesis_takes_no_further_fills():
    hypothesis = aldric_betrays_mira(Fill("trust", 1), Fill("access", 2), Fill("harm", 3))
    hypothesis.status, hypothesis.status_changed_at_t = "complete", 9
    matcher = IncrementalMatcher([betrayal()], [hypothesis])

    matcher.step(trusts(10, MIRA, ALDRIC), WORLD)

    assert hypothesis.fill_ts("trust") == [1]
    assert hypothesis not in matcher.live()


def test_seeded_hypothesis_of_a_one_step_schema_is_complete_at_once():
    one_step = SchemaDefinition(
        slug="trust_only",
        name="Trust only",
        roles={"T": "character", "V": "character"},
        steps=(betrayal().step("trust"),),
    )
    matcher = IncrementalMatcher([one_step])

    [hypothesis] = matcher.step(trusts(4, MIRA, ALDRIC), WORLD).new

    assert (hypothesis.status, hypothesis.status_changed_at_t) == ("complete", 4)


@pytest.mark.django_db
def test_stored_hypothesis_keeps_the_capped_weight(chronicle, entity_factory, beat_factory, settings):
    settings.MATCHER_REPEATABLE_FILL_CAP = 2
    load_library()
    mira, aldric = entity_factory(), entity_factory()
    for _ in range(3):
        StoredMatcher(chronicle).step(beat_factory("trusts", who=mira, whom=aldric))

    assert Hypothesis.objects.get().weight == PRIOR + 2 * TRUST
