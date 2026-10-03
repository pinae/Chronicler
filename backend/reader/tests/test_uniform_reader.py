import pytest

from reader.interfaces import Candidate, ContextBeat, Question, ReaderContext
from reader.uniform import UniformReader


def test_uniform_reader_spreads_probability_evenly_over_the_candidates():
    question = Question(
        t=1,
        text="Next: ___ harms Mira.",
        candidates=tuple(Candidate(label=label, text=label, binding_delta=None) for label in "ABCD"),
    )

    readout = UniformReader().readout(ReaderContext(t=1, beats=()), question)

    assert readout.probabilities == {"A": 0.25, "B": 0.25, "C": 0.25, "D": 0.25}


def test_uniform_reader_finds_every_beat_equally_likely():
    reader = UniformReader()

    assert reader.beat_log_likelihood(
        ReaderContext(t=1, beats=()), ContextBeat(t=2, text="x")
    ) == pytest.approx(0.0)
