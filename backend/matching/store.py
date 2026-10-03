"""Running the matcher against a stored chronicle: load hypotheses, step a beat, save the changes."""

from django.conf import settings
from django.db import transaction

from chronicle.models import Beat, Chronicle
from matching.beats import PlainBeat
from matching.engine import Fill, HypothesisState, IncrementalMatcher, MatcherConfig, StepResult, World
from matching.models import Hypothesis, StepFill
from schemas.library import definition_of
from schemas.models import Schema


class StoredMatcher:
    def __init__(self, chronicle: Chronicle) -> None:
        self.chronicle = chronicle
        self.schema_rows = {schema.slug: schema for schema in Schema.objects.all()}
        self.definitions = {slug: definition_of(schema) for slug, schema in self.schema_rows.items()}
        self.engine = IncrementalMatcher(
            list(self.definitions.values()), self.load_hypotheses(), config=matcher_config_from_settings()
        )

    def load_hypotheses(self) -> list[HypothesisState]:
        rows = Hypothesis.objects.filter(chronicle=self.chronicle).select_related("schema").order_by("pk")
        fills = StepFill.objects.filter(hypothesis__chronicle=self.chronicle).select_related("step", "beat")
        fills_by_hypothesis: dict[int, list[Fill]] = {}
        for fill in fills.order_by("beat__t", "pk"):
            fills_by_hypothesis.setdefault(fill.hypothesis_id, []).append(
                Fill(fill.step.step_id, fill.beat.t)
            )
        states = {
            row.pk: HypothesisState(
                schema=self.definitions[row.schema.slug],
                binding=dict(row.binding),
                created_at_t=row.created_at_t,
                fills=fills_by_hypothesis.get(row.pk, []),
                status=row.status,
                status_changed_at_t=row.status_changed_at_t,
                record_id=row.pk,
            )
            for row in rows
        }
        for row in rows:
            if row.refines_id is not None:
                states[row.pk].refines = states[row.refines_id]
        return list(states.values())

    def world(self) -> World:
        return World(
            entity_kinds=dict(self.chronicle.entities.values_list("pk", "kind")),
            players=frozenset(self.chronicle.players.values_list("pk", flat=True)),
        )

    def step(self, beat: Beat) -> StepResult:
        result = self.engine.step(PlainBeat.from_model(beat), self.world())
        with transaction.atomic():
            for state in [*result.new, *result.changed]:
                self.save(state)
        return result

    def save(self, state: HypothesisState) -> None:
        if state.record_id is None:
            state.record_id = self.create_row(state)
        Hypothesis.objects.filter(pk=state.record_id).update(
            binding=state.binding,
            weight=self.engine.weight(state),
            status=state.status,
            status_changed_at_t=state.status_changed_at_t,
        )
        self.save_new_fills(state.record_id, state)

    def create_row(self, state: HypothesisState) -> int:
        row = Hypothesis.objects.create(
            chronicle=self.chronicle,
            schema=self.schema_rows[state.schema.slug],
            binding=state.binding,
            weight=self.engine.weight(state),
            created_at_t=state.created_at_t,
            refines_id=state.refines.record_id if state.refines else None,
        )
        return row.pk

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


def matcher_config_from_settings() -> MatcherConfig:
    return MatcherConfig(repeatable_fill_cap=settings.MATCHER_REPEATABLE_FILL_CAP)
