from typing import Any

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError, CommandParser

from evaluation.replay import replay_story
from reader.uniform import UniformReader


class Command(BaseCommand):
    help = "Replace all data with the given fixture stories, replayed with the uniform reader (e2e only)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("stories", nargs="*", help="fixture story slugs; none leaves the database empty")

    def handle(self, *args: Any, **options: Any) -> None:
        if not settings.E2E_SEEDING_ALLOWED:
            raise CommandError("seed_e2e wipes the database; it only runs with the e2e settings")
        call_command("flush", interactive=False, verbosity=0)
        for story in options["stories"]:
            replay_story(story, reader=UniformReader(), per_player=True)
        self.stdout.write(f"Seeded: {', '.join(options['stories']) or 'nothing'}")
