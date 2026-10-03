import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from chronicle.models import Chronicle

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("kind", ["session", "literature", "media"])
def test_chronicle_can_be_any_of_the_three_kinds(kind):
    chronicle = Chronicle.objects.create(kind=kind, title="The Steward")

    chronicle.full_clean()


def test_chronicle_of_unknown_kind_fails_validation():
    chronicle = Chronicle(kind="novel", title="The Steward")

    with pytest.raises(ValidationError):
        chronicle.full_clean()


def test_chronicle_of_unknown_kind_cannot_be_stored():
    with pytest.raises(IntegrityError):
        Chronicle.objects.create(kind="novel", title="The Steward")


def test_literature_chronicle_gets_one_implicit_reader():
    chronicle = Chronicle.objects.create(kind="literature", title="The Count of Monte Cristo")

    players = list(chronicle.players.all())

    assert [(player.name, player.implicit) for player in players] == [("reader", True)]


def test_media_chronicle_gets_one_implicit_public():
    chronicle = Chronicle.objects.create(kind="media", title="Minister resigns")

    players = list(chronicle.players.all())

    assert [(player.name, player.implicit) for player in players] == [("public", True)]


def test_session_chronicle_gets_no_implicit_player():
    chronicle = Chronicle.objects.create(kind="session", title="Session 1")

    assert chronicle.players.count() == 0


def test_saving_a_chronicle_again_creates_no_second_implicit_player():
    chronicle = Chronicle.objects.create(kind="literature", title="The Count of Monte Cristo")

    chronicle.title = "Le Comte de Monte-Cristo"
    chronicle.save()

    assert chronicle.players.count() == 1
