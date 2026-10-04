"""Trying a beat before narrating it: what it would do to the lattice, and the vocabulary to compose it."""

from typing import Any

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from ninja.errors import HttpError

from chronicle.beat_log import AppendError
from chronicle.models import Chronicle
from gm_ui.audiences import ALL, resolve_audience
from gm_ui.lattice_api import BindingEntry
from matching.dry_run import CandidateBeat, Effect, dry_run
from schemas.models import Schema as SchemaRow
from schemas.vocabulary import BeatArgsError, default_vocabulary

router = Router()


class CandidateBeatIn(Schema):
    pred: str
    args: dict[str, Any]
    text: str = ""
    characters_present: list[int] = []
    players_present: list[int] = []
    audience: str = ALL  # whose lattice: "all" (the GM's) or a player id


class EffectOut(Schema):
    hypothesis_id: int | None  # None: the beat would create this hypothesis
    schema_slug: str
    schema_name: str
    binding: list[BindingEntry]
    changes: list[str]
    status: str
    filled_step: str | None
    weight_before: float | None
    weight_after: float
    refines: int | None


class DryRunOut(Schema):
    t: int
    effects: list[EffectOut]


@router.post("/chronicles/{chronicle_id}/dry-run", response=DryRunOut, url_name="dry_run_beat")
def dry_run_beat(request: HttpRequest, chronicle_id: int, candidate: CandidateBeatIn) -> DryRunOut:
    """What narrating the candidate as the next beat would do to a lattice. Nothing is kept."""
    chronicle = get_object_or_404(Chronicle, pk=chronicle_id)
    audience = resolve_audience(chronicle, candidate.audience)
    if not audience.everything and audience.player is None:
        raise HttpError(400, "the table has no lattice of its own: choose 'all' or a player")
    try:
        effects = dry_run(chronicle, candidate_beat(candidate), for_player=audience.player)
    except (BeatArgsError, AppendError) as error:
        raise HttpError(422, str(error)) from error
    names = dict(chronicle.entities.values_list("pk", "canonical_name"))
    schema_names = dict(SchemaRow.objects.values_list("slug", "name"))
    return DryRunOut(
        t=chronicle.beats.count() + 1,
        effects=[effect_out(effect, schema_names[effect.schema_slug], names) for effect in effects],
    )


def candidate_beat(candidate: CandidateBeatIn) -> CandidateBeat:
    return CandidateBeat(
        pred=candidate.pred,
        args=candidate.args,
        text=candidate.text,
        characters_present=candidate.characters_present,
        players_present=candidate.players_present,
    )


def effect_out(effect: Effect, schema_name: str, names: dict[int, str]) -> EffectOut:
    return EffectOut(
        hypothesis_id=effect.hypothesis_id,
        schema_slug=effect.schema_slug,
        schema_name=schema_name,
        binding=[
            BindingEntry(
                role=role, entity_id=entity, entity_name=names.get(entity) if entity is not None else None
            )
            for role, entity in effect.binding.items()
        ],
        changes=effect.changes,
        status=effect.status,
        filled_step=effect.filled_step,
        weight_before=effect.weight_before,
        weight_after=effect.weight_after,
        refines=effect.refines,
    )


class RoleOut(Schema):
    name: str
    kinds: list[str]
    optional: bool


class PredicateOut(Schema):
    name: str
    roles: list[RoleOut]


@router.get("/vocabulary", response=list[PredicateOut], url_name="get_vocabulary")
def get_vocabulary(request: HttpRequest) -> list[PredicateOut]:
    vocabulary = default_vocabulary()
    return [
        PredicateOut(
            name=name,
            roles=[
                RoleOut(name=role.name, kinds=sorted(role.kinds), optional=role.optional)
                for role in vocabulary.predicate(name).roles.values()
            ],
        )
        for name in vocabulary.predicate_names
    ]
