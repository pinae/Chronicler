import pytest

from matching.engine import HypothesisState, IncrementalMatcher
from matching.models import Hypothesis
from matching.tests.betrayal_world import ALDRIC, MIRA, WORLD, betrayal, harms, trusts
from matching.tests.story_runs import matched_story

ANNA, UTTERANCE = 70, 30


def test_voiced_theory_becomes_a_hypothesis_bound_as_stated():
    matcher = IncrementalMatcher([betrayal()])

    voiced = matcher.voice("betrayal", {"T": ALDRIC}, voiced_by=ANNA, voiced_in=UTTERANCE, t=4)

    assert voiced.binding == {"T": ALDRIC, "V": None, "S": None}
    assert (voiced.voiced_by, voiced.voiced_in, voiced.created_at_t, voiced.fills) == (ANNA, UTTERANCE, 4, [])
    assert matcher.weight(voiced) == -2.0
    assert matcher.live() == [voiced]


def test_theory_matching_an_engine_hypothesis_marks_it_as_voiced_instead_of_duplicating_it():
    engine_hypothesis = HypothesisState(
        schema=betrayal(), binding={"T": ALDRIC, "V": MIRA, "S": None}, created_at_t=2
    )
    matcher = IncrementalMatcher([betrayal()], [engine_hypothesis])

    voiced = matcher.voice("betrayal", {"T": ALDRIC, "V": MIRA}, voiced_by=ANNA, voiced_in=UTTERANCE, t=4)

    assert voiced is engine_hypothesis
    assert (engine_hypothesis.voiced_by, engine_hypothesis.voiced_in) == (ANNA, UTTERANCE)
    assert len(matcher.hypotheses) == 1


def test_voicing_records_when_the_theory_was_voiced():
    engine_hypothesis = HypothesisState(
        schema=betrayal(), binding={"T": ALDRIC, "V": MIRA, "S": None}, created_at_t=2
    )
    matcher = IncrementalMatcher([betrayal()], [engine_hypothesis])

    matcher.voice("betrayal", {"T": ALDRIC, "V": MIRA}, voiced_by=ANNA, voiced_in=UTTERANCE, t=4)

    assert (engine_hypothesis.created_at_t, engine_hypothesis.voiced_at_t) == (2, 4)


def test_voiced_hypothesis_takes_part_in_fill():
    matcher = IncrementalMatcher([betrayal()])
    voiced = matcher.voice("betrayal", {"T": ALDRIC, "V": MIRA}, voiced_by=ANNA, voiced_in=UTTERANCE, t=1)

    matcher.step(harms(2, ALDRIC, MIRA), WORLD)

    assert voiced.fill_ts("harm") == [2]


def test_voiced_hypothesis_is_refined_like_any_other():
    matcher = IncrementalMatcher([betrayal()])
    voiced = matcher.voice("betrayal", {"T": ALDRIC}, voiced_by=ANNA, voiced_in=UTTERANCE, t=1)

    [child] = matcher.step(trusts(2, MIRA, ALDRIC), WORLD).new

    assert child.refines is voiced
    assert child.binding == {"T": ALDRIC, "V": MIRA, "S": None}


def test_theory_with_a_role_the_schema_does_not_have_is_rejected():
    matcher = IncrementalMatcher([betrayal()])

    with pytest.raises(ValueError, match="betrayal has no role 'X'"):
        matcher.voice("betrayal", {"X": ALDRIC}, voiced_by=ANNA, voiced_in=UTTERANCE, t=1)


def test_theory_about_an_unknown_schema_is_rejected():
    matcher = IncrementalMatcher([betrayal()])

    with pytest.raises(ValueError, match="unknown schema 'heist'"):
        matcher.voice("heist", {"T": ALDRIC}, voiced_by=ANNA, voiced_in=UTTERANCE, t=1)


@pytest.mark.django_db
def test_annas_theory_in_the_steward_story_is_stored_as_a_voiced_hypothesis():
    chronicle = matched_story("steward")
    anna = chronicle.players.get(name="Anna")
    aldric = chronicle.entities.get(slug="aldric")

    voiced = Hypothesis.objects.get(voiced_by=anna)

    assert voiced.binding == {"T": aldric.id, "V": None, "S": None}
    assert voiced.voiced_in == chronicle.utterances.get(order=3)
    assert voiced.created_at_t == 4
