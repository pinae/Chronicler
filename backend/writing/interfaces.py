"""Writing a story toward a target twist (concept §9.4, R2): the StoryWriter continues the prose one
step at a time, seeing the chronicle so far, the lattice, the target hypothesis and what the
audience expects."""

from dataclasses import dataclass
from typing import Protocol

from chronicle.ingest.interfaces import IngestedBeat
from evaluation.ground_truth import TrueHypothesis
from matching.lattice import Lattice
from matching.models import Expectation


@dataclass(frozen=True)
class WritingRequest:
    prefix: tuple[str, ...]  # the story so far, one text per utterance
    lattice: Lattice  # the unfiltered lattice at the last beat
    target: TrueHypothesis  # the twist to write toward (entities as slugs)
    expectations: tuple[Expectation, ...]  # the table's readouts at the last beat


@dataclass(frozen=True)
class Continuation:
    prose: str
    # The beat the writer meant the prose to convey, for comparison with what is ingested from it.
    # None for a writer that only writes prose.
    intended: IngestedBeat | None = None


class StoryWriter(Protocol):
    def continue_story(self, request: WritingRequest) -> Continuation: ...
