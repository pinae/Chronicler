"""The reader model (concept §2, §8.3): turns what an audience has seen plus a fixed question into a
probability distribution over a closed set of answers. Ollama-backed in production, table-backed in tests."""

from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Protocol, Self


@dataclass(frozen=True)
class ContextBeat:
    t: int
    text: str


@dataclass(frozen=True)
class ReaderContext:
    """The bounded, audience-visible chronicle prefix the reader sees, optionally under an assumption
    ("Suppose Aldric is betraying Mira.") for hypothesis-conditioned estimates."""

    t: int
    beats: tuple[ContextBeat, ...]
    assumption: str | None = None

    def assuming(self, assumption: str) -> Self:
        return replace(self, assumption=assumption)

    @property
    def included_beat_ts(self) -> list[int]:
        return [beat.t for beat in self.beats]


@dataclass(frozen=True)
class Candidate:
    label: str  # single-token answer label: "A", "B", ...
    text: str
    binding_delta: Mapping[str, int] | None  # None: "none of these / nothing yet"


@dataclass(frozen=True)
class Question:
    t: int
    text: str
    candidates: tuple[Candidate, ...]


@dataclass(frozen=True)
class Readout:
    probabilities: Mapping[str, float]  # label -> probability, renormalized over the candidates
    outside_mass: float = 0.0  # probability the model put on anything but the candidate labels
    llm_call_id: int | None = None


class BeatScorer(Protocol):
    def beat_log_likelihood(self, context: ReaderContext, beat: ContextBeat) -> float:
        """Log-probability of the beat's text as the continuation of the context."""
        ...


class ReaderModel(BeatScorer, Protocol):
    def readout(self, context: ReaderContext, question: Question) -> Readout: ...
