from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser

from chronicle.models import Chronicle
from evaluation.ground_truth import read_ground_truth
from evaluation.replay import build_run, replay_story, write_run
from evaluation.truth_readouts import read_truth
from narrative_engine import di
from reader.context import RecentAndSupportingBeats
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
        parser.add_argument(
            "--per-player", action="store_true", help="also build a lattice (and readouts) for every player"
        )
        parser.add_argument("--output-dir", default=str(settings.EVALUATION_RUNS_DIR))

    def handle(self, *args: Any, **options: Any) -> None:
        reader = choose_reader(options["reader"])
        chronicle = replay_story(
            options["story"], reader=reader, until_t=options["until"], per_player=options["per_player"]
        )
        reader_name = type(reader).__name__ if reader is not None else None
        audiences = [None, *chronicle.players.filter(implicit=False)] if options["per_player"] else [None]
        truth = None
        # The ground truth is about the whole story; a partial replay cannot be measured against it.
        if reader is not None and options["until"] is None:
            truth = truth_readouts(chronicle, options["story"], reader)
        run = build_run(chronicle, options["story"], audiences=audiences, reader=reader_name, truth=truth)
        path = write_run(run, Path(options["output_dir"]))
        self.stdout.write(f"Replayed {chronicle.beats.count()} beats of {options['story']}; run file: {path}")


def truth_readouts(chronicle: Chronicle, story: str, reader: ReaderModel) -> dict[str, Any] | None:
    """What the reader makes of the story's ground truth, if it has one."""
    ground_truth = read_ground_truth(story)
    if ground_truth is None:
        return None
    return read_truth(chronicle, ground_truth, reader, RecentAndSupportingBeats())


def choose_reader(choice: str) -> ReaderModel | None:
    if choice == "none":
        return None
    if choice == "uniform":
        return UniformReader()
    reader: ReaderModel = di.make("ReaderModel")
    return reader
