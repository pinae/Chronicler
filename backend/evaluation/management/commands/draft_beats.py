from pathlib import Path
from typing import Any

import yaml
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser

from chronicle.ingest.interfaces import Ingester
from evaluation.drafting import draft_story
from narrative_engine import di

DRAFTED_FILES = ("beats.yaml", "entities.yaml")


class Command(BaseCommand):
    help = "Draft a story's beats.yaml and entities.yaml from its transcript with the configured ingester."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "story", help="slug of a story under fixtures/stories/ that has a transcript.yaml"
        )
        parser.add_argument("--stories-dir", default=str(settings.FIXTURE_STORIES_DIR))
        parser.add_argument(
            "--force", action="store_true", help="replace existing beats.yaml and entities.yaml"
        )

    def handle(self, *args: Any, **options: Any) -> None:
        story, stories_dir = options["story"], Path(options["stories_dir"])
        directory = stories_dir / story
        existing = [name for name in DRAFTED_FILES if (directory / name).exists()]
        if existing and not options["force"]:
            raise CommandError(f"{story} already has a {existing[0]}; pass --force to replace it")
        ingester: Ingester = di.make("Ingester")
        draft = draft_story(story, stories_dir, ingester)
        write_yaml(directory / "beats.yaml", draft.beats)
        write_yaml(directory / "entities.yaml", draft.entities)
        beats = plural(draft.beat_count, "beat")
        entities = plural(len(draft.entities), "entity", "entities")
        utterances = plural(draft.utterance_count, "utterance")
        self.stdout.write(
            f"Drafted {beats} and {entities} from {utterances}; {draft.review_count} marked for review"
        )


def write_yaml(path: Path, document: Any) -> None:
    path.write_text(yaml.safe_dump(document, sort_keys=False, allow_unicode=True, width=100))


def plural(count: int, singular: str, plural_form: str | None = None) -> str:
    return f"{count} {singular if count == 1 else plural_form or singular + 's'}"
