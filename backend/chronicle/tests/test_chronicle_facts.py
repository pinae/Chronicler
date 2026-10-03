import pytest

from chronicle.facts import StoredChronicleFacts

pytestmark = pytest.mark.django_db


def test_first_known_at_is_the_earliest_grant_of_the_beat_to_the_character(
    chronicle, entity_factory, beat_factory
):
    mira, aldric = entity_factory(), entity_factory()
    secret = beat_factory("hides", who=mira, what=aldric, characters=[mira])
    beat_factory("is", who=aldric, trait="curious")
    beat_factory("learns", who=aldric, what=secret)
    beat_factory("learns", who=aldric, what=secret)
    facts = StoredChronicleFacts(chronicle)

    assert facts.first_known_at(mira.id, secret.t) == 1
    assert facts.first_known_at(aldric.id, secret.t) == 3


def test_character_who_never_knew_a_beat_has_no_first_known_time(chronicle, entity_factory, beat_factory):
    mira, aldric = entity_factory(), entity_factory()
    secret = beat_factory("hides", who=mira, what=aldric, characters=[mira])

    assert StoredChronicleFacts(chronicle).first_known_at(aldric.id, secret.t) is None


def test_location_at_t_is_the_latest_is_at_up_to_t(chronicle, entity_factory, beat_factory):
    aldric = entity_factory()
    hall, cellar = entity_factory(kind="place"), entity_factory(kind="place")
    beat_factory("is_at", who=aldric, where=hall)
    beat_factory("is", who=aldric, trait="nervous")
    beat_factory("is_at", who=aldric, where=cellar)
    facts = StoredChronicleFacts(chronicle)

    assert facts.location_at(aldric.id, 0) is None
    assert facts.location_at(aldric.id, 2) == {"entity": hall.id}
    assert facts.location_at(aldric.id, 3) == {"entity": cellar.id}
