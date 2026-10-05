import pytest
from django.urls import reverse

from gm_ui.models import UsageEvent

pytestmark = pytest.mark.django_db


@pytest.fixture
def steward(load_story):
    return load_story("steward")


def knowledge(client, chronicle, **params):
    response = client.get(reverse("api:get_knowledge", args=[chronicle.pk]), params)
    assert response.status_code == 200, response.content
    return {entry["t"]: entry for entry in response.json()}


def test_a_character_knows_the_beats_they_witnessed(client, steward):
    aldric = steward.entities.get(slug="aldric")

    known = knowledge(client, steward, character=aldric.pk)

    assert known[13] == {
        "t": 13,
        "pred": "steals",
        "text": "Aldric steals the seal from Mira.",
        "known_since_t": 13,
        "learned_via_t": None,
    }


def test_a_character_learns_of_a_beat_through_a_learns_beat(client, steward):
    mira = steward.entities.get(slug="mira")

    before_reveal = knowledge(client, steward, character=mira.pk, t=21)
    after_reveal = knowledge(client, steward, character=mira.pk, t=22)

    assert 13 not in before_reveal
    assert (after_reveal[13]["known_since_t"], after_reveal[13]["learned_via_t"]) == (22, 22)


def test_a_player_knows_what_was_shown_to_them(client, steward):
    ben = steward.players.get(name="Ben")

    known = knowledge(client, steward, player=ben.pk)

    assert {7, 16} <= set(known)
    assert 5 not in known
    assert known[7]["learned_via_t"] is None


def test_exactly_one_knower_must_be_named(client, steward):
    url = reverse("api:get_knowledge", args=[steward.pk])
    mira, ben = steward.entities.get(slug="mira"), steward.players.get(name="Ben")

    assert client.get(url).status_code == 400
    assert client.get(url, {"character": mira.pk, "player": ben.pk}).status_code == 400


def test_a_knower_of_another_chronicle_is_not_found(client, steward, load_story):
    other = load_story("minimal")

    response = client.get(
        reverse("api:get_knowledge", args=[steward.pk]), {"character": other.entities.get(slug="mira").pk}
    )

    assert response.status_code == 404


def test_characters_of_a_chronicle_are_listed_in_order_of_introduction(client, steward):
    response = client.get(reverse("api:list_entities", args=[steward.pk]), {"kind": "character"})

    assert [entity["name"] for entity in response.json()][:3] == ["Mira", "Aldric", "Ronan"]
    assert {entity["kind"] for entity in response.json()} == {"character"}


def test_asking_what_someone_knows_is_recorded_as_a_usage_event(client, steward):
    mira = steward.entities.get(slug="mira")

    knowledge(client, steward, character=mira.pk, t=21)

    event = UsageEvent.objects.get(view="get_knowledge")
    assert (event.chronicle, event.t) == (steward, 21)
    assert event.params["character"] == str(mira.pk)


@pytest.fixture
def broken_jug(load_story):
    return load_story("broken-jug")


def knowledge_map(client, chronicle):
    response = client.get(reverse("api:get_knowledge_map", args=[chronicle.pk]))
    assert response.status_code == 200, response.content
    return response.json()


def known_by(result, name):
    column = next(column for column in result["columns"] if column["name"] == name)
    return {cell["t"]: cell for cell in column["known"]}


def test_the_knowledge_map_has_a_column_per_player_at_the_table(client, broken_jug):
    result = knowledge_map(client, broken_jug)

    anna, ben, clara = broken_jug.players.filter(implicit=False).order_by("pk")
    assert result["last_t"] == 32
    assert [(column["player"], column["name"]) for column in result["columns"]] == [
        (anna.pk, "Anna"),
        (ben.pk, "Ben"),
        (clara.pk, "Clara"),
    ]


def test_the_game_masters_notes_reach_the_players_only_when_they_are_learned(client, broken_jug):
    result = knowledge_map(client, broken_jug)

    for name in ("Anna", "Ben", "Clara"):
        known = known_by(result, name)
        assert known[3] == {"t": 3, "known_since_t": 26, "learned_via_t": 26}  # the judge broke the jug
        assert known[2] == {"t": 2, "known_since_t": 30, "learned_via_t": 30}  # how he threatened Eve
        assert 1 not in known  # his visit to Eve's room stays the game master's


def test_a_beat_a_player_witnessed_is_known_from_its_own_row(client, broken_jug):
    known = known_by(knowledge_map(client, broken_jug), "Ben")

    assert known[19] == {"t": 19, "known_since_t": 19, "learned_via_t": None}  # Licht suspects the judge
    assert 20 not in known  # Adam hides that he broke the jug


def test_the_knowledge_map_of_an_unknown_chronicle_is_not_found(client):
    response = client.get(reverse("api:get_knowledge_map", args=[999]))

    assert response.status_code == 404
