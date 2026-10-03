"""The incremental matcher (concept §7): new beat × open steps of live hypotheses, plus new beat ×
trigger steps. Works on plain data; matching/store.py loads and saves the hypotheses."""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field

from matching.beats import PlainBeat
from matching.match import MatchContext, match
from schemas.definitions import SchemaDefinition, StepDefinition

LIVE = "live"


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
    record_id: int | None = None  # primary key once stored

    @property
    def is_live(self) -> bool:
        return self.status == LIVE

    @property
    def weight(self) -> float:
        return self.schema.prior + sum(self.schema.step(fill.step_id).weight for fill in self.fills)

    def fill_ts(self, step_id: str) -> list[int]:
        return [fill.beat_t for fill in self.fills if fill.step_id == step_id]

    def fills_by_step(self) -> dict[str, list[int]]:
        return {step.step_id: self.fill_ts(step.step_id) for step in self.schema.steps}

    def accepts_fill(self, step: StepDefinition) -> bool:
        return step.repeatable or not self.fill_ts(step.step_id)

    def has_fill(self, beat_t: int) -> bool:
        return any(fill.beat_t == beat_t for fill in self.fills)


@dataclass(frozen=True)
class World:
    """What the matcher needs to know about the chronicle besides the beat."""

    entity_kinds: Mapping[int, str]
    players: frozenset[int] = frozenset()

    def context_for(self, schema: SchemaDefinition, fills: Mapping[str, Sequence[int]]) -> MatchContext:
        return MatchContext(
            role_kinds=schema.roles, entity_kinds=self.entity_kinds, fills=fills, players=self.players
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
        self, schemas: Sequence[SchemaDefinition], hypotheses: Iterable[HypothesisState] = ()
    ) -> None:
        self.schemas = list(schemas)
        self.hypotheses = list(hypotheses)

    def live(self) -> list[HypothesisState]:
        return [hypothesis for hypothesis in self.hypotheses if hypothesis.is_live]

    def step(self, beat: PlainBeat, world: World) -> StepResult:
        result = StepResult(changed=self.fill(beat, world))
        result.new = self.seed(beat, world)
        self.hypotheses += result.new
        return result

    def fill(self, beat: PlainBeat, world: World) -> list[HypothesisState]:
        filled = []
        for hypothesis in self.live():
            step = self.fillable_step(hypothesis, beat, world)
            if step is not None:
                hypothesis.fills.append(Fill(step.step_id, beat.t))
                filled.append(hypothesis)
        return filled

    def fillable_step(
        self, hypothesis: HypothesisState, beat: PlainBeat, world: World
    ) -> StepDefinition | None:
        """The first open step the beat fills under the hypothesis' binding, unchanged."""
        context = world.context_for(hypothesis.schema, hypothesis.fills_by_step())
        for step in hypothesis.schema.steps:
            if not hypothesis.accepts_fill(step):
                continue
            for pattern in step.patterns:
                if match(pattern, beat, hypothesis.binding, context) == hypothesis.binding:
                    return step
        return None

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
