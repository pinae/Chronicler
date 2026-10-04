from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser

from evaluation.readers import READER_CHOICES, READER_HELP, choose_reader
from evaluation.replay import write_run
from evaluation.report import table
from narrative_engine import di
from writing.comparison import PROSE_ONLY, WITH_STRUCTURE, compare_writers, condition_label, export_for_raters
from writing.management.commands.generate import checked_target, describe


class Command(BaseCommand):
    help = (
        "Continue a seed story toward a target with and without the engine's structure, compare the "
        "metrics, and export both stories blind for human raters."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("seed", help="slug of the story under fixtures/stories/ to continue")
        parser.add_argument(
            "--target", required=True, help="the twist to write toward: 'betrayal T=aldric V=mira'"
        )
        parser.add_argument("--beats", type=int, default=10, help="how many continuations each writer writes")
        parser.add_argument("--reader", choices=READER_CHOICES, default="configured", help=READER_HELP)
        parser.add_argument("--output-dir", default=str(settings.EVALUATION_RUNS_DIR))
        parser.add_argument(
            "--export-dir", required=True, help="where to write the stories for raters and the key"
        )

    def handle(self, *args: Any, **options: Any) -> None:
        seed = options["seed"]
        target = checked_target(seed, options["target"])
        writers = {WITH_STRUCTURE: di.make("StoryWriter"), PROSE_ONLY: di.make("ProseOnlyStoryWriter")}
        variants = compare_writers(
            seed,
            target,
            options["beats"],
            writers=writers,
            ingester=di.make("Ingester"),
            reader=choose_reader(options["reader"]),
        )
        for variant in variants:
            write_run(variant.run, Path(options["output_dir"]))
        export_dir = Path(options["export_dir"])
        export_for_raters(variants, export_dir)
        self.stdout.write(f"Compared {len(variants)} writers continuing {seed} toward {describe(target)}\n")
        headers = ["Metric", *(condition_label(variant.condition) for variant in variants)]
        rows = [
            [metric, *(dict(variant.metrics)[metric] for variant in variants)]
            for metric, _ in variants[0].metrics
        ]
        self.stdout.write(table(rows, headers) + "\n")
        self.stdout.write(
            f"Stories for raters: {export_dir / 'for-raters'}; key: {export_dir / 'condition-key.json'}"
        )
