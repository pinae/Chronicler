from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser

from chronicle.importers.session import SessionTranscript, TranscriptFormatError, parse_session
from chronicle.importers.story_files import (
    StoryExists,
    story_directory,
    write_readme_skeleton,
    write_transcript,
)

KIND = "session"
GM_SPEAKER = "gm"


class Command(BaseCommand):
    help = (
        "Turn a recorded play session ('Speaker: text' per turn) into a session fixture story's transcript."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("transcript_file", help="the session transcript as a text file")
        parser.add_argument("slug", help="the new story's slug (its directory name)")
        parser.add_argument("--title", required=True)
        parser.add_argument(
            "--gm", action="append", default=None, help="a name the GM speaks under (repeatable; default: GM)"
        )
        parser.add_argument("--stories-dir", default=str(settings.FIXTURE_STORIES_DIR))
        parser.add_argument("--force", action="store_true", help="replace an existing transcript")

    def handle(self, *args: Any, **options: Any) -> None:
        text = Path(options["transcript_file"]).read_text(encoding="utf-8")
        try:
            session = parse_session(text, gm_names=set(options["gm"] or ["GM"]))
            directory = story_directory(Path(options["stories_dir"]), options["slug"], options["force"])
        except (TranscriptFormatError, StoryExists) as error:
            raise CommandError(str(error)) from error
        write_transcript(directory, options["title"], KIND, utterances(session), players=session.players)
        write_readme_skeleton(directory, options["slug"], KIND)
        self.stdout.write(
            f"Wrote {len(session.turns)} turns by the GM and {len(session.players)} players "
            f"({', '.join(session.players)}) to {directory / 'transcript.yaml'}"
        )


def utterances(session: SessionTranscript) -> list[dict[str, Any]]:
    return [
        {
            "order": order,
            "speaker": turn.speaker or GM_SPEAKER,
            "text": turn.text,
            "source": {"line": turn.line},
        }
        for order, turn in enumerate(session.turns, start=1)
    ]
