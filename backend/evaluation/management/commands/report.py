import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser

from evaluation.ground_truth import read_ground_truth
from evaluation.report import markdown_report, story_section
from evaluation.run_files import NoRunFile, latest_run_file


class Command(BaseCommand):
    help = "Write the RQ1 report: the metrics of the latest run of each story, and what it could not express."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("stories", nargs="+", help="slugs of stories under fixtures/stories/")
        parser.add_argument("--runs-dir", default=str(settings.EVALUATION_RUNS_DIR))
        parser.add_argument(
            "--output", required=True, help="the Markdown file to write, e.g. docs/research/rq1.md"
        )

    def handle(self, *args: Any, **options: Any) -> None:
        runs_dir = Path(options["runs_dir"])
        try:
            run_paths = {story: latest_run_file(runs_dir, story) for story in options["stories"]}
        except NoRunFile as error:
            raise CommandError(str(error)) from error
        sections = [
            story_section(story, json.loads(path.read_text()), read_ground_truth(story), path.name)
            for story, path in run_paths.items()
        ]
        output = Path(options["output"])
        output.write_text(markdown_report(sections, datetime.now(UTC).date().isoformat()))
        self.stdout.write(f"Wrote the report on {len(sections)} stories to {output}")
