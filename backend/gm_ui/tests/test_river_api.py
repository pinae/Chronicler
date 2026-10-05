import pytest
from django.urls import reverse

from evaluation.replay import replay_story

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def at_most_four_live_betrayals(settings):
    settings.MATCHER_MAX_LIVE_PER_SCHEMA = 4


@pytest.fixture
def steward():
    return replay_story("steward", reader=None, per_player=True)


def river(client, chronicle):
    response = client.get(reverse("api:get_river", args=[chronicle.pk]))
    assert response.status_code == 200, response.content
    return response.json()


def test_the_river_has_a_column_for_the_game_master_and_each_player(client, steward):
    result = river(client, steward)

    anna, ben = steward.players.order_by("pk")
    assert result["last_t"] == 24
    assert [(column["audience"], column["name"]) for column in result["columns"]] == [
        ("all", "All beats"),
        (str(anna.pk), "Anna"),
        (str(ben.pk), "Ben"),
    ]


def test_threads_are_named_by_schema_and_core_reading(client, steward):
    game_master = river(client, steward)["columns"][0]

    [seal_thread] = [
        thread
        for thread in game_master["threads"]
        if [entry["entity_name"] for entry in thread["binding"]] == ["Aldric", "Mira", None]
    ]
    assert (seal_thread["schema_slug"], seal_thread["schema_name"]) == ("betrayal", "Betrayal")
    assert (seal_thread["open_steps"], seal_thread["waiting_since"]) == ([], 2)
    assert seal_thread["binding"][0] == {
        "role": "T",
        "entity_id": steward.entities.get(slug="aldric").pk,
        "entity_name": "Aldric",
    }


def test_every_beat_has_a_moment_with_the_threads_shares(client, steward):
    game_master = river(client, steward)["columns"][0]

    assert [moment["t"] for moment in game_master["moments"]] == list(range(25))
    last = game_master["moments"][-1]
    assert sum(share["share"] for share in last["shares"]) + last["other"] == pytest.approx(1.0)
    assert set(last["shares"][0]) == {"thread", "share", "status", "secret"}


def test_events_name_their_thread_kind_and_step(client, steward):
    game_master = river(client, steward)["columns"][0]

    thread_ids = {thread["id"] for thread in game_master["threads"]}
    kinds = {event["kind"] for event in game_master["events"]}
    assert {event["thread"] for event in game_master["events"]} <= thread_ids
    assert {"filled", "completed", "refuted", "voiced"} <= kinds
    assert {"t": 22, "kind": "filled", "step": "reveal"} in [
        {key: event[key] for key in ("t", "kind", "step")} for event in game_master["events"]
    ]


def test_an_unknown_chronicle_is_not_found(client):
    response = client.get(reverse("api:get_river", args=[999]))

    assert response.status_code == 404
