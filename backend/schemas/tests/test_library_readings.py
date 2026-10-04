"""Each schema of the library reads the plot it is named for, on a few plain beats."""

import pytest
import yaml

from matching.beats import PlainBeat
from matching.engine import COMPLETE, LIVE, IncrementalMatcher, World
from schemas.definitions import parse_schema
from schemas.library import LIBRARY_DIR

KING, THANE, LORD, WITCH, CROWN = 1, 2, 3, 4, 5
CHARACTERS = {KING: "character", THANE: "character", LORD: "character", WITCH: "character"}
WORLD = World(entity_kinds={**CHARACTERS, CROWN: "object"})


def library_schema(slug):
    path = LIBRARY_DIR / f"{slug}.yaml"
    return parse_schema(yaml.safe_load(path.read_text()), source=path.name)


def entity(entity_id):
    return {"entity": entity_id}


def proposition(pred, **args):
    return {"prop": {"pred": pred, "args": args}}


def beat(t, pred, **args):
    return PlainBeat(t=t, pred=pred, args=args)


def run(slug, *beats):
    matcher = IncrementalMatcher([library_schema(slug)])
    for each in beats:
        matcher.step(each, WORLD)
    return matcher


def reading(matcher, **binding):
    [hypothesis] = [
        hypothesis
        for hypothesis in matcher.hypotheses
        if all(hypothesis.binding[role] == entity_id for role, entity_id in binding.items())
    ]
    return hypothesis


def test_a_betrayer_who_kills_the_victim_has_done_the_harm():
    matcher = run(
        "betrayal",
        beat(1, "trusts", who=entity(KING), whom=entity(THANE)),
        beat(2, "kills", who=entity(THANE), whom=entity(KING)),
    )

    assert reading(matcher, T=THANE, V=KING).fill_ts("harm") == [2]


def test_a_hidden_crime_is_seeded_by_the_crime_and_completed_when_someone_learns_of_it():
    matcher = run(
        "hidden_crime",
        beat(1, "kills", who=entity(THANE), whom=entity(KING)),
        beat(2, "says", who=entity(THANE), what=proposition("kills", who=entity(WITCH), whom=entity(KING))),
        beat(3, "learns", who=entity(LORD), what={"beat": 1}),
    )

    solved = reading(matcher, C=THANE, V=KING, I=LORD)
    assert solved.fills_by_step() == {"crime": [1], "suspicion": [], "cover_up": [2], "discovery": [3]}
    assert solved.status == COMPLETE


def test_suspicion_alone_starts_a_hidden_crime_whose_victim_is_still_open():
    matcher = run("hidden_crime", beat(1, "distrusts", who=entity(LORD), whom=entity(THANE)))

    suspected = reading(matcher, C=THANE, I=LORD)
    assert (suspected.binding["V"], suspected.status) == (None, LIVE)


def test_growing_suspicion_strengthens_one_reading_instead_of_starting_another():
    thane_was_there = proposition("is_at", who=entity(THANE), where="the chamber")
    matcher = run(
        "hidden_crime",
        beat(1, "distrusts", who=entity(LORD), whom=entity(THANE)),
        beat(2, "learns", who=entity(LORD), what=thane_was_there),
    )

    [suspected] = matcher.live()
    assert suspected.fill_ts("suspicion") == [1, 2]


def test_a_usurper_who_kills_the_ruler_and_takes_the_crown_completes_a_usurpation():
    matcher = run(
        "usurpation",
        beat(1, "gives", who=entity(KING), what="a title", to=entity(THANE)),
        beat(2, "has", who=entity(KING), what=entity(CROWN)),
        beat(3, "wants", who=entity(THANE), what=entity(CROWN)),
        beat(4, "kills", who=entity(THANE), whom=entity(KING)),
        beat(5, "has", who=entity(THANE), what=entity(CROWN)),
    )

    assert reading(matcher, U=THANE, R=KING, P=CROWN).status == COMPLETE


@pytest.mark.parametrize(
    "fulfilment",
    [
        beat(3, "has", who=entity(THANE), what=entity(CROWN)),
        beat(3, "gives", who=entity(KING), what=entity(CROWN), to=entity(THANE)),
    ],
    ids=["taken", "given"],
)
def test_a_prophecy_is_fulfilled_when_the_foretold_thing_is_taken_or_given(fulfilment):
    matcher = run(
        "prophecy",
        beat(1, "says", who=entity(WITCH), what=proposition("has", who=entity(THANE), what=entity(CROWN))),
        beat(2, "wants", who=entity(THANE), what=entity(CROWN)),
        fulfilment,
    )

    fulfilled = reading(matcher, S=WITCH, H=THANE, X=CROWN)
    assert fulfilled.fills_by_step() == {"foretelling": [1], "temptation": [2], "fulfilment": [3]}
    assert fulfilled.status == COMPLETE
