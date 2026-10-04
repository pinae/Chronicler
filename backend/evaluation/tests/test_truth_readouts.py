import pytest

from evaluation.ground_truth import GroundTruth, ReaderBelief, TrueHypothesis
from evaluation.replay import replay_story
from evaluation.truth_readouts import read_truth
from reader.context import RecentAndSupportingBeats
from reader.interfaces import Readout

pytestmark = pytest.mark.django_db

ALDRIC_BETRAYS_MIRA = GroundTruth(
    reveal_t=22,
    true_hypothesis=TrueHypothesis(schema="betrayal", binding={"T": "aldric", "V": "mira"}),
    dormant_window=(8, 11),
    reader_beliefs=(
        ReaderBelief(t=16, question="Who will harm Mira?", answer={"aldric": 0.4, "edda": 0.4, "none": 0.2}),
    ),
)
TRUTH_QUESTION = "Is the story a Betrayal with T = Aldric, V = Mira?"


class ScriptedReader:
    """Answers every question with fixed label probabilities and scores beats by their assumption."""

    def __init__(self, probabilities, log_likelihood_of):
        self.probabilities = probabilities
        self.log_likelihood_of = log_likelihood_of
        self.questions = []

    def readout(self, context, question):
        self.questions.append((context, question))
        return Readout(probabilities=self.probabilities(question), llm_call_id=None)

    def beat_log_likelihood(self, context, beat):
        return self.log_likelihood_of(context.assumption)


class ReaderWithoutBeatLikelihoods(ScriptedReader):
    def beat_log_likelihood(self, context, beat):
        raise NotImplementedError("no estimator yet")


def truth_favoured(assumption):
    if assumption is None:
        return -2.0
    return -1.0 if "T = Aldric" in assumption else -3.0


def yes_three_quarters(question):
    return {"A": 0.75, "B": 0.25} if question.text == TRUTH_QUESTION else {"A": 0.6, "B": 0.3, "C": 0.1}


@pytest.fixture
def steward():
    return replay_story("steward", reader=None)


def read(steward, reader, truth=ALDRIC_BETRAYS_MIRA):
    return read_truth(steward, truth, reader, RecentAndSupportingBeats())


def test_the_truth_is_recorded_with_entity_ids(steward):
    record = read(steward, ScriptedReader(yes_three_quarters, truth_favoured))

    aldric, mira = (steward.entities.get(slug=slug).pk for slug in ("aldric", "mira"))
    assert (record["reveal_t"], record["schema"], record["dormant_window"]) == (22, "betrayal", [8, 11])
    assert record["binding"] == {"T": aldric, "V": mira}


def test_the_belief_in_the_truth_is_asked_at_every_t_once_the_table_knows_its_entities(steward):
    reader = ScriptedReader(yes_three_quarters, truth_favoured)

    beliefs = read(steward, reader)["beliefs"]

    assert [belief["t"] for belief in beliefs] == list(range(2, 25))  # Aldric is first named at t=2
    assert {belief["p"] for belief in beliefs} == {0.75}
    context, question = next((c, q) for c, q in reader.questions if q.text == TRUTH_QUESTION)
    assert [(c.label, c.text) for c in question.candidates] == [("A", "yes"), ("B", "no")]
    assert context.t == 2


def test_bayes_factors_compare_the_truth_with_the_tables_strongest_other_reading(steward):
    bayes_factors = read(steward, ScriptedReader(yes_three_quarters, truth_favoured))["bayes_factors"]

    ronan_betrays_mira = steward.hypotheses.get(binding__T=steward.entities.get(slug="ronan").pk)
    # Beat 10 is the GM's secret: the table saw no evidence there.
    assert [record["t"] for record in bayes_factors] == [8, 9, 11]
    assert bayes_factors[0] == {"t": 8, "log_bayes_factor": 2.0, "dominant": ronan_betrays_mira.pk}


def test_without_another_reading_the_truth_is_compared_with_the_reader_assuming_nothing(steward):
    early = GroundTruth(
        reveal_t=22,
        true_hypothesis=ALDRIC_BETRAYS_MIRA.true_hypothesis,
        dormant_window=(2, 3),
    )

    bayes_factors = read(steward, ScriptedReader(yes_three_quarters, truth_favoured), early)["bayes_factors"]

    assert bayes_factors[0] == {"t": 2, "log_bayes_factor": 1.0, "dominant": None}


def test_a_reader_without_beat_likelihoods_records_no_bayes_factors(steward):
    record = read(steward, ReaderWithoutBeatLikelihoods(yes_three_quarters, truth_favoured))

    assert record["bayes_factors"] is None
    assert record["beliefs"]


def test_annotated_reader_beliefs_are_asked_and_answered_per_entity(steward):
    reader = ScriptedReader(yes_three_quarters, truth_favoured)

    [answered] = read(steward, reader)["reader_beliefs"]

    assert answered == {
        "t": 16,
        "question": "Who will harm Mira?",
        "annotated": {"aldric": 0.4, "edda": 0.4, "none": 0.2},
        "readout": {"aldric": 0.6, "edda": 0.3, "none": 0.1},
    }
    question = next(q for _, q in reader.questions if q.text == "Who will harm Mira?")
    assert [c.text for c in question.candidates] == ["Aldric", "Edda", "nothing like this"]
