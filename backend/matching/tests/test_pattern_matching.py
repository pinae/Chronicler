import pytest

from matching.beats import PlainBeat
from matching.match import MatchContext, match
from schemas.patterns import BeatPattern, Literal, RoleVariable, StepReference, Wildcard

MIRA, ALDRIC, KEY, HALL = 1, 2, 3, 4
ENTITY_KINDS = {MIRA: "character", ALDRIC: "character", KEY: "object", HALL: "place"}
ROLE_KINDS = {"T": "character", "V": "character", "S": "object"}


def entity(entity_id):
    return {"entity": entity_id}


def beat(pred, t=1, tags=(), **args):
    return PlainBeat(t=t, pred=pred, args=args, tags=tuple(tags))


def context(fills=None):
    return MatchContext(role_kinds=ROLE_KINDS, entity_kinds=ENTITY_KINDS, fills=fills or {})


def trusts(who, whom, t=1, tags=()):
    return beat("trusts", t=t, tags=tags, who=entity(who), whom=entity(whom))


TRUST_PATTERN = BeatPattern(pred="trusts", args={"who": RoleVariable("V"), "whom": RoleVariable("T")})


def test_different_predicate_does_not_match():
    assert (
        match(TRUST_PATTERN, beat("distrusts", who=entity(MIRA), whom=entity(ALDRIC)), {}, context()) is None
    )


def test_wildcard_and_omitted_roles_match_anything():
    pattern = BeatPattern(pred="gives", args={"to": RoleVariable("T"), "what": Wildcard()})
    gift = beat("gives", who=entity(MIRA), what={"literal": "gold"}, to=entity(ALDRIC))

    assert match(pattern, gift, {}, context()) == {"T": ALDRIC}


def test_literal_matches_only_an_equal_literal():
    nervous = BeatPattern(pred="is", args={"who": RoleVariable("T"), "trait": Literal("nervous")})

    assert match(nervous, beat("is", who=entity(ALDRIC), trait={"literal": "nervous"}), {}, context()) == {
        "T": ALDRIC
    }
    assert match(nervous, beat("is", who=entity(ALDRIC), trait={"literal": "calm"}), {}, context()) is None


def test_bound_variable_matches_only_the_bound_entity():
    assert match(TRUST_PATTERN, trusts(MIRA, ALDRIC), {"T": ALDRIC, "V": MIRA}, context()) == {
        "T": ALDRIC,
        "V": MIRA,
    }
    assert match(TRUST_PATTERN, trusts(MIRA, ALDRIC), {"T": MIRA}, context()) is None


def test_unbound_variable_extends_a_copy_of_the_binding():
    binding = {"T": None, "V": MIRA}

    extended = match(TRUST_PATTERN, trusts(MIRA, ALDRIC), binding, context())

    assert extended == {"T": ALDRIC, "V": MIRA}
    assert binding == {"T": None, "V": MIRA}


def test_step_reference_matches_only_the_beat_that_filled_that_step():
    reveal = BeatPattern(pred="learns", args={"who": RoleVariable("V"), "what": StepReference("harm")})
    learns_harm = beat("learns", t=9, who=entity(MIRA), what={"beat": 7})
    learns_other = beat("learns", t=9, who=entity(MIRA), what={"beat": 5})

    assert match(reveal, learns_harm, {"V": MIRA}, context(fills={"harm": [7]})) == {"V": MIRA}
    assert match(reveal, learns_other, {"V": MIRA}, context(fills={"harm": [7]})) is None


def test_step_reference_to_an_unfilled_step_never_matches():
    reveal = BeatPattern(pred="learns", args={"who": RoleVariable("V"), "what": StepReference("harm")})

    assert match(reveal, beat("learns", t=9, who=entity(MIRA), what={"beat": 7}), {}, context()) is None


def test_nested_pattern_recurses_into_a_proposition_and_extends_the_binding():
    access = BeatPattern(
        pred="learns",
        args={
            "who": RoleVariable("T"),
            "what": BeatPattern(pred="hides", args={"who": RoleVariable("V"), "what": RoleVariable("S")}),
        },
    )
    hiding = {"prop": {"pred": "hides", "args": {"who": entity(MIRA), "what": entity(KEY)}}}

    assert match(access, beat("learns", who=entity(ALDRIC), what=hiding), {}, context()) == {
        "T": ALDRIC,
        "V": MIRA,
        "S": KEY,
    }


def test_nested_pattern_does_not_match_a_value_that_is_not_a_proposition():
    access = BeatPattern(pred="learns", args={"what": BeatPattern(pred="hides")})

    assert match(access, beat("learns", who=entity(ALDRIC), what={"beat": 1}), {}, context()) is None


def test_nested_pattern_needs_the_same_predicate():
    access = BeatPattern(pred="learns", args={"what": BeatPattern(pred="hides")})
    other = {"prop": {"pred": "has", "args": {"who": entity(MIRA), "what": entity(KEY)}}}

    assert match(access, beat("learns", who=entity(ALDRIC), what=other), {}, context()) is None


@pytest.mark.parametrize(
    ("tags", "matches"),
    [(("nervous",), True), (("secretly", "loud"), True), (("loud",), False), ((), False)],
)
def test_tags_any_needs_at_least_one_of_the_tags(tags, matches):
    pattern = BeatPattern(pred="trusts", tags_any=("nervous", "secretly"))

    assert (match(pattern, trusts(MIRA, ALDRIC, tags=tags), {}, context()) is not None) is matches


@pytest.mark.parametrize(
    ("tags", "matches"),
    [(("nervous", "secretly", "loud"), True), (("nervous",), False)],
)
def test_tags_all_needs_every_tag(tags, matches):
    pattern = BeatPattern(pred="trusts", tags_all=("nervous", "secretly"))

    assert (match(pattern, trusts(MIRA, ALDRIC, tags=tags), {}, context()) is not None) is matches


def test_binding_a_role_to_an_entity_of_the_wrong_kind_does_not_match():
    holds = BeatPattern(pred="has", args={"who": RoleVariable("T"), "what": RoleVariable("S")})

    assert match(holds, beat("has", who=entity(ALDRIC), what=entity(HALL)), {}, context()) is None
    assert match(holds, beat("has", who=entity(ALDRIC), what=entity(KEY)), {}, context()) == {
        "T": ALDRIC,
        "S": KEY,
    }


def test_role_variable_does_not_match_a_literal():
    holds = BeatPattern(pred="has", args={"who": RoleVariable("T"), "what": RoleVariable("S")})

    assert match(holds, beat("has", who=entity(ALDRIC), what={"literal": "gold"}), {}, context()) is None


def test_pattern_role_missing_from_the_beat_does_not_match():
    with_method = BeatPattern(pred="helps", args={"who": RoleVariable("T"), "how": Literal("with a rope")})

    assert match(with_method, beat("helps", who=entity(ALDRIC), whom=entity(MIRA)), {}, context()) is None


def test_quarantined_beats_never_match():
    quarantined = trusts(MIRA, ALDRIC, tags=("quarantined",))

    assert match(TRUST_PATTERN, quarantined, {}, context()) is None
