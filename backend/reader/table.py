"""A reader model that answers from tables: deterministic, for tests and fixture runs."""

from collections.abc import Mapping

from reader.interfaces import ContextBeat, Question, ReaderContext, Readout


class UnanticipatedQuestion(LookupError):
    pass


class TableReader:
    def __init__(
        self,
        readouts: Mapping[tuple[int, str], Mapping[str, float]] | None = None,
        likelihoods: Mapping[tuple[int, str | None], float] | None = None,
    ) -> None:
        self.readouts = dict(readouts or {})  # (t, question text) -> label -> probability
        self.likelihoods = dict(likelihoods or {})  # (beat t, assumption) -> log-likelihood

    def readout(self, context: ReaderContext, question: Question) -> Readout:
        try:
            probabilities = self.readouts[(question.t, question.text)]
        except KeyError:
            raise UnanticipatedQuestion(f"no readout for t={question.t}: {question.text!r}") from None
        return Readout(probabilities=dict(probabilities))

    def beat_log_likelihood(self, context: ReaderContext, beat: ContextBeat) -> float:
        try:
            return self.likelihoods[(beat.t, context.assumption)]
        except KeyError:
            raise UnanticipatedQuestion(
                f"no log-likelihood for the beat at t={beat.t} assuming {context.assumption!r}"
            ) from None
