from matching.engine import HypothesisState, IncrementalMatcher
from matching.tests.betrayal_world import ALDRIC, MIRA, RONAN, WORLD, beat, betrayal, entity, harms, trusts


def matcher_with(*hypotheses):
    return IncrementalMatcher([betrayal()], hypotheses)


def bound(t_entity, v_entity, s_entity=None):
    return {"T": t_entity, "V": v_entity, "S": s_entity}


def test_trust_seeds_a_betrayal_with_trust_filled():
    matcher = IncrementalMatcher([betrayal()])

    result = matcher.step(trusts(4, MIRA, ALDRIC), WORLD)

    [seeded] = result.new
    assert seeded.schema.slug == "betrayal"
    assert seeded.binding == bound(ALDRIC, MIRA)
    assert seeded.fill_ts("trust") == [4]
    assert seeded.created_at_t == 4
    assert matcher.weight(seeded) == -2.0 + 0.5
    assert matcher.live() == [seeded]


def test_a_second_identical_trust_beat_fills_the_repeatable_step_instead_of_seeding_again():
    matcher = IncrementalMatcher([betrayal()])
    matcher.step(trusts(1, MIRA, ALDRIC), WORLD)

    result = matcher.step(trusts(2, MIRA, ALDRIC), WORLD)

    assert result.new == []
    [hypothesis] = matcher.live()
    assert hypothesis.fill_ts("trust") == [1, 2]
    assert result.changed == [hypothesis]


def test_trust_between_other_characters_seeds_a_separate_hypothesis():
    matcher = IncrementalMatcher([betrayal()])
    matcher.step(trusts(1, MIRA, ALDRIC), WORLD)

    result = matcher.step(trusts(2, MIRA, RONAN), WORLD)

    assert [hypothesis.binding for hypothesis in result.new] == [bound(RONAN, MIRA)]
    assert len(matcher.live()) == 2


def test_beats_matching_only_non_trigger_steps_never_seed():
    matcher = IncrementalMatcher([betrayal()])

    result = matcher.step(harms(1, ALDRIC, MIRA), WORLD)

    assert result.new == []
    assert matcher.live() == []


def test_beat_fills_the_step_of_the_hypothesis_bound_to_its_entities_only():
    aldric_betrays_mira = HypothesisState(schema=betrayal(), binding=bound(ALDRIC, MIRA), created_at_t=1)
    ronan_betrays_mira = HypothesisState(schema=betrayal(), binding=bound(RONAN, MIRA), created_at_t=2)
    matcher = matcher_with(aldric_betrays_mira, ronan_betrays_mira)

    result = matcher.step(harms(7, ALDRIC, MIRA), WORLD)

    assert aldric_betrays_mira.fill_ts("harm") == [7]
    assert ronan_betrays_mira.fill_ts("harm") == []
    assert result.changed == [aldric_betrays_mira]


def test_beat_fills_at_most_one_step_of_a_hypothesis():
    """`helps(T, V)` fits trust; it must not also count for any other step of the same hypothesis."""
    hypothesis = HypothesisState(schema=betrayal(), binding=bound(ALDRIC, MIRA), created_at_t=1)
    matcher = matcher_with(hypothesis)

    matcher.step(beat(3, "helps", who=entity(ALDRIC), whom=entity(MIRA)), WORLD)

    assert [(fill.step_id, fill.beat_t) for fill in hypothesis.fills] == [("trust", 3)]


def test_non_repeatable_step_is_filled_only_once():
    hypothesis = HypothesisState(schema=betrayal(), binding=bound(ALDRIC, MIRA), created_at_t=1)
    matcher = matcher_with(hypothesis)
    matcher.step(harms(5, ALDRIC, MIRA), WORLD)

    matcher.step(harms(6, ALDRIC, MIRA), WORLD)

    assert hypothesis.fill_ts("harm") == [5]


def test_quarantined_beat_neither_fills_nor_seeds():
    matcher = IncrementalMatcher([betrayal()])
    quarantined = beat(1, "trusts", who=entity(MIRA), whom=entity(ALDRIC))
    quarantined = type(quarantined)(t=1, pred="trusts", args=quarantined.args, tags=("quarantined",))

    assert matcher.step(quarantined, WORLD).new == []
