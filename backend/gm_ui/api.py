"""The JSON API the GM/writer frontend talks to (ADR-006). OpenAPI schema: /api/openapi.json."""

from django.db.models import Count
from django.http import HttpRequest
from ninja import NinjaAPI, Schema

from chronicle.models import Chronicle

api = NinjaAPI(title="Chronicler", urls_namespace="api")


class ChronicleSummary(Schema):
    id: int
    title: str
    kind: str
    beat_count: int


@api.get("/chronicles/", response=list[ChronicleSummary], url_name="list_chronicles")
def list_chronicles(request: HttpRequest) -> list[ChronicleSummary]:
    chronicles = Chronicle.objects.annotate(beat_count=Count("beats")).order_by("-created_at", "-pk")
    return [
        ChronicleSummary(
            id=chronicle.pk, title=chronicle.title, kind=chronicle.kind, beat_count=chronicle.beat_count
        )
        for chronicle in chronicles
    ]
