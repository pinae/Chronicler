from io import StringIO

import pytest
from django.core.management import CommandError, call_command

pytestmark = pytest.mark.django_db


def replay(story, runs_dir, *options):
    call_command("replay", story, *options, "--output-dir", str(runs_dir), stdout=StringIO())


def evaluate(story, *options):
    output = StringIO()
    call_command("evaluate", story, *options, stdout=output)
    return output.getvalue()


def value_of(report, metric):
    """The value column of the row for `metric`."""
    row = next(line for line in report.splitlines() if line.startswith(metric))
    return row.removeprefix(metric).strip()


def test_evaluate_prints_every_metric_of_the_latest_run(steward_with_ground_truth):
    runs_dir = steward_with_ground_truth
    replay("steward", runs_dir, "--reader", "none")
    replay("steward", runs_dir, "--reader", "uniform")

    report = evaluate("steward", "--runs-dir", str(runs_dir))

    assert report.splitlines()[0].startswith(
        "Evaluation of steward: reader UniformReader, lattice all, run of "
    )
    assert value_of(report, "twist recall at reveal - 1") == "yes"
    assert value_of(report, "twist recall at reveal - 5") == "yes"
    assert value_of(report, "twist recall at reveal - 20") == "yes"
    assert value_of(report, "lead time") == "20 beats (first held at t = 2)"
    assert value_of(report, "coverage: beats quarantined") == "0% (0 of 24)"
    assert value_of(report, "voiced agreement (top 5)") == "100% (1 of 1)"
    # The uniform reader favours nothing: no beat fits the truth better, no belief rises.
    assert value_of(report, "retrospective fit") == "0% (0 of 10)"
    assert value_of(report, "largest surprise") == "n/a"
    assert value_of(report, "calibration (Brier score)") == "n/a"


def test_coverage_counts_the_beats_that_fill_a_step(steward_with_ground_truth):
    replay("steward", steward_with_ground_truth, "--reader", "none")

    report = evaluate("steward", "--runs-dir", str(steward_with_ground_truth))

    assert value_of(report, "coverage: beats filling a step") == "50% (12 of 24)"


def test_metrics_without_inputs_are_shown_as_not_available(steward_with_ground_truth):
    replay("minimal", steward_with_ground_truth, "--reader", "none")

    report = evaluate("minimal", "--runs-dir", str(steward_with_ground_truth))

    for metric in [
        "twist recall at reveal - 5",
        "lead time",
        "voiced agreement (top 5)",
        "retrospective fit",
        "largest surprise",
        "calibration (Brier score)",
    ]:
        assert value_of(report, metric) == "n/a", metric


def test_evaluate_reads_a_given_run_file(steward_with_ground_truth):
    replay("steward", steward_with_ground_truth, "--reader", "none", "--until", "10")
    [run_file] = (steward_with_ground_truth / "steward").glob("*.json")

    report = evaluate("steward", "--run", str(run_file))

    assert value_of(report, "coverage: beats quarantined") == "0% (0 of 10)"
    assert value_of(report, "twist recall at reveal - 5") == "n/a"  # the run ends before the reveal


def test_evaluate_measures_a_players_lattice(steward_with_ground_truth):
    replay("steward", steward_with_ground_truth, "--reader", "none", "--per-player")

    report = evaluate("steward", "--runs-dir", str(steward_with_ground_truth), "--audience", "Anna")

    assert "lattice Anna" in report.splitlines()[0]
    assert value_of(report, "voiced agreement (top 5)") == "100% (1 of 1)"


def test_evaluate_rejects_an_audience_the_run_has_no_lattice_for(steward_with_ground_truth):
    replay("steward", steward_with_ground_truth, "--reader", "none")

    with pytest.raises(CommandError, match="the run has no lattice for 'Carl'; it has: all"):
        evaluate("steward", "--runs-dir", str(steward_with_ground_truth), "--audience", "Carl")


def test_evaluate_without_a_run_file_says_how_to_make_one(tmp_path):
    with pytest.raises(CommandError, match="no run file for steward; run `manage.py replay steward` first"):
        evaluate("steward", "--runs-dir", str(tmp_path))
