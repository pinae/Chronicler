import re
import shutil

import pytest
import yaml
from django.conf import settings

from evaluation.ground_truth import (
    GroundTruth,
    GroundTruthError,
    ReaderBelief,
    TrueHypothesis,
    read_ground_truth,
)

STEWARD_TRUTH = {
    "reveal_t": 22,
    "true_hypothesis": {"schema": "betrayal", "binding": {"T": "aldric", "V": "mira"}},
    "dormant_window": [8, 21],
    "reader_beliefs": [
        {"t": 16, "question": "Who will harm Mira?", "answer": {"aldric": 0.4, "edda": 0.4, "none": 0.2}}
    ],
}


def steward_with(tmp_path, ground_truth):
    """A copy of the steward story with the given ground truth (None: no ground_truth.yaml)."""
    shutil.copytree(settings.FIXTURE_STORIES_DIR / "steward", tmp_path / "steward")
    path = tmp_path / "steward" / "ground_truth.yaml"
    path.unlink(missing_ok=True)
    if ground_truth is not None:
        path.write_text(yaml.safe_dump(ground_truth))
    return tmp_path


def changed(**changes):
    return {**STEWARD_TRUTH, **changes}


def test_a_ground_truth_is_read_with_entities_as_slugs(tmp_path):
    stories_dir = steward_with(tmp_path, STEWARD_TRUTH)

    ground_truth = read_ground_truth("steward", stories_dir)

    assert ground_truth == GroundTruth(
        reveal_t=22,
        true_hypothesis=TrueHypothesis(schema="betrayal", binding={"T": "aldric", "V": "mira"}),
        dormant_window=(8, 21),
        reader_beliefs=(
            ReaderBelief(
                t=16, question="Who will harm Mira?", answer={"aldric": 0.4, "edda": 0.4, "none": 0.2}
            ),
        ),
    )


def test_reader_beliefs_are_optional(tmp_path):
    without_beliefs = {key: value for key, value in STEWARD_TRUTH.items() if key != "reader_beliefs"}

    ground_truth = read_ground_truth("steward", steward_with(tmp_path, without_beliefs))

    assert ground_truth is not None
    assert ground_truth.reader_beliefs == ()


def test_a_story_without_ground_truth_has_none(tmp_path):
    assert read_ground_truth("steward", steward_with(tmp_path, None)) is None


@pytest.mark.parametrize(
    ("ground_truth", "message"),
    [
        ({"reveal_t": 22}, "missing 'true_hypothesis'"),
        (changed(true_hypothesis={"schema": "heist", "binding": {"T": "aldric"}}), "unknown schema 'heist'"),
        (
            changed(true_hypothesis={"schema": "betrayal", "binding": {"X": "aldric"}}),
            "betrayal has no role 'X'",
        ),
        (
            changed(true_hypothesis={"schema": "betrayal", "binding": {"T": "nobody"}}),
            "unknown entity 'nobody'",
        ),
        (
            changed(true_hypothesis={"schema": "betrayal", "binding": {"T": "seal"}}),
            "'seal' is a secret, but role T needs a character",
        ),
        (changed(reveal_t=0), "reveal_t must lie within the story (1 to 24)"),
        (changed(reveal_t=25), "reveal_t must lie within the story (1 to 24)"),
        (changed(dormant_window=[0, 21]), "dormant_window must lie within the story (1 to 24)"),
        (changed(dormant_window=[21, 8]), "dormant_window must be [start, end] with start <= end"),
        (changed(dormant_window=[8]), "dormant_window must be [start, end] with start <= end"),
        (changed(dormant_window=[8, 22]), "dormant_window must end before reveal_t"),
        (
            changed(reader_beliefs=[{"t": 16, "question": "Who?", "answer": {"aldric": 0.5, "none": 0.3}}]),
            "the probabilities of 'Who?' must add up to 1",
        ),
        (
            changed(reader_beliefs=[{"t": 16, "question": "Who?", "answer": {"nobody": 1.0}}]),
            "unknown entity 'nobody'",
        ),
        (
            changed(reader_beliefs=[{"t": 30, "question": "Who?", "answer": {"none": 1.0}}]),
            "reader belief 'Who?' must lie within the story (1 to 24)",
        ),
    ],
)
def test_an_inconsistent_ground_truth_is_rejected(tmp_path, ground_truth, message):
    stories_dir = steward_with(tmp_path, ground_truth)

    with pytest.raises(GroundTruthError, match="^" + re.escape(f"ground_truth.yaml: {message}")):
        read_ground_truth("steward", stories_dir)
