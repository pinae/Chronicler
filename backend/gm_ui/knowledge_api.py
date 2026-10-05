"""Who knows what: the beats a character or player knew at t, and how they came to know them."""

from collections.abc import Iterable

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from ninja.errors import HttpError

from chronicle.models import Chronicle, Entity, Player, ScopeGrant

router = Router()


class KnownBeat(Schema):
    t: int
    pred: str
    text: str
    known_since_t: int
    learned_via_t: int | None  # the `learns` beat that conveyed it; None: witnessed or shown


class KnowledgeCell(Schema):
    t: int
    known_since_t: int
    learned_via_t: int | None


class KnowledgeColumn(Schema):
    player: int
    name: str
    known: list[KnowledgeCell]  # by t; the beats missing here the player never learned


class KnowledgeMapOut(Schema):
    last_t: int
    columns: list[KnowledgeColumn]


class EntityOut(Schema):
    id: int
    name: str
    kind: str
    introduced_at_t: int


@router.get("/chronicles/{chronicle_id}/knowledge", response=list[KnownBeat], url_name="get_knowledge")
def get_knowledge(
    request: HttpRequest,
    chronicle_id: int,
    character: int | None = None,
    player: int | None = None,
    t: int | None = None,
) -> list[KnownBeat]:
    """The beats one character (in the story) or one player (at the table) knew at t (default: latest)."""
    chronicle = get_object_or_404(Chronicle, pk=chronicle_id)
    if (character is None) == (player is None):
        raise HttpError(400, "name exactly one knower: a character or a player")
    at_t = t if t is not None else chronicle.beats.count()
    grants = ScopeGrant.objects.filter(beat__chronicle=chronicle, t__lte=at_t).select_related(
        "beat", "via_beat"
    )
    if character is not None:
        grants = grants.filter(character=get_object_or_404(Entity, pk=character, chronicle=chronicle))
    else:
        grants = grants.filter(player=get_object_or_404(Player, pk=player, chronicle=chronicle))
    return [
        KnownBeat(
            t=grant.beat.t,
            pred=grant.beat.pred,
            text=grant.beat.text,
            known_since_t=grant.t,
            learned_via_t=learned_via(grant),
        )
        for grant in earliest_by_beat(grants.order_by("beat__t", "t"))
    ]


@router.get(
    "/chronicles/{chronicle_id}/knowledge_map", response=KnowledgeMapOut, url_name="get_knowledge_map"
)
def get_knowledge_map(request: HttpRequest, chronicle_id: int) -> KnowledgeMapOut:
    """For each player at the table, every beat they came to know and since when."""
    chronicle = get_object_or_404(Chronicle, pk=chronicle_id)
    players = chronicle.players.filter(implicit=False).order_by("pk")
    grants = ScopeGrant.objects.filter(player__in=players).select_related("beat", "via_beat")
    return KnowledgeMapOut(
        last_t=chronicle.beats.count(),
        columns=[
            KnowledgeColumn(
                player=player.pk,
                name=player.name,
                known=[
                    KnowledgeCell(t=grant.beat.t, known_since_t=grant.t, learned_via_t=learned_via(grant))
                    for grant in earliest_by_beat(grants.filter(player=player).order_by("beat__t", "t"))
                ],
            )
            for player in players
        ],
    )


def earliest_by_beat(grants_by_beat_and_t: Iterable[ScopeGrant]) -> list[ScopeGrant]:
    """The first grant of every beat, from grants ordered by beat and then by t."""
    earliest: dict[int, ScopeGrant] = {}
    for grant in grants_by_beat_and_t:
        earliest.setdefault(grant.beat.t, grant)
    return list(earliest.values())


def learned_via(grant: ScopeGrant) -> int | None:
    """The t of the `learns` beat that conveyed it; None: witnessed or shown."""
    return grant.via_beat.t if grant.via_beat else None


@router.get("/chronicles/{chronicle_id}/entities", response=list[EntityOut], url_name="list_entities")
def list_entities(request: HttpRequest, chronicle_id: int, kind: str | None = None) -> list[EntityOut]:
    chronicle = get_object_or_404(Chronicle, pk=chronicle_id)
    entities = chronicle.entities.order_by("introduced_at_t", "pk")
    if kind is not None:
        entities = entities.filter(kind=kind)
    return [
        EntityOut(
            id=entity.pk, name=entity.canonical_name, kind=entity.kind, introduced_at_t=entity.introduced_at_t
        )
        for entity in entities
    ]
