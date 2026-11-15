"""The twist schemas (WP-074): each reads a beat that makes the audience reinterpret what came before."""

import pytest

from matching.engine import COMPLETE, LIVE, REFUTED, IncrementalMatcher, World
from matching.tests.betrayal_world import KnownFacts
from schemas.tests import readings
from schemas.tests.readings import beat, entity, library_schema, proposition, reading

(
    ELIZABETH, DARCY, WICKHAM, GRACE, TAYLOR, REBECCA, MAXIM, NARRATOR, SHEPPARD, ACKROYD, POIROT,
    PIP, HAVISHAM, MAGWITCH, HARRY, SNAPE, QUIRRELL, MACBETH, WITCHES, MACDUFF, LONNEGAN, GONDORFF,
    HOOKER,
) = range(1, 24)  # fmt: skip
ALIEN_PLANET, EARTH, HOME = 31, 32, 33
READER = 41

CHARACTERS = {character: "character" for character in range(1, 24)}
PLACES = {ALIEN_PLANET: "place", EARTH: "place", HOME: "place"}
WORLD = World(entity_kinds={**CHARACTERS, **PLACES}, players=frozenset({READER}), facts=KnownFacts())


def run(slug, *beats):
    return readings.run(slug, *beats, world=WORLD)


def statuses(matcher):
    return [hypothesis.status for hypothesis in matcher.hypotheses]


# revised_belief


@pytest.mark.parametrize(
    ("believer", "subject", "belief", "truth"),
    [
        (
            GRACE,
            GRACE,
            proposition("is", who=entity(GRACE), trait="alive"),
            proposition("is", who=entity(GRACE), trait="dead"),
        ),
        (
            TAYLOR,
            TAYLOR,
            proposition("is_at", who=entity(TAYLOR), where=entity(ALIEN_PLANET)),
            proposition("is_at", who=entity(TAYLOR), where=entity(EARTH)),
        ),
        (
            NARRATOR,
            MAXIM,
            proposition("wants", who=entity(MAXIM), what=entity(REBECCA)),
            proposition("wants", who=entity(MAXIM), what=entity(NARRATOR)),
        ),
    ],
    ids=["what someone is", "where someone is", "what someone wants"],
)
def test_a_belief_is_revised_when_the_believer_learns_the_truth(believer, subject, belief, truth):
    matcher = run(
        "revised_belief",
        beat(1, "believes", who=entity(believer), what=belief),
        beat(2, "learns", who=entity(believer), what=truth),
    )

    revised = reading(matcher, B=believer, X=subject)
    assert revised.fills_by_step() == {"belief": [1], "fact": [], "revelation": [2]}
    assert revised.status == COMPLETE


def test_a_belief_is_revised_by_learning_a_fact_that_came_after_it():
    matcher = run(
        "revised_belief",
        beat(1, "believes", who=entity(ELIZABETH), what=proposition("is", who=entity(DARCY), trait="cruel")),
        beat(2, "is", who=entity(DARCY), trait="generous"),
        beat(3, "learns", who=entity(ELIZABETH), what={"beat": 2}),
    )

    revised = reading(matcher, B=ELIZABETH, X=DARCY)
    assert revised.fills_by_step() == {"belief": [1], "fact": [2], "revelation": [3]}
    assert revised.status == COMPLETE


def test_learning_about_someone_else_does_not_revise_a_belief():
    matcher = run(
        "revised_belief",
        beat(1, "believes", who=entity(ELIZABETH), what=proposition("is", who=entity(DARCY), trait="cruel")),
        beat(2, "learns", who=entity(ELIZABETH), what=proposition("is", who=entity(WICKHAM), trait="a liar")),
    )

    assert reading(matcher, B=ELIZABETH, X=DARCY).status == LIVE


# exposed_lie


def wickhams_story(t=1):
    """Wickham tells Elizabeth that Darcy cheated him of his inheritance."""
    cheated = proposition("harms", who=entity(DARCY), whom=entity(WICKHAM))
    return beat(t, "says", who=entity(WICKHAM), what=cheated, to=entity(ELIZABETH))


def test_a_lie_is_exposed_when_its_listener_stops_believing_the_claim():
    matcher = run(
        "exposed_lie",
        wickhams_story(t=1),
        beat(2, "trusts", who=entity(ELIZABETH), whom=entity(WICKHAM)),
        beat(3, "distrusts", who=entity(ELIZABETH), whom=entity(WICKHAM), what={"beat": 1}),
    )

    exposed = reading(matcher, L=WICKHAM, D=ELIZABETH)
    assert exposed.fills_by_step() == {"claim": [1], "trust": [2], "exposure": [3]}
    assert exposed.status == COMPLETE


def test_a_lie_is_exposed_when_its_listener_learns_that_the_liar_hid_something():
    matcher = run(
        "exposed_lie",
        wickhams_story(t=1),
        beat(
            2,
            "learns",
            who=entity(ELIZABETH),
            what=proposition("hides", who=entity(WICKHAM), what="his debts"),
        ),
    )

    assert reading(matcher, L=WICKHAM, D=ELIZABETH).status == COMPLETE


def test_anyone_who_stops_believing_a_claim_made_to_no_one_in_particular_exposes_the_lie():
    claim = beat(
        1, "says", who=entity(MACBETH), what=proposition("kills", who=entity(HOOKER), whom=entity(DARCY))
    )
    matcher = run(
        "exposed_lie",
        claim,
        beat(2, "distrusts", who=entity(MACDUFF), whom=entity(MACBETH), what={"beat": 1}),
    )

    assert reading(matcher, L=MACBETH, D=MACDUFF).status == COMPLETE


def test_distrusting_the_liar_about_something_else_does_not_expose_the_lie():
    matcher = run(
        "exposed_lie",
        wickhams_story(t=1),
        beat(2, "distrusts", who=entity(ELIZABETH), whom=entity(WICKHAM)),
    )

    assert reading(matcher, L=WICKHAM, D=ELIZABETH).status == LIVE


# unreliable_narrator


def sheppards_account(t):
    """Dr Sheppard tells the reader he was at home all evening."""
    alibi = proposition("is_at", who=entity(SHEPPARD), where=entity(HOME))
    return beat(t, "says", known_by_players={READER}, who=entity(SHEPPARD), what=alibi)


def test_a_narrator_is_unreliable_when_the_reader_learns_late_of_a_deed_done_before_the_telling():
    murder = beat(1, "kills", who=entity(SHEPPARD), whom=entity(ACKROYD))
    murder_revealed = beat(1, "kills", known_by_players={READER}, who=entity(SHEPPARD), whom=entity(ACKROYD))
    solution = beat(3, "learns", known_by_players={READER}, who=entity(POIROT), what={"beat": 1})
    matcher = IncrementalMatcher([library_schema("unreliable_narrator")])

    matcher.step(murder, WORLD)
    matcher.step(sheppards_account(t=2), WORLD)
    matcher.step_together([murder_revealed, solution], WORLD, now=3)

    unreliable = reading(matcher, N=SHEPPARD)
    assert unreliable.fills_by_step() == {"account": [2], "deed": [1]}
    assert unreliable.status == COMPLETE


def test_a_deed_the_reader_saw_before_the_telling_does_not_make_the_narrator_unreliable():
    matcher = run(
        "unreliable_narrator",
        beat(1, "kills", known_by_players={READER}, who=entity(SHEPPARD), whom=entity(ACKROYD)),
        sheppards_account(t=2),
    )

    assert reading(matcher, N=SHEPPARD).status == LIVE


def test_a_deed_the_reader_sees_after_the_telling_refutes_the_unreliable_narrator():
    matcher = run(
        "unreliable_narrator",
        sheppards_account(t=1),
        beat(2, "kills", known_by_players={READER}, who=entity(SHEPPARD), whom=entity(ACKROYD)),
    )

    assert reading(matcher, N=SHEPPARD).status == REFUTED


# false_attribution


def test_learning_who_really_did_a_believed_deed_reveals_a_false_attribution():
    fortune_from_havisham = proposition("gives", who=entity(HAVISHAM), what="a fortune", to=entity(PIP))
    matcher = run(
        "false_attribution",
        beat(1, "believes", who=entity(PIP), what=fortune_from_havisham),
        beat(2, "gives", who=entity(MAGWITCH), what="a fortune", to=entity(PIP)),
        beat(3, "learns", who=entity(PIP), what={"beat": 2}),
    )

    corrected = reading(matcher, A=MAGWITCH, F=HAVISHAM, W=PIP)
    assert corrected.fills_by_step() == {"misattribution": [1], "deed": [2], "correction": [3]}
    assert corrected.status == COMPLETE


def test_a_false_attribution_can_be_corrected_by_learning_the_deed_as_a_proposition():
    matcher = run(
        "false_attribution",
        beat(
            1, "believes", who=entity(HARRY), what=proposition("harms", who=entity(SNAPE), whom=entity(HARRY))
        ),
        beat(
            2,
            "learns",
            who=entity(HARRY),
            what=proposition("harms", who=entity(QUIRRELL), whom=entity(HARRY)),
        ),
    )

    assert reading(matcher, A=QUIRRELL, F=SNAPE, W=HARRY).status == COMPLETE


def test_learning_that_the_suspect_did_it_after_all_is_no_false_attribution():
    snape_harms_harry = proposition("harms", who=entity(SNAPE), whom=entity(HARRY))
    matcher = run(
        "false_attribution",
        beat(1, "believes", who=entity(HARRY), what=snape_harms_harry),
        beat(2, "learns", who=entity(HARRY), what=snape_harms_harry),
    )

    assert COMPLETE not in statuses(matcher)


# hidden_loyalty


@pytest.mark.parametrize(
    "suspicion",
    [
        beat(1, "distrusts", who=entity(HARRY), whom=entity(SNAPE)),
        beat(
            1,
            "believes",
            who=entity(HARRY),
            what=proposition("opposes", who=entity(SNAPE), whom=entity(HARRY)),
        ),
    ],
    ids=["distrust", "belief in enmity"],
)
def test_a_suspect_who_secretly_protected_someone_reveals_a_hidden_loyalty(suspicion):
    matcher = run(
        "hidden_loyalty",
        suspicion,
        beat(2, "protects", who=entity(SNAPE), whom=entity(HARRY)),
        beat(3, "learns", who=entity(HARRY), what={"beat": 2}),
    )

    loyal = reading(matcher, H=SNAPE, P=HARRY, W=HARRY)
    assert loyal.fills_by_step() == {"suspicion": [1], "service": [2], "revelation": [3]}
    assert loyal.status == COMPLETE


def test_a_hidden_loyalty_is_revealed_by_learning_of_an_alliance_as_a_proposition():
    matcher = run(
        "hidden_loyalty",
        beat(1, "distrusts", who=entity(HARRY), whom=entity(SNAPE)),
        beat(
            2,
            "learns",
            who=entity(HARRY),
            what=proposition("allies", who=entity(SNAPE), whom=entity(QUIRRELL)),
        ),
    )

    assert reading(matcher, H=SNAPE, P=QUIRRELL, W=HARRY).status == COMPLETE


# prophecy_loophole


def test_learning_what_someone_else_is_reveals_the_loophole_in_a_prophecy():
    safe = proposition("is", who=entity(MACBETH), trait="safe from any man born of woman")
    invulnerable = proposition("is", who=entity(MACBETH), trait="invulnerable")
    not_born_of_woman = proposition("is", who=entity(MACDUFF), trait="untimely ripped from his mother's womb")
    matcher = run(
        "prophecy_loophole",
        beat(1, "says", who=entity(WITCHES), what=safe),
        beat(2, "believes", who=entity(MACBETH), what=invulnerable),
        beat(3, "learns", who=entity(MACBETH), what=not_born_of_woman),
    )

    loophole = reading(matcher, S=WITCHES, H=MACBETH, E=MACDUFF)
    assert loophole.fills_by_step() == {"foretelling": [1], "reliance": [2], "loophole": [3]}
    assert loophole.status == COMPLETE


def test_learning_about_oneself_is_no_loophole():
    matcher = run(
        "prophecy_loophole",
        beat(1, "says", who=entity(WITCHES), what=proposition("is", who=entity(MACBETH), trait="safe")),
        beat(2, "learns", who=entity(MACBETH), what=proposition("is", who=entity(MACBETH), trait="king")),
    )

    assert COMPLETE not in statuses(matcher)


# con


def lonnegans_con(*ending):
    return run(
        "con",
        beat(1, "trusts", who=entity(LONNEGAN), whom=entity(GONDORFF)),
        beat(2, "allies", who=entity(GONDORFF), whom=entity(HOOKER)),
        *ending,
    )


def test_a_mark_who_hands_over_their_money_and_then_learns_of_the_hidden_alliance_was_conned():
    matcher = lonnegans_con(
        beat(3, "gives", who=entity(LONNEGAN), what="half a million dollars", to=entity(GONDORFF)),
        beat(4, "learns", who=entity(LONNEGAN), what={"beat": 2}),
    )

    conned = reading(matcher, K=GONDORFF, M=LONNEGAN, A=HOOKER)
    assert conned.fills_by_step() == {"approach": [1], "alliance": [2], "take": [3], "exposure": [4]}
    assert conned.status == COMPLETE


def test_a_con_needs_the_mark_to_hand_something_over():
    matcher = lonnegans_con(beat(3, "learns", who=entity(LONNEGAN), what={"beat": 2}))

    assert COMPLETE not in statuses(matcher)
