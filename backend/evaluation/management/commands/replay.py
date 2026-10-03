from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser

from evaluation.replay import build_run, replay_story, write_run
from narrative_engine import di
from reader.interfaces import ReaderModel
from reader.uniform import UniformReader


class Command(BaseCommand):
    help = "Run a fixture story through the whole pipeline and write a run file."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("story", help="slug of a story under fixtures/stories/")
        parser.add_argument(
            "--reader",
            choices=["configured", "uniform", "none"],
            default="configured",
            help="configured: settings.INJECTED['ReaderModel']; uniform: the know-nothing baseline; "
            "none: no readouts (lattice only)",
        )
        parser.add_argument("--until", type=int, default=None, help="stop after this t")
        parser.add_argument("--output-dir", default=str(settings.EVALUATION_RUNS_DIR))

    def handle(self, *args: Any, **options: Any) -> None:
        reader = choose_reader(options["reader"])
        chronicle = replay_story(options["story"], reader=reader, until_t=options["until"])
        reader_name = type(reader).__name__ if reader is not None else None
        run = build_run(chronicle, options["story"], reader=reader_name)
        path = write_run(run, Path(options["output_dir"]))
        self.stdout.write(f"Replayed {chronicle.beats.count()} beats of {options['story']}; run file: {path}")


def choose_reader(choice: str) -> ReaderModel | None:
    if choice == "none":
        return None
    if choice == "uniform":
        return UniformReader()
    reader: ReaderModel = di.make("ReaderModel")
    return reader
