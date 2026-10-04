import json
from io import StringIO

import pytest
from django.core.management import CommandError, call_command

from evaluation.tests.synthetic_runs import ALDRIC, MIRA, beat, hypothesis, run_file


def write_run(runs_dir, story, run, name="20261004T000000000000Z.json"):
    (runs_dir / story).mkdir(parents=True, exist_ok=True)
    (runs_dir / story / name).write_text(json.dumps({**run, "story": story}))


def report(runs_dir, output, *stories):
    printed = StringIO()
    call_command("report", *stories, "--runs-dir", str(runs_dir), "--output", str(output), stdout=printed)
    return output.read_text(), printed.getvalue()


@pytest.fixture
def runs_dir(tmp_path):
    beats = [beat(1), beat(2, quarantined=True, original_pred="adores"), beat(3)]
    held = [(range(0, 4), hypothesis(1, ALDRIC, MIRA, fills=(("trust", 1),)))]
    write_run(tmp_path / "runs", "lantern", run_file(3, held, beats=beats))
    write_run(tmp_path / "runs", "harbour", run_file(2, held))
    return tmp_path / "runs"


def test_the_report_has_a_section_per_story_with_its_metrics(runs_dir, tmp_path):
    text, printed = report(runs_dir, tmp_path / "report.md", "lantern", "harbour")

    assert text.startswith("# RQ1 report\n")
    assert "## lantern\n" in text
    assert "## harbour\n" in text
    assert "| coverage: beats filling a step | 33% (1 of 3) |" in text
    assert "| twist recall at reveal - 5 | n/a |" in text  # no ground truth
    assert "Run `20261004T000000000000Z.json`, reader none, 3 beats." in text
    assert str(tmp_path / "report.md") in printed


def test_the_report_lists_the_beats_the_vocabulary_could_not_express(runs_dir, tmp_path):
    text, _ = report(runs_dir, tmp_path / "report.md", "lantern", "harbour")

    lantern = text.split("## lantern\n")[1].split("## harbour\n")[0]
    harbour = text.split("## harbour\n")[1]
    assert "| 2 | adores | beat 2 |" in lantern
    assert "Every beat could be expressed in the vocabulary." in harbour


def test_the_report_needs_a_run_of_every_story(runs_dir, tmp_path):
    with pytest.raises(CommandError, match="no run file for ferryman"):
        report(runs_dir, tmp_path / "report.md", "lantern", "ferryman")
