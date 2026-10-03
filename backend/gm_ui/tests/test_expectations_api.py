import pytest
from django.urls import reverse

from chronicle.models import Chronicle
from evaluation.replay import replay_story
from matching.models import Expectation, Hypothesis
from reader.uniform import UniformReader

pytestmark = pytest.mark.django_db


@pytest.fixture
def steward():
    return replay_story("steward", reader=UniformReader(), until_t=12)


def voiced_theory(chronicle):
    return Hypothesis.objects.get(chronicle=chronicle, voiced_by__isnull=False, for_player=None)


def expectations(client, chronicle, hypothesis, **params):
    url = reverse("api:list_expectations", args=[chronicle.pk, hypothesis.pk])
    response = client.get(url, params)
    assert response.status_code == 200, response.content
    return response.json()


def test_latest_expectation_per_open_step_up_to_t(client, steward):
    theory = voiced_theory(steward)

    [latest] = expectations(client, steward, theory, t=10)

    assert latest["step_id"] == "trust"
    assert latest["computed_at_t"] == 10
    assert latest["question"] == "Next: ___ trusts Aldric."
    assert [candidate["text"] for candidate in latest["candidates"]] == [
        "Mira",
        "Aldric",
        "Ronan",
        "Edda",
        "The raider",
        "nothing like this yet",
    ]
    assert latest["candidates"][0]["p"] == pytest.approx(1 / 6)
    assert latest["candidates"][-1]["null"] is True


def test_earlier_t_shows_the_expectation_held_then(client, steward):
    theory = voiced_theory(steward)

    [earlier] = expectations(client, steward, theory, t=5)

    assert earlier["computed_at_t"] == 5
    assert "The raider" not in [candidate["text"] for candidate in earlier["candidates"]]


def test_without_t_the_latest_expectation_is_shown(client, steward):
    theory = voiced_theory(steward)

    [latest] = expectations(client, steward, theory)

    assert (
        latest["computed_at_t"]
        == Expectation.objects.filter(hypothesis=theory).latest("computed_at_t").computed_at_t
    )


def test_hypothesis_without_expectations_has_none(client, steward):
    unasked = Hypothesis.objects.filter(chronicle=steward, expectations__isnull=True).first()

    assert expectations(client, steward, unasked) == []


def test_hypothesis_of_another_chronicle_is_not_found(client, steward):
    other = Chronicle.objects.create(kind="session", title="Other")
    theory = voiced_theory(steward)

    response = client.get(reverse("api:list_expectations", args=[other.pk, theory.pk]))

    assert response.status_code == 404
