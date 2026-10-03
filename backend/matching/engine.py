"""The incremental matcher (concept §7): new beat × open steps of live hypotheses, plus new beat ×
trigger steps. Works on plain data; matching/store.py loads and saves the hypotheses."""

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field

from matching.beats import PlainBeat
from matching.match import MatchContext, match
from schemas.constraints import ChronicleFacts
from schemas.definitions import SchemaDefinition, StepDefinition

LIVE = "live"
COMPLETE = "complete"
REFUTED = "refuted"
MERGED = "merged"
PRUNED = "pruned"


@dataclass(frozen=True)
class Fill:
    step_id: str
    beat_t: int


@dataclass(eq=False)
class HypothesisState:
    """A partial match of a schema: binding (role -> entity id, None = open) plus step fills."""

    schema: SchemaDefinition
    binding: dict[str, int | None]
    created_at_t: int
    fills: list[Fill] = field(default_factory=list)
    status: str = LIVE
    status_changed_at_t: int | None = None
    refuted_by_t: int | None = None
    refines: "HypothesisState | None" = None  # the less specific hypothesis this one was refined from
    merged_into: "HypothesisState | None" = None
    voiced_by: int | None = None  # player id
    voiced_in: int | None = None  # utterance id
    record_id: int | None = None  # primary key once stored

    @property
    def is_live(self) -> bool:
        return self.status == LIVE

    def fill_ts(self, step_id: str) -> list[int]:
        return [fill.beat_t for fill in self.fills if fill.step_id == step_id]

    def fills_by_step(self) -> dict[str, list[int]]:
        return {step.step_id: self.fill_ts(step.step_id) for step in self.schema.steps}

    def accepts_fill(self, step: StepDefinition) -> bool:
        return step.repeatable or not self.fill_ts(step.step_id)

    def has_fill(self, beat_t: int) -> bool:
        return any(fill.beat_t == beat_t for fill in self.fills)

    def change_status(self, status: str, t: int) -> None:
        self.status, self.status_changed_at_t = status, t

    def identity(self) -> tuple[object, ...]:
        """Hypotheses with the same identity say the same thing and are merged."""
        fills = sorted((fill.step_id, fill.beat_t) for fill in self.fills)
        return (self.schema.slug, tuple(sorted(self.binding.items())), tuple(fills))


@dataclass(frozen=True)
class MatcherConfig:
    repeatable_fill_cap: int = 3  # fills of a repeatable step that add weight
    weight_floor: float = -6.0  # live hypotheses below this weight are pruned
    max_live_per_schema: int = 50  # beyond this, the lowest-weighted live hypotheses are pruned


def weight_of(schema: SchemaDefinition, fills: Iterable[Fill], repeat_cap: int) -> float:
    """Prior log-odds plus the weight of each filled step; repeatable steps count up to the cap."""
    fill_counts = Counter(fill.step_id for fill in fills)
    return schema.prior + sum(
        step.weight * min(fill_counts[step.step_id], repeat_cap if step.repeatable else 1)
        for step in schema.steps
    )


def is_complete(hypothesis: "HypothesisState") -> bool:
    return all(hypothesis.fill_ts(step.step_id) for step in hypothesis.schema.steps if step.required)


@dataclass(frozen=True)
class World:
    """What the matcher needs to know about the chronicle besides the beat."""

    entity_kinds: Mapping[int, str]
    players: frozenset[int] = frozenset()
    # Without facts constraints are not checked, which lets tests exercise matching in isolation.
    facts: ChronicleFacts | None = None
    for_player: int | None = None  # matching for one player's lattice

    def context_for(self, schema: SchemaDefinition, fills: Mapping[str, Sequence[int]]) -> MatchContext:
        return MatchContext(
            role_kinds=schema.roles,
            entity_kinds=self.entity_kinds,
            fills=fills,
            players=self.players,
            for_player=self.for_player,
        )


@dataclass
class StepResult:
    new: list[HypothesisState] = field(default_factory=list)
    changed: list[HypothesisState] = field(default_factory=list)


def open_binding(schema: SchemaDefinition) -> dict[str, int | None]:
    return {role: None for role in schema.roles}


def compatible(first: Mapping[str, int | None], second: Mapping[str, int | None]) -> bool:
    """No role is bound to different entities in the two bindings."""
    return all(first[role] is None or second.get(role) in (None, first[role]) for role in first)


class IncrementalMatcher:
    def __init__(
        self,
        schemas: Sequence[SchemaDefinition],
        hypotheses: Iterable[HypothesisState] = (),
        config: MatcherConfig | None = None,
    ) -> None:
        self.schemas = list(schemas)
        self.hypotheses = list(hypotheses)
        self.config = config or MatcherConfig()

    def weight(self, hypothesis: HypothesisState) -> float:
        return weight_of(hypothesis.schema, hypothesis.fills, self.config.repeatable_fill_cap)

    def live(self) -> list[HypothesisState]:
        return [hypothesis for hypothesis in self.hypotheses if hypothesis.is_live]

    def step(self, beat: PlainBeat, world: World) -> StepResult:
        """Fill: the beat goes to every live hypothesis that can take it under its binding. Hypotheses
        whose binding it would extend get a refined child instead, and trigger steps seed new
        hypotheses; both only when no live hypothesis of the schema already holds the beat."""
        filled = self.fill(beat, world)
        refined = self.refine(beat, world, filled)
        self.hypotheses += refined
        seeded = self.seed(beat, world)
        self.hypotheses += seeded
        new = refined + seeded
        refuted = self.refute(beat, world)
        self.complete(beat, [*filled, *new])
        merged = self.merge(beat)
        pruned = self.prune(beat)
        status_changed = [*refuted, *merged, *pruned]
        changed = list(dict.fromkeys([*filled, *(h for h in status_changed if h not in new)]))
        return StepResult(new=new, changed=changed)

    def refute(self, beat: PlainBeat, world: World) -> list[HypothesisState]:
        """Maintain: refute live hypotheses the beat contradicts or whose constraints no longer hold."""
        refuted = [
            hypothesis
            for hypothesis in self.live()
            if self.contradicted(hypothesis, beat, world)
            or self.violates_constraints(hypothesis, world, beat.t)
        ]
        for hypothesis in refuted:
            hypothesis.change_status(REFUTED, beat.t)
            hypothesis.refuted_by_t = beat.t
        return refuted

    def contradicted(self, hypothesis: HypothesisState, beat: PlainBeat, world: World) -> bool:
        """The beat matches a `contradicts` pattern of a step not yet filled, without new bindings."""
        context = world.context_for(hypothesis.schema, hypothesis.fills_by_step())
        return any(
            match(pattern, beat, hypothesis.binding, context) == hypothesis.binding
            for step in hypothesis.schema.steps
            if not hypothesis.fill_ts(step.step_id)
            for pattern in step.contradicts
        )

    def violates_constraints(self, hypothesis: HypothesisState, world: World, t: int) -> bool:
        if world.facts is None:
            return False
        return not all(
            constraint.check(hypothesis, world.facts, t) for constraint in hypothesis.schema.constraints
        )

    def merge(self, beat: PlainBeat) -> list[HypothesisState]:
        """Maintain: a live hypothesis identical to an older one is merged into it."""
        survivors: dict[tuple[object, ...], HypothesisState] = {}
        merged = []
        for hypothesis in sorted(self.live(), key=lambda hypothesis: hypothesis.created_at_t):
            survivor = survivors.setdefault(hypothesis.identity(), hypothesis)
            if survivor is hypothesis:
                continue
            survivor.voiced_by = survivor.voiced_by or hypothesis.voiced_by
            survivor.voiced_in = survivor.voiced_in or hypothesis.voiced_in
            hypothesis.change_status(MERGED, beat.t)
            hypothesis.merged_into = survivor
            merged.append(hypothesis)
        return merged

    def prune(self, beat: PlainBeat) -> list[HypothesisState]:
        """Maintain: prune hypotheses below the weight floor, then the weakest beyond the maximum per
        schema (ties: newest first). Voiced hypotheses record what the table believes and are kept."""
        prunable = [hypothesis for hypothesis in self.live() if hypothesis.voiced_by is None]
        pruned = [hypothesis for hypothesis in prunable if self.weight(hypothesis) < self.config.weight_floor]
        for schema in self.schemas:
            ranked = sorted(
                (h for h in prunable if h.schema.slug == schema.slug and h not in pruned),
                key=lambda hypothesis: (-self.weight(hypothesis), hypothesis.created_at_t),
            )
            pruned += ranked[self.config.max_live_per_schema :]
        for hypothesis in pruned:
            hypothesis.change_status(PRUNED, beat.t)
        return pruned

    def complete(self, beat: PlainBeat, touched: Sequence[HypothesisState]) -> None:
        for hypothesis in touched:
            if hypothesis.is_live and is_complete(hypothesis):
                hypothesis.change_status(COMPLETE, beat.t)

    def fill(self, beat: PlainBeat, world: World) -> list[HypothesisState]:
        filled = []
        for hypothesis in self.live():
            step = next(
                (
                    step
                    for step, binding in self.matches(hypothesis, beat, world)
                    if binding == hypothesis.binding
                ),
                None,
            )
            if step is not None:
                hypothesis.fills.append(Fill(step.step_id, beat.t))
                filled.append(hypothesis)
        return filled

    def refine(
        self, beat: PlainBeat, world: World, filled: Sequence[HypothesisState]
    ) -> list[HypothesisState]:
        children: list[HypothesisState] = []
        for parent in self.live():
            if parent in filled:
                continue
            for step, binding in self.matches(parent, beat, world):
                if binding == parent.binding or self.already_covered(parent.schema, beat, binding, children):
                    continue
                children.append(
                    HypothesisState(
                        schema=parent.schema,
                        binding=binding,
                        created_at_t=beat.t,
                        fills=[*parent.fills, Fill(step.step_id, beat.t)],
                        refines=parent,
                    )
                )
                break
        return children

    def matches(
        self, hypothesis: HypothesisState, beat: PlainBeat, world: World
    ) -> Iterable[tuple[StepDefinition, dict[str, int | None]]]:
        """(step, binding) for every open step pattern the beat matches, in step order."""
        context = world.context_for(hypothesis.schema, hypothesis.fills_by_step())
        for step in hypothesis.schema.steps:
            if not hypothesis.accepts_fill(step):
                continue
            for pattern in step.patterns:
                binding = match(pattern, beat, hypothesis.binding, context)
                if binding is not None:
                    yield step, binding

    def seed(self, beat: PlainBeat, world: World) -> list[HypothesisState]:
        seeded: list[HypothesisState] = []
        for schema in self.schemas:
            for step, binding in self.trigger_matches(schema, beat, world):
                if self.already_covered(schema, beat, binding, seeded):
                    continue
                seeded.append(
                    HypothesisState(
                        schema=schema,
                        binding=binding,
                        created_at_t=beat.t,
                        fills=[Fill(step.step_id, beat.t)],
                    )
                )
        return seeded

    def trigger_matches(
        self, schema: SchemaDefinition, beat: PlainBeat, world: World
    ) -> Iterable[tuple[StepDefinition, dict[str, int | None]]]:
        context = world.context_for(schema, {})
        for step in schema.steps:
            if not step.trigger:
                continue
            for pattern in step.patterns:
                binding = match(pattern, beat, open_binding(schema), context)
                if binding is not None:
                    yield step, binding

    def already_covered(
        self,
        schema: SchemaDefinition,
        beat: PlainBeat,
        binding: Mapping[str, int | None],
        seeded: Sequence[HypothesisState],
    ) -> bool:
        """A live hypothesis of the schema already holds this beat under a compatible binding."""
        candidates = [*self.live(), *seeded]
        return any(
            hypothesis.schema.slug == schema.slug
            and hypothesis.has_fill(beat.t)
            and compatible(hypothesis.binding, binding)
            for hypothesis in candidates
        )
