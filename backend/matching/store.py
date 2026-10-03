"""Running the matcher against a stored chronicle: load hypotheses, step a beat, save the changes."""

from collections.abc import Sequence

from django.conf import settings
from django.db import transaction

from chronicle.facts import StoredChronicleFacts
from chronicle.models import Beat, Chronicle
from matching.beats import PlainBeat
from matching.engine import Fill, HypothesisState, IncrementalMatcher, MatcherConfig, StepResult, World
from matching.models import Hypothesis, StepFill
from schemas.library import definition_of
from schemas.models import Schema


def matcher_config_from_settings() -> MatcherConfig:
    return MatcherConfig(
        repeatable_fill_cap=settings.MATCHER_REPEATABLE_FILL_CAP,
        weight_floor=settings.MATCHER_WEIGHT_FLOOR,
        max_live_per_schema=settings.MATCHER_MAX_LIVE_PER_SCHEMA,
    )


class StoredMatcher:
    def __init__(self, chronicle: Chronicle) -> None:
        self.chronicle = chronicle
        self.schema_rows = {schema.slug: schema for schema in Schema.objects.all()}
        self.definitions = {slug: definition_of(schema) for slug, schema in self.schema_rows.items()}
        self.engine = IncrementalMatcher(
            list(self.definitions.values()), self.load_hypotheses(), config=matcher_config_from_settings()
        )

    def step(self, beat: Beat) -> StepResult:
        result = self.engine.step(PlainBeat.from_model(beat), self.world())
        self.save([*result.new, *result.changed])
        return result

    def world(self) -> World:
        return World(
            entity_kinds=dict(self.chronicle.entities.values_list("pk", "kind")),
            players=frozenset(self.chronicle.players.values_list("pk", flat=True)),
            facts=StoredChronicleFacts(self.chronicle),
        )

    # Loading

    def load_hypotheses(self) -> list[HypothesisState]:
        rows = list(
            Hypothesis.objects.filter(chronicle=self.chronicle)
            .select_related("schema", "refuted_by")
            .order_by("pk")
        )
        fills = self.load_fills()
        states = {row.pk: self.state_from_row(row, fills.get(row.pk, [])) for row in rows}
        for row in rows:
            states[row.pk].refines = states.get(row.refines_id) if row.refines_id else None
            states[row.pk].merged_into = states.get(row.merged_into_id) if row.merged_into_id else None
        return list(states.values())

    def load_fills(self) -> dict[int, list[Fill]]:
        fills = StepFill.objects.filter(hypothesis__chronicle=self.chronicle).select_related("step", "beat")
        fills_by_hypothesis: dict[int, list[Fill]] = {}
        for fill in fills.order_by("beat__t", "pk"):
            fills_by_hypothesis.setdefault(fill.hypothesis_id, []).append(
                Fill(fill.step.step_id, fill.beat.t)
            )
        return fills_by_hypothesis

    def state_from_row(self, row: Hypothesis, fills: list[Fill]) -> HypothesisState:
        return HypothesisState(
            schema=self.definitions[row.schema.slug],
            binding=dict(row.binding),
            created_at_t=row.created_at_t,
            fills=fills,
            status=row.status,
            status_changed_at_t=row.status_changed_at_t,
            refuted_by_t=row.refuted_by.t if row.refuted_by else None,
            voiced_by=row.voiced_by_id,
            voiced_in=row.voiced_in_id,
            record_id=row.pk,
        )

    # Saving

    def save(self, states: Sequence[HypothesisState]) -> None:
        """Create rows first, so references between hypotheses saved together can be resolved."""
        with transaction.atomic():
            for state in states:
                if state.record_id is None:
                    state.record_id = self.create_row(state)
            for state in states:
                self.update_row(state)
                self.save_new_fills(stored_id(state), state)

    def create_row(self, state: HypothesisState) -> int:
        row = Hypothesis.objects.create(
            chronicle=self.chronicle,
            schema=self.schema_rows[state.schema.slug],
            binding=state.binding,
            weight=self.engine.weight(state),
            created_at_t=state.created_at_t,
        )
        return row.pk

    def update_row(self, state: HypothesisState) -> None:
        refuted_by = self.chronicle.beats.filter(t=state.refuted_by_t).first() if state.refuted_by_t else None
        Hypothesis.objects.filter(pk=stored_id(state)).update(
            binding=state.binding,
            weight=self.engine.weight(state),
            status=state.status,
            status_changed_at_t=state.status_changed_at_t,
            refuted_by=refuted_by,
            refines_id=state.refines.record_id if state.refines else None,
            merged_into_id=state.merged_into.record_id if state.merged_into else None,
            voiced_by_id=state.voiced_by,
            voiced_in_id=state.voiced_in,
        )

    def save_new_fills(self, record_id: int, state: HypothesisState) -> None:
        stored = set(StepFill.objects.filter(hypothesis_id=record_id).values_list("step__step_id", "beat__t"))
        steps = {step.step_id: step for step in self.schema_rows[state.schema.slug].steps.all()}
        beats = {
            beat.t: beat for beat in self.chronicle.beats.filter(t__in=[fill.beat_t for fill in state.fills])
        }
        StepFill.objects.bulk_create(
            StepFill(hypothesis_id=record_id, step=steps[fill.step_id], beat=beats[fill.beat_t])
            for fill in state.fills
            if (fill.step_id, fill.beat_t) not in stored
        )


def stored_id(state: HypothesisState) -> int:
    if state.record_id is None:
        raise ValueError("the hypothesis has not been stored yet")
    return state.record_id
