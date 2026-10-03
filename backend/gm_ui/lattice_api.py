"""The lattice screen's data: Lattice.at(t) for the GM's view or one player's, with names resolved."""

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from ninja.errors import HttpError

from chronicle.models import Chronicle
from gm_ui.audiences import ALL, resolve_audience
from matching.lattice import Lattice, LatticeHypothesis
from schemas.definitions import SchemaDefinition
from schemas.library import definition_of
from schemas.models import Schema as SchemaRow

router = Router()


class BindingEntry(Schema):
    role: str
    entity_id: int | None
    entity_name: str | None


class FilledStep(Schema):
    step_id: str
    beat_ts: list[int]


class LatticeHypothesisOut(Schema):
    id: int
    schema_slug: str
    schema_name: str
    binding: list[BindingEntry]
    status: str
    weight: float
    created_at_t: int
    status_changed_at_t: int | None
    filled_steps: list[FilledStep]
    open_steps: list[str]
    refines: int | None
    voiced: bool


class LatticeOut(Schema):
    t: int
    hypotheses: list[LatticeHypothesisOut]


@router.get("/chronicles/{chronicle_id}/lattice", response=LatticeOut, url_name="get_lattice")
def get_lattice(
    request: HttpRequest, chronicle_id: int, audience: str = ALL, t: int | None = None
) -> LatticeOut:
    """The unfiltered lattice ("all", the GM's view) or one player's lattice at t (default: latest)."""
    chronicle = get_object_or_404(Chronicle, pk=chronicle_id)
    resolved = resolve_audience(chronicle, audience)
    if not resolved.everything and resolved.player is None:
        raise HttpError(400, "the table has no lattice of its own: choose 'all' or a player")
    at_t = t if t is not None else chronicle.beats.count()
    lattice = Lattice.at(chronicle, at_t, for_player=resolved.player)
    names = dict(chronicle.entities.values_list("pk", "canonical_name"))
    schemas = {
        row.slug: row for row in SchemaRow.objects.filter(slug__in={h.schema for h in lattice.hypotheses})
    }
    definitions = {slug: definition_of(row) for slug, row in schemas.items()}
    return LatticeOut(
        t=at_t,
        hypotheses=[
            hypothesis_out(hypothesis, schemas[hypothesis.schema], definitions[hypothesis.schema], names)
            for hypothesis in lattice.hypotheses
        ],
    )


def hypothesis_out(
    hypothesis: LatticeHypothesis, row: SchemaRow, definition: SchemaDefinition, names: dict[int, str]
) -> LatticeHypothesisOut:
    fill_ts = {
        step.step_id: [f.beat_t for f in hypothesis.fills if f.step_id == step.step_id]
        for step in definition.steps
    }
    return LatticeHypothesisOut(
        id=hypothesis.id,
        schema_slug=row.slug,
        schema_name=row.name,
        binding=[
            BindingEntry(
                role=role, entity_id=entity, entity_name=names.get(entity) if entity is not None else None
            )
            for role, entity in hypothesis.binding.items()
        ],
        status=hypothesis.status,
        weight=hypothesis.weight,
        created_at_t=hypothesis.created_at_t,
        status_changed_at_t=hypothesis.status_changed_at_t,
        filled_steps=[FilledStep(step_id=step_id, beat_ts=ts) for step_id, ts in fill_ts.items() if ts],
        open_steps=[step_id for step_id, ts in fill_ts.items() if not ts],
        refines=hypothesis.refines_id,
        voiced=hypothesis.voiced_by is not None,
    )
