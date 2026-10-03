import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from chronicle.models import Chronicle, Entity

pytestmark = pytest.mark.django_db


@pytest.fixture
def session():
    return Chronicle.objects.create(kind="session", title="Session 1")


@pytest.mark.parametrize("kind", ["character", "object", "place", "faction", "secret", "source"])
def test_entity_can_be_any_of_the_six_kinds(session, kind):
    entity = Entity.objects.create(chronicle=session, kind=kind, canonical_name="Aldric", introduced_at_t=1)

    entity.full_clean()


def test_entity_of_unknown_kind_fails_validation(session):
    entity = Entity(chronicle=session, kind="weather", canonical_name="Storm", introduced_at_t=1)

    with pytest.raises(ValidationError):
        entity.full_clean()


def test_entity_of_unknown_kind_cannot_be_stored(session):
    with pytest.raises(IntegrityError):
        Entity.objects.create(chronicle=session, kind="weather", canonical_name="Storm", introduced_at_t=1)


def test_aliases_are_stored_as_a_list(session):
    aldric = Entity.objects.create(
        chronicle=session,
        kind="character",
        canonical_name="Aldric",
        aliases=["the steward", "Aldric of Wend"],
        introduced_at_t=1,
    )

    aldric.refresh_from_db()

    assert aldric.aliases == ["the steward", "Aldric of Wend"]


def test_entity_without_aliases_has_an_empty_list(session):
    aldric = Entity.objects.create(
        chronicle=session, kind="character", canonical_name="Aldric", introduced_at_t=1
    )

    assert aldric.aliases == []
