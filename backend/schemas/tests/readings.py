"""Helpers for running library schemas over a few plain beats."""

import yaml

from matching.beats import PlainBeat
from matching.engine import IncrementalMatcher, World
from schemas.definitions import SchemaDefinition, parse_schema
from schemas.library import LIBRARY_DIR


def library_schema(slug: str) -> SchemaDefinition:
    path = LIBRARY_DIR / f"{slug}.yaml"
    return parse_schema(yaml.safe_load(path.read_text()), source=path.name)


def entity(entity_id):
    return {"entity": entity_id}


def proposition(pred, **args):
    return {"prop": {"pred": pred, "args": args}}


def beat(t, pred, known_by_players=frozenset(), **args):
    return PlainBeat(t=t, pred=pred, args=args, known_by_players=frozenset(known_by_players))


def run(slug, *beats, world: World):
    matcher = IncrementalMatcher([library_schema(slug)])
    for each in beats:
        matcher.step(each, world)
    return matcher


def reading(matcher, **binding):
    """The one hypothesis binding these roles to these entities (other roles may be bound to anyone)."""
    [hypothesis] = [
        hypothesis
        for hypothesis in matcher.hypotheses
        if all(hypothesis.binding[role] == entity_id for role, entity_id in binding.items())
    ]
    return hypothesis
