"""Comparing story writers (concept §9.4, RQ3): each writer continues the same seed toward the same
target with the same reader and ingester, and each result is measured against the target. Because
the same reader model guides and judges, human ratings carry the headline result; the rater export
hides which writer wrote which story."""

import json
import secrets
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from chronicle.ingest.interfaces import Ingester
from chronicle.models import Chronicle
from chronicle.story_fixtures import read_story
from evaluation.ground_truth import GroundTruth, TrueHypothesis
from evaluation.metrics import ALL
from evaluation.replay import build_run
from evaluation.report import DEFAULT_TOP_K, metric_rows
from evaluation.truth_readouts import read_truth
from reader.context import RecentAndSupportingBeats
from reader.interfaces import ReaderModel
from writing.generate import generate_story, generated_truth
from writing.interfaces import StoryWriter

WITH_STRUCTURE = "with-structure"
PROSE_ONLY = "prose-only"
RATER_DIRECTORY = "for-raters"
CONDITION_KEY = "condition-key.json"


@dataclass(frozen=True)
class Variant:
    """One writer's continuation of the seed: the chronicle, its run file and its ground truth."""

    condition: str
    chronicle: Chronicle
    run: dict[str, Any]
    truth: GroundTruth | None

    @property
    def texts(self) -> list[str]:
        return list(self.chronicle.utterances.order_by("order").values_list("text", flat=True))

    @property
    def metrics(self) -> list[tuple[str, str]]:
        return metric_rows(self.run, self.truth, ALL, DEFAULT_TOP_K)


def generate_variant(
    seed: str,
    target: TrueHypothesis,
    continuations: int,
    condition: str,
    writer: StoryWriter,
    ingester: Ingester,
    reader: ReaderModel | None,
) -> Variant:
    """The seed continued by the writer, with a run file (`<seed>-<condition>`) measured against
    the target."""
    seed_last_t = len(read_story(seed).beats)
    chronicle = generate_story(seed, target, continuations, writer=writer, ingester=ingester, reader=reader)
    truth = generated_truth(target, seed_last_t, chronicle.beats.count())
    record = read_truth(chronicle, truth, reader, RecentAndSupportingBeats()) if truth and reader else None
    reader_name = type(reader).__name__ if reader else None
    run = build_run(chronicle, f"{seed}-{condition}", reader=reader_name, truth=record)
    return Variant(condition=condition, chronicle=chronicle, run=run, truth=truth)


def compare_writers(
    seed: str,
    target: TrueHypothesis,
    continuations: int,
    writers: Mapping[str, StoryWriter],
    ingester: Ingester,
    reader: ReaderModel | None,
) -> list[Variant]:
    return [
        generate_variant(seed, target, continuations, condition, writer, ingester, reader)
        for condition, writer in writers.items()
    ]


def export_for_raters(variants: Sequence[Variant], directory: Path) -> dict[str, str]:
    """One Markdown file per story under a random id in `for-raters/`, and the id → condition key
    beside it in `condition-key.json`, which must not reach the raters."""
    rater_directory = directory / RATER_DIRECTORY
    rater_directory.mkdir(parents=True, exist_ok=True)
    key: dict[str, str] = {}
    for variant in variants:
        story_id = unused_id(key)
        (rater_directory / f"{story_id}.md").write_text(story_text(variant.chronicle.title, variant.texts))
        key[story_id] = variant.condition
    (directory / CONDITION_KEY).write_text(json.dumps(key, indent=1, sort_keys=True))
    return key


def unused_id(taken: Mapping[str, str]) -> str:
    while (story_id := secrets.token_hex(4)) in taken:
        pass
    return story_id


def story_text(title: str, paragraphs: Sequence[str]) -> str:
    return f"# {title}\n\n" + "\n\n".join(paragraphs) + "\n"


def condition_label(condition: str) -> str:
    return condition.replace("-", " ")
