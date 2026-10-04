import json
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser

from evaluation.ground_truth import read_ground_truth
from evaluation.metrics import ALL
from evaluation.report import metric_rows, table


class Command(BaseCommand):
    help = "Compute the evaluation metrics (concept §9.2) of a story's run file and print them as a table."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("story", help="slug of a story under fixtures/stories/")
        parser.add_argument("--run", default=None, help="the run file to evaluate (default: the latest)")
        parser.add_argument("--runs-dir", default=str(settings.EVALUATION_RUNS_DIR))
        parser.add_argument("--audience", default=ALL, help="whose lattice: 'all' (default) or a player name")
        parser.add_argument("--top-k", type=int, default=5, help="k for voiced-hypothesis agreement")

    def handle(self, *args: Any, **options: Any) -> None:
        story = options["story"]
        path = Path(options["run"]) if options["run"] else latest_run_file(Path(options["runs_dir"]), story)
        run = json.loads(path.read_text())
        audience = options["audience"]
        check_audience(run, audience)
        truth = read_ground_truth(story)
        self.stdout.write(
            f"Evaluation of {story}: reader {run['reader'] or 'none'}, lattice {audience}, "
            f"run of {run['created_at']} ({path.name})\n"
        )
        self.stdout.write(table(metric_rows(run, truth, audience, options["top_k"])))


def latest_run_file(runs_dir: Path, story: str) -> Path:
    """Run files are named by their UTC timestamp, so the last name is the latest run."""
    run_files = sorted((runs_dir / story).glob("*.json"))
    if not run_files:
        raise CommandError(f"no run file for {story}; run `manage.py replay {story}` first")
    return run_files[-1]


def check_audience(run: dict[str, Any], audience: str) -> None:
    audiences = list(run["timeline"][0]["lattice"])
    if audience not in audiences:
        raise CommandError(f"the run has no lattice for '{audience}'; it has: {', '.join(audiences)}")
