import pytest

from matching.beats import PlainBeat
from matching.match import MatchContext, match
from schemas.patterns import BeatPattern, RoleVariable

MINISTER, PARTY, HERALD, COURIER = 1, 2, 3, 4
ANNA, BEN = 10, 11
ENTITY_KINDS = {MINISTER: "character", PARTY: "faction", HERALD: "source", COURIER: "source"}
ROLE_KINDS = {"M": "character", "P": "faction", "O": "source"}


def entity(entity_id):
    return {"entity": entity_id}


def context(for_player=None):
    return MatchContext(
        role_kinds=ROLE_KINDS,
        entity_kinds=ENTITY_KINDS,
        players=frozenset({ANNA, BEN}),
        for_player=for_player,
    )


def breaks(known_by_players=frozenset({ANNA, BEN})):
    return PlainBeat(
        t=1,
        pred="breaks",
        args={"who": entity(MINISTER), "whom": entity(PARTY)},
        known_by_players=known_by_players,
    )


def says(outlet, claim):
    return PlainBeat(t=2, pred="says", args={"who": entity(outlet), "what": {"prop": claim}})


BREAKS_WITH_PARTY = {"pred": "breaks", "args": {"who": entity(MINISTER), "whom": entity(PARTY)}}
VISIBLE_BREAK = BeatPattern(
    pred="breaks", args={"who": RoleVariable("M"), "whom": RoleVariable("P")}, players_know=True
)
CLAIMED_BREAK = BeatPattern(
    pred="breaks", args={"who": RoleVariable("M"), "whom": RoleVariable("P")}, claimed_by=RoleVariable("O")
)


class TestPlayersKnow:
    def test_beat_every_player_knows_matches_for_the_table(self):
        assert match(VISIBLE_BREAK, breaks(), {}, context()) == {"M": MINISTER, "P": PARTY}

    def test_beat_only_some_players_know_does_not_match_for_the_table(self):
        assert match(VISIBLE_BREAK, breaks(known_by_players=frozenset({ANNA})), {}, context()) is None

    def test_private_beat_matches_for_the_player_who_knows_it(self):
        private = breaks(known_by_players=frozenset({ANNA}))

        assert match(VISIBLE_BREAK, private, {}, context(for_player=ANNA)) is not None
        assert match(VISIBLE_BREAK, private, {}, context(for_player=BEN)) is None

    def test_beat_no_player_knows_does_not_match(self):
        assert match(VISIBLE_BREAK, breaks(known_by_players=frozenset()), {}, context()) is None

    def test_pattern_without_scope_matches_beats_nobody_knows(self):
        unscoped = BeatPattern(pred="breaks", args={"who": RoleVariable("M")})

        assert match(unscoped, breaks(known_by_players=frozenset()), {}, context()) == {"M": MINISTER}


class TestClaims:
    def test_claimed_pattern_matches_the_proposition_and_binds_the_speaker(self):
        assert match(CLAIMED_BREAK, says(HERALD, BREAKS_WITH_PARTY), {}, context()) == {
            "O": HERALD,
            "M": MINISTER,
            "P": PARTY,
        }

    def test_bound_source_must_be_the_speaker(self):
        assert match(CLAIMED_BREAK, says(HERALD, BREAKS_WITH_PARTY), {"O": COURIER}, context()) is None

    def test_claimed_pattern_does_not_match_a_beat_that_is_not_a_claim(self):
        assert match(CLAIMED_BREAK, breaks(), {}, context()) is None

    def test_claimed_pattern_needs_the_same_predicate_inside_the_claim(self):
        other_claim = {"pred": "allies", "args": {"who": entity(MINISTER), "whom": entity(PARTY)}}

        assert match(CLAIMED_BREAK, says(HERALD, other_claim), {}, context()) is None

    def test_claims_never_count_as_facts(self):
        """Without claimed_by a pattern never looks inside a claim: the engine does not judge truth (RQ4)."""
        fact_pattern = BeatPattern(pred="breaks", args={"who": RoleVariable("M"), "whom": RoleVariable("P")})

        assert match(fact_pattern, says(HERALD, BREAKS_WITH_PARTY), {}, context()) is None


@pytest.mark.django_db
def test_plain_beat_knows_which_players_were_granted_it_at_its_own_t(
    chronicle, players, entity_factory, beat_factory
):
    minister = entity_factory()
    anna, ben = players
    shared = beat_factory("is", who=minister, trait="tired", players=[anna, ben])
    private = beat_factory("is", who=minister, trait="ambitious", players=[anna])

    assert PlainBeat.from_model(shared).known_by_players == {anna.id, ben.id}
    assert PlainBeat.from_model(private).known_by_players == {anna.id}
