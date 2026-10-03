import pytest

pytestmark = pytest.mark.django_db


def test_chronicle_fixture_is_a_session(chronicle):
    assert chronicle.kind == "session"


def test_players_fixture_seats_two_players_at_the_chronicle(chronicle, players):
    assert [player.chronicle for player in players] == [chronicle, chronicle]
    assert len({player.name for player in players}) == 2


def test_entity_factory_creates_entities_in_the_chronicle(chronicle, entity_factory):
    aldric = entity_factory(canonical_name="Aldric")
    key = entity_factory(kind="object")

    assert (aldric.chronicle, aldric.kind, aldric.canonical_name) == (chronicle, "character", "Aldric")
    assert (key.chronicle, key.kind) == (chronicle, "object")


def test_beat_factory_appends_beats_with_consecutive_t(chronicle, entity_factory, beat_factory):
    aldric = entity_factory()

    first = beat_factory("is", who=aldric, trait="nervous")
    second = beat_factory("is", who=aldric, trait="tired")

    assert (first.t, second.t) == (1, 2)
    assert first.args == {"who": {"entity": aldric.id}, "trait": {"literal": "nervous"}}


def test_beat_factory_accepts_presence_and_beat_references(chronicle, players, entity_factory, beat_factory):
    mira, aldric = entity_factory(), entity_factory()
    secret = beat_factory("hides", who=mira, what=aldric, characters=[mira], players=[players[0]])

    learns = beat_factory("learns", who=aldric, what=secret)

    assert learns.args["what"] == {"beat": secret.t}
    assert set(secret.known_by_players_at(1)) == {players[0]}
