from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser

from chronicle.ingest.interfaces import Ingester
from chronicle.story_fixtures import read_story
from evaluation.ground_truth import GroundTruthError, TrueHypothesis, check_true_hypothesis
from evaluation.metrics import ALL
from evaluation.readers import READER_CHOICES, READER_HELP, choose_reader
from evaluation.replay import build_run, write_run
from evaluation.report import DEFAULT_TOP_K, metric_rows, table
from evaluation.truth_readouts import read_truth
from narrative_engine import di
from reader.context import RecentAndSupportingBeats
from schemas.library import read_library
from writing.generate import generate_story, generated_truth
from writing.interfaces import StoryWriter

TARGET_FORMAT = "a target is a schema and its binding, e.g. 'betrayal T=aldric V=mira'"


class Command(BaseCommand):
    help = (
        "Continue a seed story toward a target twist with the configured story writer, then evaluate "
        "the generated story."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("seed", help="slug of the story under fixtures/stories/ to continue")
        parser.add_argument(
            "--target", required=True, help="the twist to write toward: 'betrayal T=aldric V=mira'"
        )
        parser.add_argument("--beats", type=int, default=10, help="how many continuations the writer writes")
        parser.add_argument("--reader", choices=READER_CHOICES, default="configured", help=READER_HELP)
        parser.add_argument("--output-dir", default=str(settings.EVALUATION_RUNS_DIR))

    def handle(self, *args: Any, **options: Any) -> None:
        seed = options["seed"]
        story = read_story(seed)
        target = parse_target(options["target"])
        try:
            check_true_hypothesis(
                target, {entity.slug: entity.kind for entity in story.entities}, read_library()
            )
        except GroundTruthError as error:
            raise CommandError(f"--target: {error.reason}") from error
        writer: StoryWriter = di.make("StoryWriter")
        ingester: Ingester = di.make("Ingester")
        reader = choose_reader(options["reader"])
        chronicle = generate_story(
            seed, target, options["beats"], writer=writer, ingester=ingester, reader=reader
        )
        truth = generated_truth(target, len(story.beats), chronicle.beats.count())
        truth_record = (
            read_truth(chronicle, truth, reader, RecentAndSupportingBeats()) if truth and reader else None
        )
        reader_name = type(reader).__name__ if reader else None
        run = build_run(chronicle, f"{seed}-generated", reader=reader_name, truth=truth_record)
        path = write_run(run, Path(options["output_dir"]))
        generated = f"Generated {options['beats']} continuations of {seed} toward {describe(target)}"
        self.stdout.write(f"{generated}; run file: {path}\n")
        self.stdout.write(table(metric_rows(run, truth, ALL, DEFAULT_TOP_K)))


def parse_target(text: str) -> TrueHypothesis:
    schema, *assignments = text.split()
    if not assignments or not all(assignment.count("=") == 1 for assignment in assignments):
        raise CommandError(TARGET_FORMAT)
    return TrueHypothesis(schema=schema, binding=dict(assignment.split("=") for assignment in assignments))


def describe(target: TrueHypothesis) -> str:
    roles = ", ".join(f"{role} = {slug}" for role, slug in target.binding.items())
    return f"{target.schema} ({roles})"
