from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser

from chronicle.ingest.interfaces import Ingester
from chronicle.story_fixtures import read_story
from evaluation.ground_truth import GroundTruthError, TrueHypothesis, check_true_hypothesis
from evaluation.readers import READER_CHOICES, READER_HELP, choose_reader
from evaluation.replay import write_run
from evaluation.report import table
from narrative_engine import di
from schemas.library import read_library
from writing.comparison import generate_variant
from writing.interfaces import StoryWriter

GENERATED = "generated"
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
        target = checked_target(seed, options["target"])
        writer: StoryWriter = di.make("StoryWriter")
        ingester: Ingester = di.make("Ingester")
        reader = choose_reader(options["reader"])
        variant = generate_variant(seed, target, options["beats"], GENERATED, writer, ingester, reader)
        path = write_run(variant.run, Path(options["output_dir"]))
        generated = f"Generated {options['beats']} continuations of {seed} toward {describe(target)}"
        self.stdout.write(f"{generated}; run file: {path}\n")
        self.stdout.write(table(variant.metrics))


def checked_target(seed: str, text: str) -> TrueHypothesis:
    """The target, checked against the seed story's entities and the schema library."""
    target = parse_target(text)
    entity_kinds = {entity.slug: entity.kind for entity in read_story(seed).entities}
    try:
        check_true_hypothesis(target, entity_kinds, read_library())
    except GroundTruthError as error:
        raise CommandError(f"--target: {error.reason}") from error
    return target


def parse_target(text: str) -> TrueHypothesis:
    schema, *assignments = text.split()
    if not assignments or not all(assignment.count("=") == 1 for assignment in assignments):
        raise CommandError(TARGET_FORMAT)
    return TrueHypothesis(schema=schema, binding=dict(assignment.split("=") for assignment in assignments))


def describe(target: TrueHypothesis) -> str:
    roles = ", ".join(f"{role} = {slug}" for role, slug in target.binding.items())
    return f"{target.schema} ({roles})"
