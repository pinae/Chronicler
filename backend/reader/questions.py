"""Readout questions (concept §8.3, M6): for a live hypothesis and its next open step, a deterministic
multiple-choice question about which entity will fill the step's open role."""

import string
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from string import Formatter
from typing import Protocol

from chronicle.beat_args import referenced_entity_ids
from chronicle.models import Chronicle, Entity, Player
from reader.interfaces import Candidate, Question
from reader.templates import PERSON_ROLES, PREDICATE_TEMPLATES
from schemas.definitions import SchemaDefinition, StepDefinition
from schemas.patterns import ArgumentPattern, BeatPattern, Literal, RoleVariable, StepReference

BLANK = "___"
NOTHING_YET = "nothing like this yet"
IT_HAPPENS = "this happens next"
DEFAULT_MAX_CANDIDATES = 20


class AskableHypothesis(Protocol):
    @property
    def schema(self) -> SchemaDefinition: ...

    @property
    def binding(self) -> Mapping[str, int | None]: ...

    def fill_ts(self, step_id: str) -> list[int]: ...


@dataclass(frozen=True)
class EntityInView:
    id: int
    name: str
    kind: str
    introduced_at_t: int


def next_open_step(hypothesis: AskableHypothesis) -> StepDefinition | None:
    """The first unfilled required step, or once those are filled, the first unfilled optional one."""
    unfilled = [step for step in hypothesis.schema.steps if not hypothesis.fill_ts(step.step_id)]
    required = [step for step in unfilled if step.required]
    candidates = required or unfilled
    return candidates[0] if candidates else None


def build_questions(
    hypothesis: AskableHypothesis,
    t: int,
    entities: Iterable[EntityInView],
    step_texts: Mapping[int, str],
    max_candidates: int = DEFAULT_MAX_CANDIDATES,
) -> list[Question]:
    """One question per page of at most `max_candidates` labels (the last always "nothing yet")."""
    step = next_open_step(hypothesis)
    if step is None:
        return []
    pattern = step.patterns[0]
    open_role = first_open_role(pattern, hypothesis)
    known = sorted(
        (entity for entity in entities if entity.introduced_at_t <= t),
        key=lambda e: (e.introduced_at_t, e.id),
    )
    phrasing = Phrasing(hypothesis, {entity.id: entity.name for entity in known}, step_texts, open_role)
    text = f"Next: {phrasing.statement(pattern)}."
    if open_role is None:
        return [Question(t=t, text=text, candidates=labelled([(IT_HAPPENS, {})]))]
    options = [
        (entity.name, {open_role: entity.id})
        for entity in known
        if entity.kind == hypothesis.schema.roles[open_role]
    ]
    if not options:
        return []
    page_size = max_candidates - 1
    pages = [options[start : start + page_size] for start in range(0, len(options), page_size)]
    return [Question(t=t, text=text, candidates=labelled(page)) for page in pages]


def labelled(options: Sequence[tuple[str, Mapping[str, int]]]) -> tuple[Candidate, ...]:
    with_nothing_yet = [*options, (NOTHING_YET, None)]
    return tuple(
        Candidate(label=string.ascii_uppercase[index], text=text, binding_delta=delta)
        for index, (text, delta) in enumerate(with_nothing_yet)
    )


def first_open_role(pattern: BeatPattern, hypothesis: AskableHypothesis) -> str | None:
    variables = set(role_variables(pattern))
    return next(
        (
            role
            for role in hypothesis.schema.roles
            if role in variables and hypothesis.binding.get(role) is None
        ),
        None,
    )


def role_variables(pattern: BeatPattern) -> Iterable[str]:
    if pattern.claimed_by:
        yield pattern.claimed_by.name
    for value in pattern.args.values():
        if isinstance(value, RoleVariable):
            yield value.name
        elif isinstance(value, BeatPattern):
            yield from role_variables(value)


class Phrasing:
    """Turns a beat pattern into a plain sentence under a hypothesis' binding."""

    def __init__(
        self,
        hypothesis: AskableHypothesis,
        names: Mapping[int, str],
        step_texts: Mapping[int, str],
        open_role: str | None,
    ) -> None:
        self.hypothesis = hypothesis
        self.names = names
        self.step_texts = step_texts
        self.open_role = open_role

    def statement(self, pattern: BeatPattern) -> str:
        template = PREDICATE_TEMPLATES[pattern.pred]
        template_roles = [field for _, field, _, _ in Formatter().parse(template) if field]
        words = {role: self.value(role, pattern.args.get(role)) for role in template_roles}
        extras = [
            f"({role}: {self.value(role, value)})"
            for role, value in pattern.args.items()
            if role not in template_roles
        ]
        return " ".join([template.format(**words), *extras])

    def value(self, role: str, value: ArgumentPattern | None) -> str:
        match value:
            case RoleVariable(name) if self.hypothesis.binding.get(name) is not None:
                entity_id = self.hypothesis.binding[name]
                return self.names.get(entity_id, f"entity {entity_id}") if entity_id is not None else BLANK
            case RoleVariable(name) if name == self.open_role:
                return BLANK
            case Literal(scalar):
                return str(scalar)
            case StepReference(step_id):
                fill_ts = self.hypothesis.fill_ts(step_id)
                return (
                    self.step_texts.get(fill_ts[0], f"the event at t={fill_ts[0]}")
                    if fill_ts
                    else "that event"
                )
            case BeatPattern():
                return self.statement(value)
            case _:
                return "someone" if role in PERSON_ROLES else "something"


def entities_in_view(chronicle: Chronicle, player: Player | None, t: int) -> list[EntityInView]:
    """Entities mentioned in the beats the audience (one player, or the table) had seen by t."""
    mentioned: set[int] = set()
    for args in chronicle.visible_to(player, t).values_list("args", flat=True):
        mentioned |= referenced_entity_ids(args)
    entities = Entity.objects.filter(chronicle=chronicle, pk__in=mentioned).order_by("introduced_at_t", "pk")
    return [
        EntityInView(
            id=entity.pk, name=entity.canonical_name, kind=entity.kind, introduced_at_t=entity.introduced_at_t
        )
        for entity in entities
    ]
