"""The Seed phase (concept §3): ask the reader model what the audience expects next for each live
hypothesis, and store the answers per t.

Runs after the matcher's Maintain phase, so no question is asked about a hypothesis the same beat
refuted. An audience is only asked about hypotheses whose fills it has seen and whose bound entities
it knows, so a question never gives away a beat the audience has not seen.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from django.conf import settings

from chronicle.models import Chronicle, Player
from matching.engine import Fill
from matching.lattice import Lattice, LatticeHypothesis
from matching.models import Expectation
from reader.context import ContextBuilder, Supporting
from reader.interfaces import Question, ReaderModel, Readout
from reader.questions import build_questions, entities_in_view, next_open_step
from schemas.definitions import SchemaDefinition
from schemas.library import definition_of
from schemas.models import Schema, Step


@dataclass(frozen=True)
class AskableHypothesis:
    schema: SchemaDefinition
    binding: Mapping[str, int | None]
    fills: tuple[Fill, ...]

    def fill_ts(self, step_id: str) -> list[int]:
        return [fill.beat_t for fill in self.fills if fill.step_id == step_id]


def seed_expectations(
    chronicle: Chronicle,
    t: int,
    audience: Player | None,
    reader: ReaderModel,
    context_builder: ContextBuilder,
) -> list[Expectation]:
    """Expectations of `audience` (a player, or None for the whole table) at t, about the hypotheses
    of that audience's lattice."""
    visible_ts = set(chronicle.visible_to(audience, t).values_list("t", flat=True))
    entities = entities_in_view(chronicle, audience, t)
    known_entity_ids = {entity.id for entity in entities}
    askable = [
        hypothesis
        for hypothesis in Lattice.at(chronicle, t, for_player=audience).live()
        if seen_by_audience(hypothesis, visible_ts, known_entity_ids)
    ]
    supporting = [
        Supporting(hypothesis.weight, tuple(fill.beat_t for fill in hypothesis.fills))
        for hypothesis in askable
    ]
    context = context_builder.build(chronicle, audience, t, supporting)
    step_texts = {beat.t: beat.text.rstrip(".") for beat in context.beats}
    definitions = {
        slug: definition_of(schema) for slug, schema in Schema.objects.in_bulk(field_name="slug").items()
    }
    expectations = []
    for hypothesis in askable:
        askable_state = AskableHypothesis(
            definitions[hypothesis.schema], hypothesis.binding, hypothesis.fills
        )
        step = next_open_step(askable_state)
        if step is None:
            continue
        step_row = Step.objects.get(schema__slug=hypothesis.schema, step_id=step.step_id)
        questions = build_questions(
            askable_state, t, entities, step_texts, max_candidates=settings.READER_MAX_CANDIDATES
        )
        for question in questions:
            readout = reader.readout(context, question)
            expectations.append(store_expectation(hypothesis, step_row, t, audience, question, readout))
    return expectations


def seen_by_audience(hypothesis: LatticeHypothesis, visible_ts: set[int], known_entity_ids: set[int]) -> bool:
    fills_seen = all(fill.beat_t in visible_ts for fill in hypothesis.fills)
    bound = {entity for entity in hypothesis.binding.values() if entity is not None}
    return fills_seen and bound <= known_entity_ids


def store_expectation(
    hypothesis: LatticeHypothesis,
    step: Step,
    t: int,
    audience: Player | None,
    question: Question,
    readout: Readout,
) -> Expectation:
    return Expectation.objects.create(
        hypothesis_id=hypothesis.id,
        step=step,
        computed_at_t=t,
        for_player=audience,
        question=question.text,
        candidates=[
            candidate_record(candidate.label, candidate.text, candidate.binding_delta, readout)
            for candidate in question.candidates
        ],
        outside_mass=readout.outside_mass,
        llm_call_id=readout.llm_call_id,
    )


def candidate_record(
    label: str, text: str, binding_delta: Mapping[str, int] | None, readout: Readout
) -> dict[str, Any]:
    record: dict[str, Any] = {"label": label, "text": text}
    if binding_delta is None:
        record["null"] = True
    else:
        record["binding_delta"] = dict(binding_delta)
    record["p"] = readout.probabilities.get(label, 0.0)
    return record
