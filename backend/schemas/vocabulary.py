"""The closed predicate vocabulary (concept §5) and validation of beat arguments (§4.1)."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from functools import cache
from pathlib import Path
from typing import Any

import yaml

DEFAULT_VOCABULARY_PATH = Path(__file__).with_name("vocabulary.yaml")
OPTIONAL_MARKER = "?"


class ValueKind(StrEnum):
    ENTITY = "entity"
    LITERAL = "literal"
    BEAT = "beat"
    PROP = "prop"


class VocabularyError(Exception):
    """The vocabulary file itself is malformed."""


class BeatArgsError(ValueError):
    """Beat arguments do not fit the vocabulary."""


class UnknownPredicate(BeatArgsError):
    def __init__(self, predicate: str) -> None:
        super().__init__(f"unknown predicate '{predicate}'")
        self.predicate = predicate


class InvalidBeatArgs(BeatArgsError):
    pass


@dataclass(frozen=True)
class Role:
    name: str
    kinds: frozenset[ValueKind]
    optional: bool


@dataclass(frozen=True)
class Predicate:
    name: str
    roles: Mapping[str, Role]

    def role(self, name: str) -> Role:
        return self.roles[name]

    @property
    def required_role_names(self) -> set[str]:
        return {role.name for role in self.roles.values() if not role.optional}


class Vocabulary:
    def __init__(self, predicates: Mapping[str, Predicate]) -> None:
        self._predicates = dict(predicates)

    @property
    def predicate_names(self) -> list[str]:
        return list(self._predicates)

    def __contains__(self, predicate_name: object) -> bool:
        return predicate_name in self._predicates

    def predicate(self, name: str) -> Predicate:
        try:
            return self._predicates[name]
        except KeyError:
            raise UnknownPredicate(name) from None

    def validate_args(self, predicate_name: str, args: object) -> None:
        """Raise UnknownPredicate or InvalidBeatArgs unless `args` fit the predicate, recursively."""
        predicate = self.predicate(predicate_name)
        if not isinstance(args, Mapping):
            raise InvalidBeatArgs(f"{predicate_name}: arguments must be a mapping of role to value")
        unknown_roles = sorted(args.keys() - predicate.roles.keys())
        if unknown_roles:
            raise InvalidBeatArgs(f"{predicate_name}: unknown role '{unknown_roles[0]}'")
        missing_roles = sorted(predicate.required_role_names - args.keys())
        if missing_roles:
            raise InvalidBeatArgs(f"{predicate_name}: missing role '{missing_roles[0]}'")
        for role_name, value in args.items():
            self._validate_value(predicate.role(role_name), predicate_name, value)

    def _validate_value(self, role: Role, predicate_name: str, value: object) -> None:
        where = f"{predicate_name}: role '{role.name}'"
        kind, content = split_value(value, where)
        if kind not in role.kinds:
            allowed = ", ".join(sorted(role.kinds))
            raise InvalidBeatArgs(f"{where} accepts {allowed}, not {kind}")
        if kind is ValueKind.PROP:
            self.validate_args(content["pred"], content["args"])


def split_value(value: object, where: str) -> tuple[ValueKind, Any]:
    """Return the kind and content of a `{kind: content}` argument value, checking its shape."""
    if not (isinstance(value, Mapping) and len(value) == 1):
        raise InvalidBeatArgs(f"{where}: a value is one of {{entity|literal|beat|prop: ...}}, got {value!r}")
    [(key, content)] = value.items()
    try:
        kind = ValueKind(key)
    except ValueError:
        raise InvalidBeatArgs(f"{where}: unknown value kind '{key}'") from None
    if not CONTENT_IS_WELL_FORMED[kind](content):
        raise InvalidBeatArgs(f"{where}: malformed {kind} value {content!r}")
    return kind, content


def is_id(content: object) -> bool:
    return isinstance(content, int) and not isinstance(content, bool)


def is_plain_literal(content: object) -> bool:
    return isinstance(content, str | int | float | bool)


def is_proposition(content: object) -> bool:
    return isinstance(content, Mapping) and isinstance(content.get("pred"), str) and "args" in content


CONTENT_IS_WELL_FORMED = {
    ValueKind.ENTITY: is_id,
    ValueKind.BEAT: is_id,
    ValueKind.LITERAL: is_plain_literal,
    ValueKind.PROP: is_proposition,
}


def load_vocabulary(path: Path) -> Vocabulary:
    document = yaml.safe_load(path.read_text())
    predicates = {
        name: parse_predicate(name, roles) for name, roles in (document.get("predicates") or {}).items()
    }
    return Vocabulary(predicates)


def parse_predicate(name: str, roles: object) -> Predicate:
    if not isinstance(roles, Mapping) or not roles:
        raise VocabularyError(f"predicate '{name}' must declare at least one role")
    parsed = [parse_role(name, role_key, kinds) for role_key, kinds in roles.items()]
    return Predicate(name=name, roles={role.name: role for role in parsed})


def parse_role(predicate_name: str, role_key: str, kinds: object) -> Role:
    role_name = role_key.removesuffix(OPTIONAL_MARKER)
    if not isinstance(kinds, list) or not kinds:
        raise VocabularyError(f"predicate '{predicate_name}': role '{role_name}' must list its value kinds")
    try:
        parsed_kinds = frozenset(ValueKind(kind) for kind in kinds)
    except ValueError as error:
        raise VocabularyError(f"predicate '{predicate_name}': role '{role_name}': {error}") from None
    return Role(name=role_name, kinds=parsed_kinds, optional=role_key.endswith(OPTIONAL_MARKER))


@cache
def default_vocabulary() -> Vocabulary:
    return load_vocabulary(DEFAULT_VOCABULARY_PATH)
