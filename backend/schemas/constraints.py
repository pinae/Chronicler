"""Schema constraints (concept §6.2), typed and checkable against a partial hypothesis at time t.

Constraints read the chronicle through `ChronicleFacts`, so they can be checked against plain data.
A constraint that refers to an unbound role or a step not filled by time t is not (yet) violated.
"""

import json
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from schemas.patterns import SchemaDefinitionError


class HypothesisLike(Protocol):
    @property
    def binding(self) -> Mapping[str, int | None]: ...

    def fill_ts(self, step_id: str) -> Sequence[int]: ...


class ChronicleFacts(Protocol):
    def first_known_at(self, character_id: int, beat_t: int) -> int | None:
        """The t from which the character knew the beat at `beat_t`, or None if never."""
        ...

    def location_at(self, entity_id: int, t: int) -> Mapping[str, Any] | None:
        """The `where` argument of the entity's latest `is_at` beat up to t."""
        ...


def first_fill_t(hypothesis: HypothesisLike, step_id: str, t: int) -> int | None:
    fills_so_far = [fill_t for fill_t in hypothesis.fill_ts(step_id) if fill_t <= t]
    return min(fills_so_far) if fills_so_far else None


@dataclass(frozen=True)
class Distinct:
    roles: tuple[str, ...]

    def check(self, hypothesis: HypothesisLike, facts: ChronicleFacts, t: int) -> bool:
        bound = [hypothesis.binding.get(role) for role in self.roles]
        entities = [entity for entity in bound if entity is not None]
        return len(entities) == len(set(entities))

    def to_document(self) -> dict[str, Any]:
        return {"type": "distinct", "roles": list(self.roles)}


@dataclass(frozen=True)
class Before:
    steps: tuple[str, str]

    def check(self, hypothesis: HypothesisLike, facts: ChronicleFacts, t: int) -> bool:
        first, second = (first_fill_t(hypothesis, step, t) for step in self.steps)
        return first is None or second is None or first < second

    def to_document(self) -> dict[str, Any]:
        return {"type": "before", "steps": list(self.steps)}


@dataclass(frozen=True)
class After:
    steps: tuple[str, str]

    def check(self, hypothesis: HypothesisLike, facts: ChronicleFacts, t: int) -> bool:
        first, second = (first_fill_t(hypothesis, step, t) for step in self.steps)
        return first is None or second is None or first > second

    def to_document(self) -> dict[str, Any]:
        return {"type": "after", "steps": list(self.steps)}


@dataclass(frozen=True)
class Knows:
    """The character knew the step's beat when it filled the step."""

    role: str
    step: str

    def check(self, hypothesis: HypothesisLike, facts: ChronicleFacts, t: int) -> bool:
        character = hypothesis.binding.get(self.role)
        fill_t = first_fill_t(hypothesis, self.step, t)
        if character is None or fill_t is None:
            return True
        known_from = facts.first_known_at(character, fill_t)
        return known_from is not None and known_from <= fill_t

    def to_document(self) -> dict[str, Any]:
        return {"type": "knows", "role": self.role, "step": self.step}


@dataclass(frozen=True)
class NotKnows:
    """The character does not know the step's beat before the `until` step is filled (or ever)."""

    role: str
    step: str
    until: str | None = None

    def check(self, hypothesis: HypothesisLike, facts: ChronicleFacts, t: int) -> bool:
        character = hypothesis.binding.get(self.role)
        fill_t = first_fill_t(hypothesis, self.step, t)
        if character is None or fill_t is None:
            return True
        known_from = facts.first_known_at(character, fill_t)
        if known_from is None or known_from > t:
            return True
        until_t = first_fill_t(hypothesis, self.until, t) if self.until else None
        return until_t is not None and known_from >= until_t

    def to_document(self) -> dict[str, Any]:
        document = {"type": "not_knows", "role": self.role, "step": self.step}
        if self.until:
            document["until"] = self.until
        return document


@dataclass(frozen=True)
class SamePlace:
    """The roles' entities are at the same place when the step was filled (without a step: at t)."""

    roles: tuple[str, ...]
    step: str | None = None

    def check(self, hypothesis: HypothesisLike, facts: ChronicleFacts, t: int) -> bool:
        at_t = first_fill_t(hypothesis, self.step, t) if self.step else t
        if at_t is None:
            return True
        entities = [hypothesis.binding.get(role) for role in self.roles]
        places = [facts.location_at(entity, at_t) for entity in entities if entity is not None]
        known_places = {json.dumps(place, sort_keys=True) for place in places if place is not None}
        return len(known_places) <= 1

    def to_document(self) -> dict[str, Any]:
        document: dict[str, Any] = {"type": "same_place", "roles": list(self.roles)}
        if self.step:
            document["step"] = self.step
        return document


type Constraint = Distinct | Before | After | Knows | NotKnows | SamePlace


def parse_constraint(
    document: Mapping[str, Any],
    role_names: Collection[str],
    step_ids: Collection[str],
    location: str = "constraint",
) -> Constraint:
    constraint_type = document.get("type")
    parse = CONSTRAINT_PARSERS.get(str(constraint_type))
    if parse is None:
        raise SchemaDefinitionError(f"{location}: unknown type '{constraint_type}'")
    try:
        return parse(ConstraintFields(document, role_names, step_ids))
    except SchemaDefinitionError as error:
        raise SchemaDefinitionError(f"{location} ({constraint_type}): {error}") from None


class ConstraintFields:
    """Reads and checks the fields of one constraint document."""

    def __init__(
        self, document: Mapping[str, Any], role_names: Collection[str], step_ids: Collection[str]
    ) -> None:
        self.document = document
        self.role_names = role_names
        self.step_ids = step_ids

    def required(self, key: str) -> Any:
        if key not in self.document:
            raise SchemaDefinitionError(f"missing key '{key}'")
        return self.document[key]

    def role(self, key: str = "role") -> str:
        return self.check_role(self.required(key))

    def roles(self) -> tuple[str, ...]:
        return tuple(self.check_role(role) for role in self.required("roles"))

    def step(self, key: str = "step") -> str:
        return self.check_step(self.required(key))

    def optional_step(self, key: str) -> str | None:
        return self.check_step(self.document[key]) if key in self.document else None

    def step_pair(self) -> tuple[str, str]:
        steps = self.required("steps")
        if len(steps) != 2:
            raise SchemaDefinitionError("needs exactly two steps")
        return self.check_step(steps[0]), self.check_step(steps[1])

    def check_role(self, role: str) -> str:
        if role not in self.role_names:
            raise SchemaDefinitionError(f"'{role}' is not a role")
        return role

    def check_step(self, step_id: str) -> str:
        if step_id not in self.step_ids:
            raise SchemaDefinitionError(f"'{step_id}' is not a step")
        return step_id


CONSTRAINT_PARSERS: dict[str, Callable[[ConstraintFields], Constraint]] = {
    "distinct": lambda fields: Distinct(roles=fields.roles()),
    "before": lambda fields: Before(steps=fields.step_pair()),
    "after": lambda fields: After(steps=fields.step_pair()),
    "knows": lambda fields: Knows(role=fields.role(), step=fields.step()),
    "not_knows": lambda fields: NotKnows(
        role=fields.role(), step=fields.step(), until=fields.optional_step("until")
    ),
    "same_place": lambda fields: SamePlace(roles=fields.roles(), step=fields.optional_step("step")),
}
