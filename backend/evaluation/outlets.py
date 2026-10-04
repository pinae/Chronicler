"""Comparing outlets (concept §9.4, RQ4): how strongly each outlet's coverage instantiates a
narrative, how much the outlets agree on it, and how much of it rests on claims that fact-checkers
labeled false or unverified.

The engine measures narrative instantiation; it does not judge truth. Fact labels are read from
annotators and imports (WP-053), never produced here."""

from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass

from chronicle.models import Chronicle, EntityKind, FactLabel, Verdict
from evaluation.metrics import HELD, Share
from matching.engine import Fill
from matching.lattice import Lattice
from schemas.definitions import SchemaDefinition

SUSPECT_VERDICTS = (Verdict.FALSE, Verdict.UNVERIFIED)


@dataclass(frozen=True)
class Reading:
    """A hypothesis as it is compared across chronicles: entities by slug, since ids differ."""

    schema: str
    binding: tuple[tuple[str, str | None], ...]  # (role, entity slug or None)
    status: str
    weight: float
    fills: tuple[Fill, ...]


@dataclass(frozen=True)
class OutletLattice:
    outlet: str
    readings: tuple[Reading, ...]
    suspect_ts: frozenset[int]  # beats labeled false or unverified by any labeler


def outlet_lattice(chronicle: Chronicle) -> OutletLattice:
    """The lattice of a media chronicle at its last beat, with the beats fact-checkers doubt."""
    slugs = dict(chronicle.entities.values_list("pk", "slug"))
    lattice = Lattice.at(chronicle, chronicle.beats.count())
    suspect = FactLabel.objects.filter(beat__chronicle=chronicle, verdict__in=SUSPECT_VERDICTS)
    return OutletLattice(
        outlet=chronicle.title,
        readings=tuple(
            Reading(
                schema=hypothesis.schema,
                binding=tuple(
                    (role, slugs.get(entity) if entity else None)
                    for role, entity in hypothesis.binding.items()
                ),
                status=hypothesis.status,
                weight=hypothesis.weight,
                fills=hypothesis.fills,
            )
            for hypothesis in lattice.hypotheses
        ),
        suspect_ts=frozenset(suspect.values_list("beat__t", flat=True)),
    )


def held_readings(outlet: OutletLattice, schema: SchemaDefinition) -> list[Reading]:
    return [
        reading for reading in outlet.readings if reading.schema == schema.slug and reading.status in HELD
    ]


def completion(outlet: OutletLattice, schema: SchemaDefinition) -> Share:
    """The share of the schema's required steps that the outlet's best reading filled."""
    required = {step.step_id for step in schema.steps if step.required}
    filled = [
        {fill.step_id for fill in reading.fills} & required for reading in held_readings(outlet, schema)
    ]
    return Share(max((len(steps) for steps in filled), default=0), len(required))


def step_overlap(first: OutletLattice, second: OutletLattice, schema: SchemaDefinition) -> Share:
    """Of the (reading, step) pairs either outlet filled, how many both filled."""
    first_steps, second_steps = filled_steps(first, schema), filled_steps(second, schema)
    return Share(len(first_steps & second_steps), len(first_steps | second_steps))


def filled_steps(outlet: OutletLattice, schema: SchemaDefinition) -> set[tuple[object, str]]:
    """(reading, step) pairs; a reading is its binding without the source roles, since each outlet
    is the source of its own claims."""
    return {
        (without_sources(reading.binding, schema), fill.step_id)
        for reading in held_readings(outlet, schema)
        for fill in reading.fills
    }


def without_sources(
    binding: tuple[tuple[str, str | None], ...], schema: SchemaDefinition
) -> tuple[object, ...]:
    return tuple((role, slug) for role, slug in binding if schema.roles[role] != EntityKind.SOURCE)


def suspect_weight_share(outlet: OutletLattice, schema: SchemaDefinition, repeat_cap: int) -> float | None:
    """The share of the strongest reading's step weight that rests on beats labeled false or
    unverified. None without a held reading that any beat fills."""
    readings = [reading for reading in held_readings(outlet, schema) if reading.fills]
    if not readings:
        return None
    strongest = max(readings, key=lambda reading: reading.weight)
    weighted = list(fill_weights(strongest, schema, repeat_cap))
    total = sum(weight for _, weight in weighted)
    if total == 0:
        return None
    return sum(weight for fill, weight in weighted if fill.beat_t in outlet.suspect_ts) / total


def fill_weights(reading: Reading, schema: SchemaDefinition, repeat_cap: int) -> Iterator[tuple[Fill, float]]:
    """Each fill with the weight it adds; fills of a repeatable step beyond the cap add none."""
    steps = {step.step_id: step for step in schema.steps}
    counted: Counter[str] = Counter()
    for fill in sorted(reading.fills, key=lambda fill: fill.beat_t):
        step = steps[fill.step_id]
        limit = repeat_cap if step.repeatable else 1
        counted[fill.step_id] += 1
        yield fill, step.weight if counted[fill.step_id] <= limit else 0.0
