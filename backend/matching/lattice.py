"""The hypothesis lattice at any t (concept §4, replay guarantee).

Every change to a hypothesis is time-indexed: it exists from created_at_t, its fills carry their
beat's t, and it changes status once, at status_changed_at_t. The lattice at t is therefore a filter
over stored rows, never a snapshot.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Self

from django.conf import settings

from chronicle.models import Chronicle, Player
from matching.engine import LIVE, Fill, weight_of
from matching.models import Hypothesis, StepFill
from schemas.definitions import SchemaDefinition
from schemas.library import definition_of


@dataclass(frozen=True)
class LatticeHypothesis:
    id: int
    schema: str
    binding: Mapping[str, int | None]
    status: str
    weight: float
    created_at_t: int
    fills: tuple[Fill, ...]
    status_changed_at_t: int | None = None
    refuted_by_t: int | None = None
    refines_id: int | None = None
    merged_into_id: int | None = None
    voiced_by: int | None = None  # set from voiced_at_t on
    voiced_in: int | None = None
    voiced_at_t: int | None = None

    @property
    def is_live(self) -> bool:
        return self.status == LIVE


@dataclass(frozen=True)
class Lattice:
    t: int
    hypotheses: tuple[LatticeHypothesis, ...]

    @classmethod
    def at(cls, chronicle: Chronicle, t: int, for_player: Player | None = None) -> Self:
        """The unfiltered lattice at t, or with `for_player` that player's lattice."""
        rows = (
            Hypothesis.objects.filter(chronicle=chronicle, for_player=for_player, created_at_t__lte=t)
            .select_related("schema", "refuted_by")
            .order_by("created_at_t", "pk")
        )
        fills = fills_up_to(chronicle, t)
        definitions: dict[str, SchemaDefinition] = {}
        hypotheses = []
        for row in rows:
            definition = definitions.setdefault(row.schema.slug, definition_of(row.schema))
            hypotheses.append(hypothesis_at(row, t, definition, fills.get(row.pk, ())))
        return cls(t=t, hypotheses=tuple(hypotheses))

    def live(self) -> list[LatticeHypothesis]:
        return [hypothesis for hypothesis in self.hypotheses if hypothesis.is_live]


def fills_up_to(chronicle: Chronicle, t: int) -> dict[int, tuple[Fill, ...]]:
    fills: dict[int, list[Fill]] = {}
    rows = StepFill.objects.filter(hypothesis__chronicle=chronicle, beat__t__lte=t).select_related(
        "step", "beat"
    )
    for fill in rows.order_by("beat__t", "pk"):
        fills.setdefault(fill.hypothesis_id, []).append(Fill(fill.step.step_id, fill.beat.t))
    return {hypothesis_id: tuple(hypothesis_fills) for hypothesis_id, hypothesis_fills in fills.items()}


def hypothesis_at(
    row: Hypothesis, t: int, definition: SchemaDefinition, fills: tuple[Fill, ...]
) -> LatticeHypothesis:
    changed_by_t = row.status_changed_at_t is not None and row.status_changed_at_t <= t
    voiced_by_t = row.voiced_at_t is not None and row.voiced_at_t <= t
    return LatticeHypothesis(
        id=row.pk,
        schema=row.schema.slug,
        binding=row.binding,
        status=row.status if changed_by_t else LIVE,
        weight=weight_of(definition, fills, settings.MATCHER_REPEATABLE_FILL_CAP),
        created_at_t=row.created_at_t,
        fills=fills,
        status_changed_at_t=row.status_changed_at_t if changed_by_t else None,
        refuted_by_t=row.refuted_by.t if changed_by_t and row.refuted_by else None,
        refines_id=row.refines_id,
        merged_into_id=row.merged_into_id if changed_by_t else None,
        voiced_by=row.voiced_by_id if voiced_by_t else None,
        voiced_in=row.voiced_in_id if voiced_by_t else None,
        voiced_at_t=row.voiced_at_t if voiced_by_t else None,
    )
