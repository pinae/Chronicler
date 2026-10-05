"""The story map's river (WP-067): threads of readings per audience at every beat, names resolved."""

from collections.abc import Mapping

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router, Schema

from chronicle.models import Chronicle
from gm_ui.audiences import ALL
from gm_ui.lattice_api import BindingEntry
from gm_ui.river import AudienceRiver, Event, Moment, Thread, river_of
from schemas.models import Schema as SchemaRow

router = Router()


class ThreadOut(Schema):
    id: int
    schema_slug: str
    schema_name: str
    binding: list[BindingEntry]
    open_steps: list[str]  # required steps its strongest reading has not filled when last held
    waiting_since: int | None  # the t of that reading's first fill
    payoff_steps: list[str]  # the steps of its schema's payoff phase


class ShareOut(Schema):
    thread: int
    share: float
    status: str
    secret: bool


class MomentOut(Schema):
    t: int
    shares: list[ShareOut]
    other: float
    surprise: float  # how much the readings' shares moved since the beat before, 0..1
    tension: float  # the share of the readings with development but no payoff yet, 0..1


class EventOut(Schema):
    t: int
    thread: int
    kind: str
    step: str | None


class ColumnOut(Schema):
    audience: str  # "all" or a player id, as the other endpoints take it
    name: str
    threads: list[ThreadOut]
    moments: list[MomentOut]
    events: list[EventOut]


class RiverOut(Schema):
    last_t: int
    columns: list[ColumnOut]


@router.get("/chronicles/{chronicle_id}/river", response=RiverOut, url_name="get_river")
def get_river(request: HttpRequest, chronicle_id: int) -> RiverOut:
    """For the game master and each player, the threads they hold at every beat (story map)."""
    chronicle = get_object_or_404(Chronicle, pk=chronicle_id)
    names = dict(chronicle.entities.values_list("pk", "canonical_name"))
    schema_names = dict(SchemaRow.objects.values_list("slug", "name"))
    return RiverOut(
        last_t=chronicle.beats.count(),
        columns=[column_out(river, names, schema_names) for river in river_of(chronicle)],
    )


def column_out(river: AudienceRiver, names: Mapping[int, str], schema_names: Mapping[str, str]) -> ColumnOut:
    return ColumnOut(
        audience=ALL if river.player is None else str(river.player.pk),
        name=river.name,
        threads=[thread_out(thread, names, schema_names) for thread in river.threads],
        moments=[moment_out(moment) for moment in river.moments],
        events=[event_out(event) for event in river.events],
    )


def thread_out(thread: Thread, names: Mapping[int, str], schema_names: Mapping[str, str]) -> ThreadOut:
    return ThreadOut(
        id=thread.id,
        schema_slug=thread.schema,
        schema_name=schema_names.get(thread.schema, thread.schema),
        binding=[
            BindingEntry(role=role, entity_id=entity, entity_name=names.get(entity) if entity else None)
            for role, entity in thread.binding.items()
        ],
        open_steps=list(thread.open_steps),
        waiting_since=thread.waiting_since,
        payoff_steps=list(thread.payoff_steps),
    )


def moment_out(moment: Moment) -> MomentOut:
    return MomentOut(
        t=moment.t,
        shares=[
            ShareOut(thread=thread, share=share.share, status=share.status, secret=share.secret)
            for thread, share in moment.shares.items()
        ],
        other=moment.other,
        surprise=moment.surprise,
        tension=moment.tension,
    )


def event_out(event: Event) -> EventOut:
    return EventOut(t=event.t, thread=event.thread, kind=event.kind, step=event.step)
