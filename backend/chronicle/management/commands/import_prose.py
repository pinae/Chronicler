from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser

from chronicle.importers.prose import ProseTranscript, parse_prose
from chronicle.importers.story_files import (
    TODO,
    StoryExists,
    story_directory,
    write_readme_skeleton,
    write_transcript,
)

KIND = "literature"


class Command(BaseCommand):
    help = "Turn a plain-text or Project Gutenberg book into a literature fixture story's transcript."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("text_file", help="the book as a plain-text file")
        parser.add_argument("slug", help="the new story's slug (its directory name)")
        parser.add_argument("--title", default=None, help="the title, if the text does not name one")
        parser.add_argument("--stories-dir", default=str(settings.FIXTURE_STORIES_DIR))
        parser.add_argument("--force", action="store_true", help="replace an existing transcript")

    def handle(self, *args: Any, **options: Any) -> None:
        transcript = parse_prose(Path(options["text_file"]).read_text(encoding="utf-8"))
        slug = options["slug"]
        try:
            directory = story_directory(Path(options["stories_dir"]), slug, options["force"])
        except StoryExists as error:
            raise CommandError(str(error)) from error
        write_transcript(
            directory, options["title"] or transcript.title or slug, KIND, utterances(transcript)
        )
        write_readme_skeleton(directory, slug, KIND, provenance=provenance(transcript))
        self.stdout.write(
            f"Wrote {len(transcript.paragraphs)} paragraphs in {transcript.chapter_count} chapters to "
            f"{directory / 'transcript.yaml'}"
        )


def utterances(transcript: ProseTranscript) -> list[dict[str, Any]]:
    return [
        {
            "order": order,
            "speaker": "narrator",
            "text": paragraph.text,
            "source": {"chapter": paragraph.chapter},
        }
        for order, paragraph in enumerate(transcript.paragraphs, start=1)
    ]


def provenance(transcript: ProseTranscript) -> str:
    if transcript.gutenberg_ebook is None:
        return TODO
    number = transcript.gutenberg_ebook
    return f"Project Gutenberg eBook #{number}, https://www.gutenberg.org/ebooks/{number}"
