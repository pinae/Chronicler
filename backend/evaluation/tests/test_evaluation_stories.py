"""The two evaluation stories (WP-043): the engine must see each twist coming."""

import json
from io import StringIO

import pytest
from django.core.management import call_command

from evaluation.ground_truth import TrueHypothesis, read_ground_truth
from evaluation.metrics import holds_truth, twist_recall

pytestmark = pytest.mark.django_db

EVALUATION_STORIES = ["steward", "ferryman"]


def replayed_run(story, runs_dir):
    call_command("replay", story, "--reader", "uniform", "--output-dir", str(runs_dir), stdout=StringIO())
    [run_file] = (runs_dir / story).glob("*.json")
    return json.loads(run_file.read_text())


@pytest.mark.parametrize("story", EVALUATION_STORIES)
def test_the_engine_holds_the_twist_five_beats_before_the_reveal(story, tmp_path):
    truth = read_ground_truth(story)
    assert truth is not None

    run = replayed_run(story, tmp_path)

    assert twist_recall(run, truth, k=5) is True
    assert run["truth"]["reveal_t"] == truth.reveal_t


def test_the_ferryman_lattice_holds_the_red_herring_next_to_the_truth(tmp_path):
    """Before the reveal the reader is led to suspect Bram; the lattice keeps both readings."""
    truth = read_ground_truth("ferryman")
    assert truth is not None
    run = replayed_run("ferryman", tmp_path)
    bram_betrays_oskar = TrueHypothesis(schema="betrayal", binding={"T": "bram", "V": "oskar"})

    assert holds_truth(run, bram_betrays_oskar, 13, "all")
    assert holds_truth(run, truth.true_hypothesis, 13, "all")
