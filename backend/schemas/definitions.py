"""Schema definitions (concept §6): parsed, validated and serializable back to their YAML shape."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from chronicle.models import EntityKind
from schemas.constraints import Constraint, parse_constraint
from schemas.patterns import BeatPattern, PatternParser, SchemaDefinitionError
from schemas.vocabulary import Vocabulary, default_vocabulary

__all__ = ["SchemaDefinition", "SchemaDefinitionError", "StepDefinition", "parse_schema"]

PHASES = ("setup", "development", "payoff")
REQUIRED_SCHEMA_KEYS = ("slug", "name", "roles", "steps")
REQUIRED_STEP_KEYS = ("step_id", "phase", "patterns")


@dataclass(frozen=True)
class StepDefinition:
    step_id: str
    order: int
    phase: str
    patterns: tuple[BeatPattern, ...]
    required: bool = True
    repeatable: bool = False
    weight: float = 1.0
    contradicts: tuple[BeatPattern, ...] = ()
    trigger: bool = False

    def to_document(self) -> dict[str, Any]:
        document: dict[str, Any] = {"step_id": self.step_id, "phase": self.phase}
        if self.trigger:
            document["trigger"] = True
        document["patterns"] = [pattern.to_document() for pattern in self.patterns]
        if not self.required:
            document["required"] = False
        if self.repeatable:
            document["repeatable"] = True
        document["weight"] = self.weight
        if self.contradicts:
            document["contradicts"] = [pattern.to_document() for pattern in self.contradicts]
        return document


@dataclass(frozen=True)
class SchemaDefinition:
    slug: str
    name: str
    roles: Mapping[str, str]
    steps: tuple[StepDefinition, ...]
    prior: float = 0.0
    payoff_steps: tuple[str, ...] = ()
    constraints: tuple[Constraint, ...] = ()
    origin: str = "library"

    def step(self, step_id: str) -> StepDefinition:
        return next(step for step in self.steps if step.step_id == step_id)

    def in_role_order(self, binding: Mapping[str, int | None]) -> dict[str, int | None]:
        """The binding with its roles in the schema's order, whatever order it was stored in."""
        return {role: binding.get(role) for role in self.roles}

    def to_document(self) -> dict[str, Any]:
        document: dict[str, Any] = {
            "slug": self.slug,
            "name": self.name,
            "roles": dict(self.roles),
            "prior": self.prior,
            "payoff_steps": list(self.payoff_steps),
            "constraints": [constraint.to_document() for constraint in self.constraints],
            "steps": [step.to_document() for step in self.steps],
        }
        if self.origin != "library":
            document["origin"] = self.origin
        return document


def parse_schema(
    document: Mapping[str, Any], source: str, vocabulary: Vocabulary | None = None
) -> SchemaDefinition:
    """Parse a schema document; every problem is reported as `<source>: <what is wrong>`."""
    try:
        return SchemaParser(document, vocabulary or default_vocabulary()).parse()
    except SchemaDefinitionError as error:
        raise SchemaDefinitionError(f"{source}: {error}") from None


class SchemaParser:
    def __init__(self, document: Mapping[str, Any], vocabulary: Vocabulary) -> None:
        self.document = document
        self.vocabulary = vocabulary

    def parse(self) -> SchemaDefinition:
        require_keys(self.document, REQUIRED_SCHEMA_KEYS)
        roles = self.parse_roles()
        step_documents = self.document["steps"] or []
        step_ids = self.parse_step_ids(step_documents, roles)
        patterns = PatternParser(set(roles), set(step_ids), self.vocabulary)
        steps = tuple(
            self.parse_step(order, step_document, patterns)
            for order, step_document in enumerate(step_documents, start=1)
        )
        return SchemaDefinition(
            slug=self.document["slug"],
            name=self.document["name"],
            roles=roles,
            steps=steps,
            prior=float(self.document.get("prior", 0.0)),
            payoff_steps=self.parse_payoff_steps(step_ids),
            constraints=self.parse_constraints(roles, step_ids),
            origin=self.document.get("origin", "library"),
        )

    def parse_roles(self) -> dict[str, str]:
        roles = dict(self.document["roles"])
        for role, kind in roles.items():
            if kind not in EntityKind.values:
                raise SchemaDefinitionError(f"role '{role}' has kind '{kind}', which is not an entity kind")
        return roles

    def parse_step_ids(self, step_documents: list[Mapping[str, Any]], roles: Mapping[str, str]) -> list[str]:
        step_ids: list[str] = []
        for step_document in step_documents:
            require_keys(step_document, REQUIRED_STEP_KEYS)
            step_id = step_document["step_id"]
            if step_id in step_ids:
                raise SchemaDefinitionError(f"step '{step_id}' is defined twice")
            if step_id in roles:
                raise SchemaDefinitionError(f"'{step_id}' is both a role and a step")
            step_ids.append(step_id)
        return step_ids

    def parse_step(self, order: int, document: Mapping[str, Any], patterns: PatternParser) -> StepDefinition:
        step_id = document["step_id"]
        if document["phase"] not in PHASES:
            raise SchemaDefinitionError(f"step '{step_id}' has unknown phase '{document['phase']}'")
        if not document["patterns"]:
            raise SchemaDefinitionError(f"step '{step_id}' needs at least one pattern")
        return StepDefinition(
            step_id=step_id,
            order=order,
            phase=document["phase"],
            patterns=tuple(
                patterns.parse(pattern, f"step '{step_id}', pattern {number}")
                for number, pattern in enumerate(document["patterns"], start=1)
            ),
            required=bool(document.get("required", True)),
            repeatable=bool(document.get("repeatable", False)),
            weight=float(document.get("weight", 1.0)),
            contradicts=tuple(
                patterns.parse(pattern, f"step '{step_id}', contradicts {number}")
                for number, pattern in enumerate(document.get("contradicts") or [], start=1)
            ),
            trigger=bool(document.get("trigger", False)),
        )

    def parse_constraints(self, roles: Mapping[str, str], step_ids: list[str]) -> tuple[Constraint, ...]:
        return tuple(
            parse_constraint(document, roles.keys(), step_ids, location=f"constraint {number}")
            for number, document in enumerate(self.document.get("constraints") or [], start=1)
        )

    def parse_payoff_steps(self, step_ids: list[str]) -> tuple[str, ...]:
        payoff_steps = tuple(self.document.get("payoff_steps") or ())
        for step_id in payoff_steps:
            if step_id not in step_ids:
                raise SchemaDefinitionError(f"payoff step '{step_id}' is not a step")
        return payoff_steps


def require_keys(document: object, keys: tuple[str, ...]) -> None:
    if not isinstance(document, Mapping):
        raise SchemaDefinitionError(f"expected a mapping, got {document!r}")
    for key in keys:
        if key not in document:
            raise SchemaDefinitionError(f"missing key '{key}'")
