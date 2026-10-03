import pytest
from django.core.management import CommandError, call_command
from django.urls import reverse

from chronicle.models import Chronicle


@pytest.fixture
def built_frontend(tmp_path, settings):
    (tmp_path / "index.html").write_text("<!doctype html><title>Chronicler</title><div id=root></div>")
    settings.FRONTEND_DIST_DIR = tmp_path
    return tmp_path


def test_root_serves_the_built_frontend(client, built_frontend):
    response = client.get("/")

    assert response.status_code == 200
    assert b"<title>Chronicler</title>" in response.content


def test_client_side_routes_serve_the_same_page(client, built_frontend):
    response = client.get("/chronicles/7/beats")

    assert response.status_code == 200
    assert b"<title>Chronicler</title>" in response.content


def test_missing_build_explains_how_to_build_it(client, tmp_path, settings):
    settings.FRONTEND_DIST_DIR = tmp_path / "missing"

    response = client.get("/")

    assert response.status_code == 503
    assert b"npm run build" in response.content


@pytest.mark.django_db
def test_api_paths_are_not_served_the_frontend(client, built_frontend):
    response = client.get("/api/no-such-endpoint")

    assert response.status_code == 404
    assert b"<title>Chronicler</title>" not in response.content


def test_healthz_still_answers(client, built_frontend):
    assert client.get(reverse("healthz")).json() == {"status": "ok"}


@pytest.mark.django_db
def test_seed_e2e_replaces_all_data_with_the_given_stories(settings):
    settings.E2E_SEEDING_ALLOWED = True
    Chronicle.objects.create(kind="session", title="Left over")

    call_command("seed_e2e", "minimal")

    assert list(Chronicle.objects.values_list("title", flat=True)) == ["The Minimal Hall"]


@pytest.mark.django_db
def test_seed_e2e_without_stories_leaves_an_empty_database(settings):
    settings.E2E_SEEDING_ALLOWED = True
    Chronicle.objects.create(kind="session", title="Left over")

    call_command("seed_e2e")

    assert Chronicle.objects.count() == 0


@pytest.mark.django_db
def test_seed_e2e_refuses_to_wipe_a_database_outside_e2e(settings):
    settings.E2E_SEEDING_ALLOWED = False

    with pytest.raises(CommandError, match="e2e"):
        call_command("seed_e2e", "minimal")
