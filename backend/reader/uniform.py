"""A reader that knows nothing: every candidate equally likely, every beat equally expected.
The baseline the reader model has to beat, and a reader for runs that need no language model."""

from reader.interfaces import ContextBeat, Question, ReaderContext, Readout


class UniformReader:
    def readout(self, context: ReaderContext, question: Question) -> Readout:
        share = 1.0 / len(question.candidates)
        return Readout(probabilities={candidate.label: share for candidate in question.candidates})

    def beat_log_likelihood(self, context: ReaderContext, beat: ContextBeat) -> float:
        return 0.0
