"""Generating a story (concept §9.4, R2): the seed story is replayed as a literature chronicle, then
the writer continues it. Each continuation's prose is ingested like any other utterance, so the
lattice the writer sees next, and the evaluation, rest on what the prose conveys, not on what the
writer meant."""

from dataclasses import asdict
from typing import Any

from chronicle.ingest.interfaces import IngestedBeat, Ingester
from chronicle.models import Chronicle, ChronicleKind, Utterance
from evaluation.ground_truth import GroundTruth, TrueHypothesis
from evaluation.replay import replay_story
from matching.lattice import Lattice
from matching.models import Expectation
from narrative_engine.pipeline import Pipeline
from reader.context import ContextBuilder, RecentAndSupportingBeats
from reader.interfaces import ReaderModel
from writing.interfaces import Continuation, StoryWriter, WritingRequest


def generate_story(
    seed: str,
    target: TrueHypothesis,
    continuations: int,
    writer: StoryWriter,
    ingester: Ingester,
    reader: ReaderModel | None,
    context_builder: ContextBuilder | None = None,
) -> Chronicle:
    context_builder = context_builder or RecentAndSupportingBeats()
    chronicle = replay_story(
        seed, reader=reader, context_builder=context_builder, kind=ChronicleKind.LITERATURE
    )
    pipeline = Pipeline(chronicle, ingester, reader, context_builder)
    for _ in range(continuations):
        continuation = writer.continue_story(writing_request(chronicle, target))
        pipeline.process(generated_utterance(chronicle, continuation, writer))
    return chronicle


def writing_request(chronicle: Chronicle, target: TrueHypothesis) -> WritingRequest:
    t = chronicle.beats.count()
    expectations = Expectation.objects.filter(
        hypothesis__chronicle=chronicle, for_player=None, computed_at_t=t
    ).select_related("step")
    return WritingRequest(
        prefix=tuple(chronicle.utterances.order_by("order").values_list("text", flat=True)),
        lattice=Lattice.at(chronicle, t),
        target=target,
        expectations=tuple(expectations),
    )


def generated_utterance(chronicle: Chronicle, continuation: Continuation, writer: StoryWriter) -> Utterance:
    last = chronicle.utterances.order_by("order").last()
    source: dict[str, Any] = {"generated_by": type(writer).__name__}
    if continuation.intended is not None:
        source["intended"] = intended_entry(continuation.intended)
    return Utterance.objects.create(
        chronicle=chronicle, order=(last.order if last else 0) + 1, text=continuation.prose, source=source
    )


def intended_entry(beat: IngestedBeat) -> dict[str, Any]:
    """The intended beat in fixture notation, leaving out defaults."""
    defaults = asdict(IngestedBeat(pred="", args={}))
    return {
        key: value for key, value in asdict(beat).items() if key in ("pred", "args") or value != defaults[key]
    }


def generated_truth(target: TrueHypothesis, seed_last_t: int, last_t: int) -> GroundTruth | None:
    """The target as the generated story's ground truth: revealed at its last beat, dormant over the
    generated beats before. None if the continuation added fewer than two beats."""
    if last_t < seed_last_t + 2:
        return None
    return GroundTruth(reveal_t=last_t, true_hypothesis=target, dormant_window=(seed_last_t + 1, last_t - 1))
