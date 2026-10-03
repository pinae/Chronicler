"""The JSON API the GM/writer frontend talks to (ADR-006). OpenAPI schema: /api/openapi.json."""

from django.db.models import Count
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import NinjaAPI, Schema

from chronicle.models import Chronicle
from gm_ui.audiences import ALL, resolve_audience

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


class PlayerSummary(Schema):
    id: int
    name: str


class ChronicleDetail(Schema):
    id: int
    title: str
    kind: str
    last_t: int
    players: list[PlayerSummary]


class BeatSummary(Schema):
    t: int
    pred: str
    text: str
    source_kind: str
    quarantined: bool


@api.get("/chronicles/{chronicle_id}", response=ChronicleDetail, url_name="get_chronicle")
def get_chronicle(request: HttpRequest, chronicle_id: int) -> ChronicleDetail:
    chronicle = get_object_or_404(Chronicle, pk=chronicle_id)
    players = chronicle.players.filter(implicit=False).order_by("pk")
    return ChronicleDetail(
        id=chronicle.pk,
        title=chronicle.title,
        kind=chronicle.kind,
        last_t=chronicle.beats.count(),
        players=[PlayerSummary(id=player.pk, name=player.name) for player in players],
    )


@api.get("/chronicles/{chronicle_id}/beats", response=list[BeatSummary], url_name="list_beats")
def list_beats(
    request: HttpRequest, chronicle_id: int, audience: str = ALL, t: int | None = None
) -> list[BeatSummary]:
    """The beats `audience` ("all", "table" or a player id) had seen up to t (default: the latest)."""
    chronicle = get_object_or_404(Chronicle, pk=chronicle_id)
    up_to = t if t is not None else chronicle.beats.count()
    beats = resolve_audience(chronicle, audience).beats_up_to(chronicle, up_to)
    return [
        BeatSummary(
            t=beat.t,
            pred=beat.pred,
            text=beat.text,
            source_kind=beat.source_kind,
            quarantined=beat.is_quarantined,
        )
        for beat in beats.order_by("t")
    ]


# Registered last so its import of this module's api object is complete.
from gm_ui.knowledge_api import router as knowledge_router  # noqa: E402
from gm_ui.lattice_api import router as lattice_router  # noqa: E402

api.add_router("", lattice_router)
api.add_router("", knowledge_router)
