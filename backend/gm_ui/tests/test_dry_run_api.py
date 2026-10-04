import pytest
from django.urls import reverse

from chronicle.models import Beat
from evaluation.replay import replay_story
from gm_ui.models import UsageEvent
from matching.models import Hypothesis

pytestmark = pytest.mark.django_db


@pytest.fixture
def steward():
    return replay_story("steward", reader=None, until_t=11, per_player=True)


def entity(chronicle, slug):
    return {"entity": chronicle.entities.get(slug=slug).pk}


def steal_the_seal(chronicle, **overrides):
    return {
        "pred": "steals",
        "args": {
            "who": entity(chronicle, "aldric"),
            "what": entity(chronicle, "seal"),
            "from": entity(chronicle, "mira"),
        },
        "text": "Aldric steals the seal from Mira.",
        "characters_present": [chronicle.entities.get(slug="aldric").pk],
        "players_present": [],
        **overrides,
    }


def post_dry_run(client, chronicle, body):
    return client.post(
        reverse("api:dry_run_beat", args=[chronicle.pk]), body, content_type="application/json"
    )


def test_a_dry_run_reports_the_effects_with_names_and_weights(client, steward):
    response = post_dry_run(client, steward, steal_the_seal(steward))

    assert response.status_code == 200, response.content
    result = response.json()
    assert result["t"] == 12
    [effect] = [
        effect
        for effect in result["effects"]
        if [entry["entity_name"] for entry in effect["binding"]] == ["Aldric", "Mira", "The family seal"]
    ]
    assert effect["schema_name"] == "Betrayal"
    assert effect["binding"][0] == {
        "role": "T",
        "entity_id": steward.entities.get(slug="aldric").pk,
        "entity_name": "Aldric",
    }
    assert (effect["changes"], effect["filled_step"]) == (["filled"], "harm")
    assert (effect["weight_before"], effect["weight_after"]) == (0.0, 1.5)


def test_a_dry_run_changes_nothing(client, steward):
    counts_before = (Beat.objects.count(), Hypothesis.objects.count())

    post_dry_run(client, steward, steal_the_seal(steward))

    assert (Beat.objects.count(), Hypothesis.objects.count()) == counts_before


def test_a_dry_run_on_a_players_lattice(client, steward):
    ben = steward.players.get(name="Ben")

    unseen = post_dry_run(client, steward, steal_the_seal(steward, audience=str(ben.pk)))
    seen = post_dry_run(
        client, steward, steal_the_seal(steward, audience=str(ben.pk), players_present=[ben.pk])
    )

    assert unseen.json()["effects"] == []
    assert [effect["changes"] for effect in seen.json()["effects"]] == [["filled"]]


def test_the_table_has_no_lattice_to_dry_run(client, steward):
    response = post_dry_run(client, steward, steal_the_seal(steward, audience="table"))

    assert response.status_code == 400


def test_an_invalid_candidate_beat_returns_the_validation_error(client, steward):
    missing_from = steal_the_seal(steward)
    del missing_from["args"]["from"]

    response = post_dry_run(client, steward, missing_from)

    assert response.status_code == 422
    assert response.json() == {"detail": "steals: missing role 'from'"}


def test_a_candidate_beat_naming_another_chronicles_entity_returns_the_validation_error(
    client, steward, load_story
):
    other = load_story("minimal")
    foreign = steal_the_seal(steward, characters_present=[other.entities.all()[0].pk])

    response = post_dry_run(client, steward, foreign)

    assert response.status_code == 422
    assert "is not part of this chronicle" in response.json()["detail"]


def test_a_dry_run_is_recorded_as_a_usage_event_with_the_candidate_and_its_t(client, steward):
    candidate = steal_the_seal(steward)

    post_dry_run(client, steward, candidate)

    event = UsageEvent.objects.get(view="dry_run_beat")
    assert (event.chronicle, event.t) == (steward, 12)
    assert event.params["body"] == candidate


def test_the_vocabulary_lists_each_predicate_with_its_roles(client):
    response = client.get(reverse("api:get_vocabulary"))

    assert response.status_code == 200
    predicates = {predicate["name"]: predicate["roles"] for predicate in response.json()}
    assert predicates["takes"] == [
        {"name": "who", "kinds": ["entity"], "optional": False},
        {"name": "what", "kinds": ["entity", "literal"], "optional": False},
        {"name": "from", "kinds": ["entity"], "optional": True},
    ]
