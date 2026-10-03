import pytest
from django.db import IntegrityError

from chronicle.models import Chronicle, Entity, Player, Utterance

pytestmark = pytest.mark.django_db


@pytest.fixture
def session():
    return Chronicle.objects.create(kind="session", title="Session 1")


def test_two_utterances_of_one_chronicle_cannot_share_an_order(session):
    Utterance.objects.create(chronicle=session, order=1, text="You enter the hall.")

    with pytest.raises(IntegrityError):
        Utterance.objects.create(chronicle=session, order=1, text="The steward bows.")


def test_utterances_of_different_chronicles_may_share_an_order(session):
    other = Chronicle.objects.create(kind="session", title="Session 2")
    Utterance.objects.create(chronicle=session, order=1, text="You enter the hall.")

    Utterance.objects.create(chronicle=other, order=1, text="You enter the crypt.")


def test_chapter_source_metadata_round_trips(session):
    utterance = Utterance.objects.create(chronicle=session, order=1, text="…", source={"chapter": 3})

    utterance.refresh_from_db()

    assert utterance.source == {"chapter": 3}


def test_article_source_metadata_round_trips(session):
    article = {
        "outlet": "The Herald",
        "author": "J. Doe",
        "published_at": "2026-05-01T08:30:00Z",
        "url": "https://herald.example/minister-resigns",
    }
    utterance = Utterance.objects.create(chronicle=session, order=1, text="…", source=article)

    utterance.refresh_from_db()

    assert utterance.source == article


def test_utterance_without_source_metadata_has_an_empty_source(session):
    utterance = Utterance.objects.create(chronicle=session, order=1, text="…")

    assert utterance.source == {}


def test_player_can_speak(session):
    mira_player = Player.objects.create(chronicle=session, name="Anna")

    utterance = Utterance.objects.create(
        chronicle=session, order=1, speaker_player=mira_player, text="I trust Aldric."
    )

    assert utterance.speaker_player == mira_player
    assert utterance.speaker_entity is None


def test_outlet_entity_can_speak():
    media = Chronicle.objects.create(kind="media", title="Minister resigns")
    herald = Entity.objects.create(
        chronicle=media, kind="source", canonical_name="The Herald", introduced_at_t=1
    )

    utterance = Utterance.objects.create(chronicle=media, order=1, speaker_entity=herald, text="…")

    assert utterance.speaker_entity == herald
    assert utterance.speaker_player is None


def test_game_master_or_narrator_speaks_without_a_speaker(session):
    utterance = Utterance.objects.create(chronicle=session, order=1, text="You enter the hall.")

    assert utterance.speaker_player is None
    assert utterance.speaker_entity is None


def test_utterance_cannot_have_a_player_and_an_entity_as_speaker():
    media = Chronicle.objects.create(kind="media", title="Minister resigns")
    herald = Entity.objects.create(
        chronicle=media, kind="source", canonical_name="The Herald", introduced_at_t=1
    )
    public = media.players.get()

    with pytest.raises(IntegrityError):
        Utterance.objects.create(
            chronicle=media, order=1, speaker_player=public, speaker_entity=herald, text="…"
        )
