from pathlib import Path
from typing import Any

import yaml
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser

from chronicle.importers.media import ArticleCollection, ArticleCollectionError, Outlet, parse_articles
from chronicle.importers.story_files import (
    StoryExists,
    story_directory,
    write_entities,
    write_readme_skeleton,
    write_transcript,
)
from chronicle.models import ChronicleKind, EntityKind


class Command(BaseCommand):
    help = "Turn a collection of news articles about one event into one media fixture story per outlet."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("collection_file", help="YAML with event, title and articles (see docs/usage)")
        parser.add_argument("--stories-dir", default=str(settings.FIXTURE_STORIES_DIR))
        parser.add_argument("--force", action="store_true", help="replace existing transcripts")

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            collection = parse_articles(yaml.safe_load(Path(options["collection_file"]).read_text()))
            directories = {
                outlet.slug: story_directory(
                    Path(options["stories_dir"]), story_slug(collection, outlet), options["force"]
                )
                for outlet in collection.outlets.values()
            }
        except (ArticleCollectionError, StoryExists) as error:
            raise CommandError(str(error)) from error
        for outlet in collection.outlets.values():
            write_outlet_story(directories[outlet.slug], collection, outlet)
        self.stdout.write(
            f"Wrote {len(collection.outlets)} outlets, {collection.passage_count} passages of "
            f"{collection.event}: {', '.join(story_slug(collection, o) for o in collection.outlets.values())}"
        )


def story_slug(collection: ArticleCollection, outlet: Outlet) -> str:
    return f"{collection.event}-{outlet.slug}"


def write_outlet_story(directory: Path, collection: ArticleCollection, outlet: Outlet) -> None:
    utterances = [
        {"order": order, "speaker": outlet.slug, "text": passage.text, "source": passage.source}
        for order, passage in enumerate(outlet.passages, start=1)
    ]
    write_transcript(directory, f"{collection.title} ({outlet.name})", ChronicleKind.MEDIA.value, utterances)
    write_entities(directory, {outlet.slug: {"kind": EntityKind.SOURCE.value, "name": outlet.name}})
    write_readme_skeleton(directory, directory.name, ChronicleKind.MEDIA.value)
