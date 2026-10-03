"""Beat patterns (concept §6.1): the slots of schema steps that beats can fill."""

from collections.abc import Mapping, Set
from dataclasses import dataclass, field
from typing import Any

from schemas.vocabulary import UnknownPredicate, ValueKind, Vocabulary

WILDCARD = "*"
VARIABLE_PREFIX = "$"
PATTERN_KEYS = {"pred", "args", "tags_any", "tags_all", "scope", "claimed_by"}

type Scalar = str | int | float | bool


class SchemaDefinitionError(ValueError):
    pass


@dataclass(frozen=True)
class RoleVariable:
    """`$T`: equal to the role's bound entity, or binds it."""

    name: str


@dataclass(frozen=True)
class StepReference:
    """`$harm`: the beat that filled another step of the same hypothesis."""

    step_id: str


@dataclass(frozen=True)
class Wildcard:
    """`"*"`: matches anything."""


@dataclass(frozen=True)
class Literal:
    value: Scalar


@dataclass(frozen=True)
class BeatPattern:
    pred: str
    args: Mapping[str, "ArgumentPattern"] = field(default_factory=dict)
    tags_any: tuple[str, ...] = ()
    tags_all: tuple[str, ...] = ()
    players_know: bool = False
    claimed_by: RoleVariable | None = None

    def to_document(self) -> dict[str, Any]:
        document: dict[str, Any] = {"pred": self.pred}
        if self.args:
            document["args"] = {role: argument_to_document(value) for role, value in self.args.items()}
        if self.tags_any:
            document["tags_any"] = list(self.tags_any)
        if self.tags_all:
            document["tags_all"] = list(self.tags_all)
        if self.players_know:
            document["scope"] = {"players_know": True}
        if self.claimed_by:
            document["claimed_by"] = VARIABLE_PREFIX + self.claimed_by.name
        return document


type ArgumentPattern = RoleVariable | StepReference | Wildcard | Literal | BeatPattern


def argument_to_document(value: ArgumentPattern) -> Any:
    match value:
        case RoleVariable(name):
            return VARIABLE_PREFIX + name
        case StepReference(step_id):
            return VARIABLE_PREFIX + step_id
        case Wildcard():
            return WILDCARD
        case Literal(scalar):
            return scalar
        case BeatPattern():
            return value.to_document()


def required_kind(value: ArgumentPattern) -> ValueKind | None:
    """The kind of beat argument a pattern value can match; None for the wildcard."""
    match value:
        case RoleVariable():
            return ValueKind.ENTITY
        case StepReference():
            return ValueKind.BEAT
        case Literal():
            return ValueKind.LITERAL
        case BeatPattern():
            return ValueKind.PROP
        case Wildcard():
            return None


class PatternParser:
    """Parses pattern documents of one schema, checking them against its roles, steps and the vocabulary."""

    def __init__(self, role_names: Set[str], step_ids: Set[str], vocabulary: Vocabulary) -> None:
        self.role_names = role_names
        self.step_ids = step_ids
        self.vocabulary = vocabulary

    def parse(self, document: object, location: str) -> BeatPattern:
        try:
            return self._parse_pattern(document)
        except SchemaDefinitionError as error:
            raise SchemaDefinitionError(f"{location}: {error}") from None

    def _parse_pattern(self, document: object) -> BeatPattern:
        if not isinstance(document, Mapping) or "pred" not in document:
            raise SchemaDefinitionError(f"a pattern is a mapping with 'pred', got {document!r}")
        unknown_keys = sorted(document.keys() - PATTERN_KEYS)
        if unknown_keys:
            raise SchemaDefinitionError(f"unknown key '{unknown_keys[0]}' in pattern")
        pred = document["pred"]
        try:
            predicate = self.vocabulary.predicate(pred)
        except UnknownPredicate as error:
            raise SchemaDefinitionError(str(error)) from None
        args = {role: self._parse_argument(value) for role, value in (document.get("args") or {}).items()}
        for role_name, value in args.items():
            if role_name not in predicate.roles:
                raise SchemaDefinitionError(f"{pred} has no role '{role_name}'")
            kind = required_kind(value)
            accepted = predicate.role(role_name).kinds
            if kind is not None and kind not in accepted:
                raise SchemaDefinitionError(
                    f"{pred}: role '{role_name}' accepts {', '.join(sorted(accepted))}, not {kind}"
                )
        return BeatPattern(
            pred=pred,
            args=args,
            tags_any=tuple(document.get("tags_any", ())),
            tags_all=tuple(document.get("tags_all", ())),
            players_know=bool((document.get("scope") or {}).get("players_know", False)),
            claimed_by=self._parse_claimed_by(document.get("claimed_by")),
        )

    def _parse_argument(self, value: object) -> ArgumentPattern:
        if value == WILDCARD:
            return Wildcard()
        if isinstance(value, str) and value.startswith(VARIABLE_PREFIX):
            return self._parse_variable(value.removeprefix(VARIABLE_PREFIX))
        if isinstance(value, Mapping):
            return self._parse_pattern(value)
        if isinstance(value, str | int | float | bool):
            return Literal(value)
        raise SchemaDefinitionError(f"cannot read pattern value {value!r}")

    def _parse_variable(self, name: str) -> RoleVariable | StepReference:
        if name in self.role_names:
            return RoleVariable(name)
        if name in self.step_ids:
            return StepReference(name)
        raise SchemaDefinitionError(f"'{VARIABLE_PREFIX}{name}' is neither a role nor a step")

    def _parse_claimed_by(self, value: object) -> RoleVariable | None:
        if value is None:
            return None
        variable = self._parse_argument(value)
        if not isinstance(variable, RoleVariable):
            raise SchemaDefinitionError(
                f"claimed_by must name a role variable such as $Source, got {value!r}"
            )
        return variable
