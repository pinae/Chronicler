import pytest
from django.urls import reverse

from chronicle.models import Chronicle, Player
from gm_ui.models import UsageEvent

pytestmark = pytest.mark.django_db


@pytest.fixture
def steward(load_story):
    return load_story("steward")


def beats(client, chronicle, **params):
    response = client.get(reverse("api:list_beats", args=[chronicle.pk]), params)
    assert response.status_code == 200, response.content
    return response.json()


def test_chronicle_detail_names_title_kind_last_t_and_players(client, steward):
    response = client.get(reverse("api:get_chronicle", args=[steward.pk]))

    assert response.json() == {
        "id": steward.pk,
        "title": "The Steward of Wend",
        "kind": "session",
        "last_t": 24,
        "players": [
            {"id": steward.players.get(name="Anna").pk, "name": "Anna"},
            {"id": steward.players.get(name="Ben").pk, "name": "Ben"},
        ],
    }


def test_unknown_chronicle_is_not_found(client):
    assert client.get(reverse("api:get_chronicle", args=[999])).status_code == 404
    assert client.get(reverse("api:list_beats", args=[999])).status_code == 404


def test_all_beats_are_listed_in_t_order_by_default(client, steward):
    listed = beats(client, steward)

    assert [beat["t"] for beat in listed] == list(range(1, 25))
    assert listed[12] == {
        "t": 13,
        "pred": "steals",
        "text": "Aldric steals the seal from Mira.",
        "source_kind": "action",
        "quarantined": False,
    }


def test_beats_can_be_listed_up_to_t(client, steward):
    assert [beat["t"] for beat in beats(client, steward, t=10)] == list(range(1, 11))


def test_the_table_sees_only_what_every_player_saw(client, steward):
    table_ts = [beat["t"] for beat in beats(client, steward, audience="table")]

    assert table_ts == [t for t in range(1, 25) if t not in {5, 6, 7, 10, 12, 13, 16}]


def test_a_player_sees_their_private_beats_too(client, steward):
    ben = steward.players.get(name="Ben")

    ben_ts = [beat["t"] for beat in beats(client, steward, audience=str(ben.pk))]

    assert 7 in ben_ts
    assert 16 in ben_ts
    assert 5 not in ben_ts


def test_a_player_of_another_chronicle_is_not_found(client, steward):
    stranger = Player.objects.create(
        chronicle=Chronicle.objects.create(kind="session", title="Other"), name="Zoe"
    )

    response = client.get(reverse("api:list_beats", args=[steward.pk]), {"audience": str(stranger.pk)})

    assert response.status_code == 404


def test_an_audience_that_is_neither_all_table_nor_a_player_is_rejected(client, steward):
    response = client.get(reverse("api:list_beats", args=[steward.pk]), {"audience": "everyone"})

    assert response.status_code == 400


def test_listing_beats_is_recorded_with_chronicle_and_t(client, steward):
    beats(client, steward, audience="table", t=12)

    event = UsageEvent.objects.get(view="list_beats")
    assert (event.chronicle, event.t, event.params["audience"]) == (steward, 12, "table")
