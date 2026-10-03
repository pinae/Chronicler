from django.urls import reverse


def test_healthz_reports_ok(client):
    response = client.get(reverse("healthz"))

    assert response.status_code == 200
