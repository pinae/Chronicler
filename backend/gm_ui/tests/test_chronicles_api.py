import pytest
from django.urls import reverse

from chronicle.models import Chronicle
from gm_ui.models import UsageEvent

pytestmark = pytest.mark.django_db


def test_chronicle_list_is_empty_without_chronicles(client):
    response = client.get(reverse("api:list_chronicles"))

    assert response.status_code == 200
    assert response.json() == []


def test_chronicle_list_shows_title_kind_and_number_of_beats_newest_first(client, load_story):
    older = Chronicle.objects.create(kind="literature", title="The Count of Monte Cristo")
    newer = load_story("minimal")

    response = client.get(reverse("api:list_chronicles"))

    assert response.json() == [
        {"id": newer.pk, "title": "The Minimal Hall", "kind": "session", "beat_count": 5},
        {"id": older.pk, "title": "The Count of Monte Cristo", "kind": "literature", "beat_count": 0},
    ]


def test_every_api_request_is_recorded_as_a_usage_event(client):
    client.get(reverse("api:list_chronicles"), {"kind": "session"})

    [event] = UsageEvent.objects.all()
    assert (event.view, event.chronicle, event.t, event.params) == (
        "list_chronicles",
        None,
        None,
        {"kind": "session"},
    )
    assert event.created_at is not None


def test_requests_outside_the_api_are_not_recorded(client):
    client.get(reverse("healthz"))

    assert UsageEvent.objects.count() == 0


def test_the_api_publishes_an_openapi_schema_for_the_frontend(client):
    response = client.get("/api/openapi.json")

    assert response.status_code == 200
    assert "/api/chronicles/" in response.json()["paths"]


def test_a_request_for_a_missing_chronicle_is_recorded_without_a_link(client):
    client.get(reverse("api:get_chronicle", args=[999]))

    [event] = UsageEvent.objects.all()
    assert (event.chronicle, event.params) == (None, {"chronicle_id": "999"})
