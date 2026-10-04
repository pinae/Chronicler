import json
from io import StringIO

import pytest
from django.core.management import CommandError, call_command
from django.utils import timezone

from chronicle.models import Chronicle, Player, Utterance
from gm_ui.models import UsageEvent
from gm_ui.study import has_consent, pseudonymized_text

pytestmark = pytest.mark.django_db


def table(title, *players, consenting=()):
    chronicle = Chronicle.objects.create(kind="session", title=title)
    for name in players:
        Player.objects.create(
            chronicle=chronicle, name=name, consent_given_at=timezone.now() if name in consenting else None
        )
    return chronicle


def test_every_player_has_a_stable_pseudonym_of_their_own():
    wend = table("Wend", "Anna", "Ben")
    anna, ben = wend.players.get(name="Anna"), wend.players.get(name="Ben")

    assert anna.pseudonym.startswith("player-")
    assert anna.pseudonym != ben.pseudonym
    anna.refresh_from_db()
    assert Player.objects.get(pk=anna.pk).pseudonym == anna.pseudonym


def test_a_table_may_be_studied_only_when_every_player_consented():
    assert has_consent(table("Wend", "Anna", "Ben", consenting=["Anna", "Ben"]))
    assert not has_consent(table("Harbour", "Anna", "Ben", consenting=["Anna"]))


def test_literature_needs_no_consent_from_its_implicit_reader():
    novel = Chronicle.objects.create(kind="literature", title="A Novel")

    assert has_consent(novel)


def test_player_names_in_text_are_replaced_by_their_pseudonyms():
    wend = table("Wend", "Anna", "Ben")
    anna = wend.players.get(name="Anna")

    text = pseudonymized_text("Anna, roll for it. Annabelle waits.", wend)

    assert text == f"{anna.pseudonym}, roll for it. Annabelle waits."


def export_usage(*options):
    output, errors = StringIO(), StringIO()
    call_command("export_usage", *options, stdout=output, stderr=errors)
    return [json.loads(line) for line in output.getvalue().splitlines()], errors.getvalue()


def test_the_usage_export_leaves_out_tables_without_everyones_consent(client):
    agreed = table("Wend", "Anna", consenting=["Anna"])
    refused = table("Harbour", "Anna", "Ben", consenting=["Anna"])
    UsageEvent.objects.create(view="list_beats", chronicle=agreed)
    UsageEvent.objects.create(view="list_beats", chronicle=refused)

    events, errors = export_usage()

    assert [event["chronicle"] for event in events] == [agreed.pk]
    assert "Left out 1 chronicle without every player's consent." in errors


def test_the_usage_export_names_players_by_pseudonym():
    wend = table("Wend", "Anna", consenting=["Anna"])
    anna = wend.players.get()
    UsageEvent.objects.create(
        view="dry_run_beat",
        chronicle=wend,
        params={"audience": str(anna.pk), "body": {"pred": "is", "players_present": [anna.pk]}},
    )

    [event], _ = export_usage()

    assert event["params"]["audience"] == anna.pseudonym
    assert event["params"]["body"]["players_present"] == [anna.pseudonym]


def export_session(chronicle):
    output = StringIO()
    call_command("export_session", str(chronicle.pk), stdout=output)
    return json.loads(output.getvalue())


def test_a_session_export_speaks_with_pseudonyms_only():
    wend = table("Wend", "Anna", "Ben", consenting=["Anna", "Ben"])
    anna = wend.players.get(name="Anna")
    Utterance.objects.create(chronicle=wend, order=1, text="Ben, the door creaks.")
    Utterance.objects.create(chronicle=wend, order=2, speaker_player=anna, text="I open it.")

    session = export_session(wend)

    ben = wend.players.get(name="Ben")
    assert session["players"] == [anna.pseudonym, ben.pseudonym]
    assert session["utterances"] == [
        {"order": 1, "speaker": "gm", "text": f"{ben.pseudonym}, the door creaks."},
        {"order": 2, "speaker": anna.pseudonym, "text": "I open it."},
    ]
    assert "Anna" not in json.dumps(session)


def test_a_session_without_everyones_consent_is_not_exported():
    harbour = table("Harbour", "Anna", "Ben", consenting=["Anna"])

    with pytest.raises(CommandError, match="not every player of Harbour has consented"):
        export_session(harbour)
