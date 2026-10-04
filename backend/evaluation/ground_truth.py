"""A story's ground truth (concept §9.1): the twist the engine should see coming, and when."""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from django.conf import settings

from chronicle.story_fixtures import StoryFixture, read_story
from schemas.definitions import SchemaDefinition
from schemas.library import read_library

GROUND_TRUTH_FILE = "ground_truth.yaml"
NO_ONE = "none"  # the answer "nothing like this" in reader beliefs
PROBABILITY_TOLERANCE = 0.01


class GroundTruthError(ValueError):
    def __init__(self, reason: str) -> None:
        super().__init__(f"{GROUND_TRUTH_FILE}: {reason}")
        self.reason = reason


@dataclass(frozen=True)
class TrueHypothesis:
    schema: str
    binding: Mapping[str, str]  # role -> entity slug; roles left out may be bound to anyone


@dataclass(frozen=True)
class ReaderBelief:
    t: int
    question: str
    answer: Mapping[str, float]  # entity slug, or "none" -> annotated probability


@dataclass(frozen=True)
class GroundTruth:
    reveal_t: int
    true_hypothesis: TrueHypothesis
    dormant_window: tuple[int, int]  # where the true hypothesis should be live but not dominant
    reader_beliefs: tuple[ReaderBelief, ...] = ()


def read_ground_truth(
    slug: str, stories_dir: Path | None = None, schemas: Sequence[SchemaDefinition] | None = None
) -> GroundTruth | None:
    """The story's ground truth, checked against the story and the schema library; None if the
    story has none."""
    directory = (stories_dir or settings.FIXTURE_STORIES_DIR) / slug
    path = directory / GROUND_TRUTH_FILE
    if not path.exists():
        return None
    ground_truth = parse_ground_truth(yaml.safe_load(path.read_text()))
    check_ground_truth(ground_truth, read_story(slug, directory.parent), schemas or read_library())
    return ground_truth


def parse_ground_truth(document: Mapping[str, Any]) -> GroundTruth:
    true_hypothesis = required(document, "true_hypothesis")
    window = required(document, "dormant_window")
    if not (isinstance(window, list) and len(window) == 2 and window[0] <= window[1]):
        raise GroundTruthError("dormant_window must be [start, end] with start <= end")
    return GroundTruth(
        reveal_t=required(document, "reveal_t"),
        true_hypothesis=TrueHypothesis(
            schema=required(true_hypothesis, "schema"), binding=dict(required(true_hypothesis, "binding"))
        ),
        dormant_window=(window[0], window[1]),
        reader_beliefs=tuple(
            ReaderBelief(
                t=required(belief, "t"),
                question=required(belief, "question"),
                answer=dict(required(belief, "answer")),
            )
            for belief in document.get("reader_beliefs") or []
        ),
    )


def required(document: Mapping[str, Any], key: str) -> Any:
    if key not in document:
        raise GroundTruthError(f"missing '{key}'")
    return document[key]


def check_ground_truth(
    ground_truth: GroundTruth, story: StoryFixture, schemas: Sequence[SchemaDefinition]
) -> None:
    last_t = len(story.beats)
    within_story = f"must lie within the story (1 to {last_t})"
    entity_kinds = {entity.slug: entity.kind for entity in story.entities}
    if not 1 <= ground_truth.reveal_t <= last_t:
        raise GroundTruthError(f"reveal_t {within_story}")
    check_true_hypothesis(ground_truth.true_hypothesis, entity_kinds, schemas)
    start, end = ground_truth.dormant_window
    if not (start >= 1 and end <= last_t):
        raise GroundTruthError(f"dormant_window {within_story}")
    if end >= ground_truth.reveal_t:
        raise GroundTruthError("dormant_window must end before reveal_t")
    for belief in ground_truth.reader_beliefs:
        if not 1 <= belief.t <= last_t:
            raise GroundTruthError(f"reader belief '{belief.question}' {within_story}")
        check_answer(belief, entity_kinds)


def check_true_hypothesis(
    true_hypothesis: TrueHypothesis, entity_kinds: Mapping[str, str], schemas: Sequence[SchemaDefinition]
) -> None:
    schema = next((schema for schema in schemas if schema.slug == true_hypothesis.schema), None)
    if schema is None:
        raise GroundTruthError(f"unknown schema '{true_hypothesis.schema}'")
    for role, slug in true_hypothesis.binding.items():
        if role not in schema.roles:
            raise GroundTruthError(f"{schema.slug} has no role '{role}'")
        if slug not in entity_kinds:
            raise GroundTruthError(f"unknown entity '{slug}'")
        if entity_kinds[slug] != schema.roles[role]:
            raise GroundTruthError(
                f"'{slug}' is a {entity_kinds[slug]}, but role {role} needs a {schema.roles[role]}"
            )


def check_answer(belief: ReaderBelief, entity_kinds: Mapping[str, str]) -> None:
    unknown = sorted(slug for slug in belief.answer if slug != NO_ONE and slug not in entity_kinds)
    if unknown:
        raise GroundTruthError(f"unknown entity '{unknown[0]}'")
    if not math.isclose(sum(belief.answer.values()), 1.0, abs_tol=PROBABILITY_TOLERANCE):
        raise GroundTruthError(f"the probabilities of '{belief.question}' must add up to 1")
