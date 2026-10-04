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


def lattice(client, chronicle, **params):
    response = client.get(reverse("api:get_lattice", args=[chronicle.pk]), params)
    assert response.status_code == 200, response.content
    return response.json()


def by_binding(hypotheses):
    return {
        tuple(entry["entity_name"] for entry in hypothesis["binding"]): hypothesis
        for hypothesis in hypotheses
    }


def test_lattice_at_the_end_shows_every_hypothesis_with_its_status(client, steward):
    result = lattice(client, steward)

    assert result["t"] == 24
    statuses = {names: h["status"] for names, h in by_binding(result["hypotheses"]).items()}
    assert statuses[("Aldric", "Mira", "The family seal")] == "complete"
    assert statuses[("Aldric", "Mira", None)] == "refuted"


def test_hypothesis_lists_schema_binding_weight_and_steps(client, steward):
    seal_betrayal = by_binding(lattice(client, steward, t=20)["hypotheses"])[
        ("Aldric", "Mira", "The family seal")
    ]

    assert (seal_betrayal["schema_slug"], seal_betrayal["schema_name"]) == ("betrayal", "Betrayal")
    assert seal_betrayal["binding"][0] == {
        "role": "T",
        "entity_id": steward.entities.get(slug="aldric").pk,
        "entity_name": "Aldric",
    }
    assert seal_betrayal["status"] == "live"
    assert seal_betrayal["weight"] == pytest.approx(-2.0 + 3 * 0.5 + 1.0 + 1.5 + 0.5)
    assert seal_betrayal["filled_steps"] == [
        {"step_id": "trust", "beat_ts": [2, 8, 17]},
        {"step_id": "access", "beat_ts": [7]},
        {"step_id": "harm", "beat_ts": [13]},
        {"step_id": "benefit", "beat_ts": [15]},
    ]
    assert seal_betrayal["open_steps"] == ["reveal"]
    assert seal_betrayal["created_at_t"] == 7
    assert seal_betrayal["refines"] is not None


def test_moving_t_back_shows_the_lattice_as_it_was(client, steward):
    before_reveal = by_binding(lattice(client, steward, t=21)["hypotheses"])

    assert before_reveal[("Aldric", "Mira", "The family seal")]["status"] == "live"
    assert len(lattice(client, steward, t=6)["hypotheses"]) == 4


def test_a_players_lattice_holds_only_what_they_saw(client, steward):
    anna = steward.players.get(name="Anna")

    before_reveal = by_binding(lattice(client, steward, audience=str(anna.pk), t=21)["hypotheses"])
    after_reveal = by_binding(lattice(client, steward, audience=str(anna.pk), t=22)["hypotheses"])

    assert ("Aldric", "Mira", "The family seal") not in before_reveal
    assert ("Aldric", "Mira", None) in before_reveal
    # At t=22 Anna hears of the theft (t=13): her lattice takes it up then.
    assert ("Aldric", "Mira", "The family seal") in after_reveal


def test_the_table_has_no_lattice_of_its_own(client, steward):
    response = client.get(reverse("api:get_lattice", args=[steward.pk]), {"audience": "table"})

    assert response.status_code == 400
    assert "lattice" in response.json()["detail"]
