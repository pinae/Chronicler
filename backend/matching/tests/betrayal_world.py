"""Shared plain-data setting for matcher tests: the betrayal schema and a small cast."""

import yaml

from matching.beats import PlainBeat
from matching.engine import World
from schemas.definitions import parse_schema
from schemas.library import LIBRARY_DIR

MIRA, ALDRIC, RONAN, KEY, LETTER = 1, 2, 3, 4, 5
ENTITY_KINDS = {MIRA: "character", ALDRIC: "character", RONAN: "character", KEY: "secret", LETTER: "secret"}
WORLD = World(entity_kinds=ENTITY_KINDS)


def betrayal():
    return parse_schema(yaml.safe_load((LIBRARY_DIR / "betrayal.yaml").read_text()), source="betrayal.yaml")


def entity(entity_id):
    return {"entity": entity_id}


def beat(t, pred, **args):
    return PlainBeat(t=t, pred=pred, args=args)


def trusts(t, who, whom):
    return beat(t, "trusts", who=entity(who), whom=entity(whom))


def harms(t, who, whom):
    return beat(t, "harms", who=entity(who), whom=entity(whom))
