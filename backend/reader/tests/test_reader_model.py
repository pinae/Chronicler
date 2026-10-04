import pytest
from django.core.exceptions import ImproperlyConfigured

from narrative_engine import di
from reader.bayes import bayes_factor
from reader.interfaces import Candidate, ContextBeat, Question, ReaderContext
from reader.table import TableReader, UnanticipatedQuestion

CONTEXT = ReaderContext(t=12, beats=(ContextBeat(t=2, text="Mira trusts Aldric."),))
QUESTION = Question(
    t=12,
    text="Who will harm Mira?",
    candidates=(
        Candidate(label="A", text="Aldric", binding_delta={"T": 2}),
        Candidate(label="B", text="Ronan", binding_delta={"T": 3}),
        Candidate(label="C", text="nobody yet", binding_delta=None),
    ),
)
THEFT = ContextBeat(t=13, text="Aldric steals the seal.")


def test_table_reader_answers_anticipated_questions():
    reader = TableReader(readouts={(12, "Who will harm Mira?"): {"A": 0.6, "B": 0.3, "C": 0.1}})

    readout = reader.readout(CONTEXT, QUESTION)

    assert readout.probabilities == {"A": 0.6, "B": 0.3, "C": 0.1}
    assert readout.outside_mass == 0.0


def test_table_reader_raises_on_an_unanticipated_question():
    reader = TableReader(readouts={(11, "Who will harm Mira?"): {"A": 1.0}})

    with pytest.raises(UnanticipatedQuestion, match=r"t=12.*Who will harm Mira\?"):
        reader.readout(CONTEXT, QUESTION)


def test_table_reader_gives_log_likelihoods_of_beats_under_assumptions():
    reader = TableReader(likelihoods={(13, "Aldric betrays Mira."): -1.5})

    assert reader.beat_log_likelihood(CONTEXT.assuming("Aldric betrays Mira."), THEFT) == -1.5


def test_table_reader_raises_on_an_unanticipated_likelihood():
    with pytest.raises(UnanticipatedQuestion, match=r"t=13.*Ronan betrays Mira"):
        TableReader().beat_log_likelihood(CONTEXT.assuming("Ronan betrays Mira."), THEFT)


def test_assuming_a_hypothesis_keeps_the_beats():
    conditioned = CONTEXT.assuming("Aldric betrays Mira.")

    assert (conditioned.beats, conditioned.assumption) == (CONTEXT.beats, "Aldric betrays Mira.")


class RecordingReader:
    def __init__(self, log_likelihoods):
        self.log_likelihoods = log_likelihoods
        self.calls = []

    def beat_log_likelihood(self, context, beat):
        self.calls.append((context.assumption, beat))
        return self.log_likelihoods[context.assumption]


def test_bayes_factor_compares_the_same_beat_under_both_hypotheses():
    reader = RecordingReader({"Aldric betrays Mira.": -1.0, "Ronan betrays Mira.": -3.5})

    log_factor = bayes_factor(reader, THEFT, CONTEXT, "Aldric betrays Mira.", "Ronan betrays Mira.")

    assert log_factor == pytest.approx(2.5)
    [(first_assumption, first_beat), (second_assumption, second_beat)] = reader.calls
    assert (first_assumption, second_assumption) == ("Aldric betrays Mira.", "Ronan betrays Mira.")
    assert first_beat is second_beat is THEFT


def test_bayes_factor_against_no_assumption_compares_with_the_plain_reader():
    reader = RecordingReader({"Aldric betrays Mira.": -1.0, None: -2.0})

    log_factor = bayes_factor(reader, THEFT, CONTEXT, "Aldric betrays Mira.", None)

    assert log_factor == pytest.approx(1.0)


def test_test_settings_bind_the_reader_model_to_the_table_reader():
    assert isinstance(di.make("ReaderModel"), TableReader)


def test_registry_builds_what_the_settings_name(settings):
    settings.INJECTED = {**settings.INJECTED, "ReaderModel": "reader.tests.test_reader_model.RecordingReader"}

    with pytest.raises(TypeError):  # RecordingReader needs arguments: proves the class was built
        di.make("ReaderModel")


def test_registry_rejects_an_interface_without_a_binding():
    with pytest.raises(ImproperlyConfigured, match="StoryTeller"):
        di.make("StoryTeller")
