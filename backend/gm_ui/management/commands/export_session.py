import json
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from chronicle.models import Chronicle, Utterance
from gm_ui.study import has_consent, humans, pseudonymized_text

GM_SPEAKER = "gm"


class Command(BaseCommand):
    help = "Export a recorded session for the study: players by pseudonym, only if every player consented."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("chronicle_id", type=int)

    def handle(self, *args: Any, **options: Any) -> None:
        chronicle = Chronicle.objects.filter(pk=options["chronicle_id"]).first()
        if chronicle is None:
            raise CommandError(f"there is no chronicle {options['chronicle_id']}")
        if not has_consent(chronicle):
            raise CommandError(f"not every player of {chronicle.title} has consented; nothing was exported")
        session = {
            "title": chronicle.title,
            "kind": chronicle.kind,
            "players": [player.pseudonym for player in humans(chronicle)],
            "utterances": [
                {"order": u.order, "speaker": speaker(u), "text": pseudonymized_text(u.text, chronicle)}
                for u in chronicle.utterances.select_related("speaker_player", "speaker_entity").order_by(
                    "order"
                )
            ],
        }
        self.stdout.write(json.dumps(session, ensure_ascii=False, indent=1))


def speaker(utterance: Utterance) -> str:
    """Players by pseudonym; characters and outlets keep their names; the GM is "gm"."""
    if utterance.speaker_player is not None:
        return utterance.speaker_player.pseudonym
    if utterance.speaker_entity is not None:
        return utterance.speaker_entity.canonical_name
    return GM_SPEAKER
