"""Matching one beat against one beat pattern under a binding (concept §7).

Exact by design: predicates and entity ids are compared, never similarity. A match returns the
(possibly extended) binding as a new dict; no match returns None.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from matching.beats import PlainBeat
from schemas.patterns import ArgumentPattern, BeatPattern, Literal, RoleVariable, StepReference, Wildcard

type Binding = Mapping[str, int | None]


@dataclass(frozen=True)
class MatchContext:
    role_kinds: Mapping[str, str]  # schema role -> entity kind
    entity_kinds: Mapping[int, str]  # entity id -> entity kind
    fills: Mapping[str, Sequence[int]] = field(default_factory=dict)  # step id -> t of the beats filling it


def match(
    pattern: BeatPattern, beat: PlainBeat, binding: Binding, context: MatchContext
) -> dict[str, int | None] | None:
    if beat.is_quarantined or beat.pred != pattern.pred:
        return None
    if not tags_fit(pattern, beat.tags):
        return None
    return match_args(pattern.args, beat.args, dict(binding), context)


def tags_fit(pattern: BeatPattern, tags: Sequence[str]) -> bool:
    if pattern.tags_any and not set(pattern.tags_any) & set(tags):
        return False
    return set(pattern.tags_all) <= set(tags)


def match_args(
    pattern_args: Mapping[str, ArgumentPattern],
    beat_args: Mapping[str, Any],
    binding: dict[str, int | None],
    context: MatchContext,
) -> dict[str, int | None] | None:
    for role, expected in pattern_args.items():
        if isinstance(expected, Wildcard):
            continue
        if role not in beat_args:
            return None
        matched = match_value(expected, beat_args[role], binding, context)
        if matched is None:
            return None
        binding = matched
    return binding


def match_value(
    expected: ArgumentPattern,
    actual: Mapping[str, Any],
    binding: dict[str, int | None],
    context: MatchContext,
) -> dict[str, int | None] | None:
    [(kind, content)] = actual.items()
    match expected:
        case Literal(value):
            return binding if kind == "literal" and content == value else None
        case RoleVariable(role):
            return bind_role(role, kind, content, binding, context)
        case StepReference(step_id):
            return binding if kind == "beat" and content in context.fills.get(step_id, ()) else None
        case BeatPattern():
            if kind != "prop" or content["pred"] != expected.pred:
                return None
            return match_args(expected.args, content["args"], binding, context)
        case Wildcard():
            return binding


def bind_role(
    role: str, kind: str, entity_id: Any, binding: dict[str, int | None], context: MatchContext
) -> dict[str, int | None] | None:
    if kind != "entity":
        return None
    bound = binding.get(role)
    if bound is not None:
        return binding if bound == entity_id else None
    if context.entity_kinds.get(entity_id) != context.role_kinds.get(role):
        return None
    return {**binding, role: entity_id}
