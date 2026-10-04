"""What the reader model makes of a story's ground truth (concept §9.2): the inputs of retrospective
fit, the surprise curve and calibration.

Asked after the replay, for the table's view: every input (visible beats, lattice, context) is
time-indexed, so each answer is the one the reader would have given at that t.

Hypotheses are put to the reader in one generic phrasing, "a Betrayal with T = Aldric, V = Mira",
for the truth and its rivals alike, so a Bayes factor compares stories, not wordings.
"""

from collections.abc import Mapping, Sequence
from typing import Any

from chronicle.models import Chronicle
from evaluation.ground_truth import NO_ONE, GroundTruth
from evaluation.metrics import HELD
from matching.lattice import Lattice, LatticeHypothesis
from reader.bayes import bayes_factor
from reader.context import ContextBuilder, Supporting
from reader.expectations import seen_by_audience
from reader.interfaces import Candidate, ContextBeat, Question, ReaderContext, ReaderModel
from reader.questions import entities_in_view
from schemas.models import Schema

TABLE = None  # the audience whose view is evaluated: everything every player saw


def read_truth(
    chronicle: Chronicle, truth: GroundTruth, reader: ReaderModel, context_builder: ContextBuilder
) -> dict[str, Any]:
    """The run file's `truth` record: the ground truth in entity ids plus the reader's answers."""
    return TruthReader(chronicle, truth, reader, context_builder).record()


class TruthReader:
    def __init__(
        self, chronicle: Chronicle, truth: GroundTruth, reader: ReaderModel, context_builder: ContextBuilder
    ) -> None:
        self.chronicle = chronicle
        self.truth = truth
        self.reader = reader
        self.context_builder = context_builder
        self.entity_ids = dict(chronicle.entities.values_list("slug", "pk"))
        self.names = dict(chronicle.entities.values_list("pk", "canonical_name"))
        self.schema_names = dict(Schema.objects.values_list("slug", "name"))
        self.true_binding = {
            role: self.entity_ids[slug] for role, slug in truth.true_hypothesis.binding.items()
        }
        self.true_description = self.describe(truth.true_hypothesis.schema, self.true_binding)

    def record(self) -> dict[str, Any]:
        return {
            "reveal_t": self.truth.reveal_t,
            "schema": self.truth.true_hypothesis.schema,
            "binding": self.true_binding,
            "dormant_window": list(self.truth.dormant_window),
            "beliefs": self.beliefs(),
            "bayes_factors": self.bayes_factors(),
            "reader_beliefs": [
                self.answer(belief.t, belief.question, belief.answer) for belief in self.truth.reader_beliefs
            ],
        }

    # Belief in the truth, per t

    def beliefs(self) -> list[dict[str, Any]]:
        """P("yes") to "Is the story <truth>?" at every t at which the table knows the truth's
        entities; asking earlier would name someone the table has not met."""
        beliefs = []
        for t in range(1, self.chronicle.beats.count() + 1):
            known = {entity.id for entity in entities_in_view(self.chronicle, TABLE, t)}
            if not set(self.true_binding.values()) <= known:
                continue
            question = Question(
                t=t,
                text=f"Is the story {self.true_description}?",
                candidates=(Candidate("A", "yes", self.true_binding), Candidate("B", "no", None)),
            )
            readout = self.reader.readout(self.context_at(t), question)
            beliefs.append(
                {"t": t, "p": readout.probabilities.get("A", 0.0), "llm_call": readout.llm_call_id}
            )
        return beliefs

    # Bayes factors in the dormant window

    def bayes_factors(self) -> list[dict[str, Any]] | None:
        """Per beat of the dormant window the table saw: log p(beat | truth) - log p(beat | the
        table's strongest other reading before the beat). None if the reader cannot score beats."""
        start, end = self.truth.dormant_window
        visible = {beat.t: beat for beat in self.chronicle.visible_to(TABLE, end) if beat.t >= start}
        try:
            return [self.bayes_factor_at(beat.t, beat.text) for beat in visible.values()]
        except NotImplementedError:
            return None

    def bayes_factor_at(self, t: int, text: str) -> dict[str, Any]:
        rival = self.strongest_rival(t - 1)
        rival_assumption = (
            None if rival is None else self.assumption(self.describe(rival.schema, rival.binding))
        )
        log_factor = bayes_factor(
            self.reader,
            ContextBeat(t=t, text=text),
            self.context_at(t - 1),
            self.assumption(self.true_description),
            rival_assumption,
        )
        return {"t": t, "log_bayes_factor": log_factor, "dominant": rival.id if rival else None}

    def strongest_rival(self, t: int) -> LatticeHypothesis | None:
        """The strongest reading at t the table could hold (it saw every fill) that is not the truth.
        Hypotheses without fills exist only because a player voiced them. Ties: the older first."""
        rivals = [
            hypothesis
            for hypothesis in self.table_readings(t)
            if hypothesis.fills and not self.reads_as_truth(hypothesis)
        ]
        return min(rivals, key=lambda h: (-h.weight, h.created_at_t), default=None)

    def reads_as_truth(self, hypothesis: LatticeHypothesis) -> bool:
        return hypothesis.schema == self.truth.true_hypothesis.schema and all(
            hypothesis.binding.get(role) == entity for role, entity in self.true_binding.items()
        )

    # Annotated reader beliefs

    def answer(self, t: int, question_text: str, annotated: Mapping[str, float]) -> dict[str, Any]:
        """The annotated question with the annotated answers as candidates, in their order."""
        slugs = list(annotated)
        candidates = tuple(
            self.candidate(label, slug) for label, slug in zip(labels(len(slugs)), slugs, strict=True)
        )
        readout = self.reader.readout(
            self.context_at(t), Question(t=t, text=question_text, candidates=candidates)
        )
        return {
            "t": t,
            "question": question_text,
            "annotated": dict(annotated),
            "readout": {
                slug: readout.probabilities.get(c.label, 0.0)
                for slug, c in zip(slugs, candidates, strict=True)
            },
        }

    def candidate(self, label: str, slug: str) -> Candidate:
        if slug == NO_ONE:
            return Candidate(label, "nothing like this", None)
        entity_id = self.entity_ids[slug]
        return Candidate(label, self.names[entity_id], {"answer": entity_id})

    # Shared

    def table_readings(self, t: int) -> list[LatticeHypothesis]:
        visible_ts = set(self.chronicle.visible_to(TABLE, t).values_list("t", flat=True))
        known = {entity.id for entity in entities_in_view(self.chronicle, TABLE, t)}
        return [
            hypothesis
            for hypothesis in Lattice.at(self.chronicle, t).hypotheses
            if hypothesis.status in HELD and seen_by_audience(hypothesis, visible_ts, known)
        ]

    def context_at(self, t: int) -> ReaderContext:
        supporting = [
            Supporting(hypothesis.weight, tuple(fill.beat_t for fill in hypothesis.fills))
            for hypothesis in self.table_readings(t)
        ]
        return self.context_builder.build(self.chronicle, TABLE, t, supporting)

    def describe(self, schema: str, binding: Mapping[str, int | None]) -> str:
        roles = ", ".join(
            f"{role} = {self.names[entity]}" for role, entity in binding.items() if entity is not None
        )
        name = self.schema_names.get(schema, schema)
        return f"a {name} with {roles}" if roles else f"a {name}"

    @staticmethod
    def assumption(description: str) -> str:
        return f"Suppose the story is {description}."


def labels(count: int) -> Sequence[str]:
    return [chr(ord("A") + index) for index in range(count)]
