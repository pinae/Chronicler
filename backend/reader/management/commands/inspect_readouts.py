from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from chronicle.models import Chronicle, Player
from reader.inspection import describe_readouts


class Command(BaseCommand):
    help = "Show what the reader model answered at one beat: first token, raw alternatives, answers."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("chronicle", help="a chronicle id, or a story slug for its newest replay")
        parser.add_argument(
            "--t", type=int, required=True, help="the beat after which the readouts were asked"
        )
        parser.add_argument(
            "--audience", default=None, help="a player's name; without it, the readouts of the whole table"
        )

    def handle(self, *args: Any, **options: Any) -> None:
        chronicle = find_chronicle(options["chronicle"])
        audience = find_player(chronicle, options["audience"])
        for line in describe_readouts(chronicle, options["t"], audience):
            self.stdout.write(line)


def find_chronicle(reference: str) -> Chronicle:
    if reference.isdigit():
        chronicle = Chronicle.objects.filter(pk=int(reference)).first()
    else:
        chronicle = Chronicle.objects.filter(meta__fixture=reference).order_by("-pk").first()
    if chronicle is None:
        raise CommandError(f"no chronicle '{reference}'; replay the story first or give a chronicle id")
    return chronicle


def find_player(chronicle: Chronicle, name: str | None) -> Player | None:
    if name is None:
        return None
    player = chronicle.players.filter(name=name, implicit=False).first()
    if player is None:
        raise CommandError(f"{chronicle.title} has no player '{name}'")
    return player
