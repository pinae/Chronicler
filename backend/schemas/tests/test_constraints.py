from dataclasses import dataclass, field

import pytest
import yaml

from schemas.constraints import After, Before, Distinct, Knows, NotKnows, SamePlace, parse_constraint
from schemas.definitions import SchemaDefinitionError, parse_schema
from schemas.library import LIBRARY_DIR

T, V, S = 1, 2, 3
HALL, CELLAR = 20, 21


@dataclass
class Hypothesis:
    """Plain data: role binding plus the t of each step's fills."""

    binding: dict
    fills: dict = field(default_factory=dict)

    def fill_ts(self, step_id):
        return sorted(self.fills.get(step_id, []))


@dataclass
class Facts:
    """What the chronicle says: when a character first knew a beat, where entities were."""

    first_known: dict = field(default_factory=dict)  # (character, beat t) -> t of first grant
    locations: dict = field(default_factory=dict)  # entity -> [(from t, place)]

    def first_known_at(self, character_id, beat_t):
        return self.first_known.get((character_id, beat_t))

    def location_at(self, entity_id, t):
        visits = [place for since, place in self.locations.get(entity_id, []) if since <= t]
        return {"entity": visits[-1]} if visits else None


BETRAYAL = Hypothesis(binding={"T": T, "V": V, "S": S}, fills={"trust": [3], "harm": [7], "reveal": [12]})


class TestDistinct:
    def test_different_entities_satisfy_it(self):
        assert Distinct(roles=("T", "V")).check(BETRAYAL, Facts(), t=20)

    def test_the_same_entity_in_both_roles_violates_it(self):
        assert not Distinct(roles=("T", "V")).check(Hypothesis({"T": T, "V": T}), Facts(), t=20)

    def test_unbound_roles_do_not_violate_it(self):
        assert Distinct(roles=("T", "V")).check(Hypothesis({"T": T, "V": None}), Facts(), t=20)


class TestBeforeAndAfter:
    def test_earlier_step_satisfies_before(self):
        assert Before(steps=("trust", "harm")).check(BETRAYAL, Facts(), t=20)

    def test_later_step_violates_before(self):
        late_trust = Hypothesis(BETRAYAL.binding, {"trust": [8], "harm": [7]})

        assert not Before(steps=("trust", "harm")).check(late_trust, Facts(), t=20)

    def test_the_earliest_fill_of_a_repeatable_step_counts(self):
        trusted_twice = Hypothesis(BETRAYAL.binding, {"trust": [8, 3], "harm": [7]})

        assert Before(steps=("trust", "harm")).check(trusted_twice, Facts(), t=20)

    def test_unfilled_step_does_not_violate_before(self):
        assert Before(steps=("trust", "harm")).check(
            Hypothesis(BETRAYAL.binding, {"trust": [3]}), Facts(), t=20
        )

    def test_fills_after_t_are_not_yet_known(self):
        late_trust = Hypothesis(BETRAYAL.binding, {"trust": [8], "harm": [7]})

        assert Before(steps=("trust", "harm")).check(late_trust, Facts(), t=7)

    def test_after_is_the_mirror_of_before(self):
        assert After(steps=("harm", "trust")).check(BETRAYAL, Facts(), t=20)
        assert not After(steps=("trust", "harm")).check(BETRAYAL, Facts(), t=20)


class TestKnows:
    def test_character_who_knew_the_beat_when_it_filled_the_step_satisfies_it(self):
        facts = Facts(first_known={(T, 7): 7})

        assert Knows(role="T", step="harm").check(BETRAYAL, facts, t=20)

    def test_character_who_learned_the_beat_later_violates_it(self):
        facts = Facts(first_known={(T, 7): 9})

        assert not Knows(role="T", step="harm").check(BETRAYAL, facts, t=20)

    def test_unfilled_step_or_unbound_role_does_not_violate_it(self):
        assert Knows(role="T", step="harm").check(Hypothesis(BETRAYAL.binding), Facts(), t=20)
        assert Knows(role="T", step="harm").check(Hypothesis({"T": None}, {"harm": [7]}), Facts(), t=20)


class TestNotKnows:
    """Knowledge changes while a story is told: the victim may learn of the harm, but only at the reveal."""

    until_reveal = NotKnows(role="V", step="harm", until="reveal")

    def test_learning_at_the_reveal_satisfies_it(self):
        facts = Facts(first_known={(V, 7): 12})

        assert self.until_reveal.check(BETRAYAL, facts, t=20)

    def test_learning_before_the_reveal_violates_it(self):
        facts = Facts(first_known={(V, 7): 9})

        assert not self.until_reveal.check(BETRAYAL, facts, t=20)

    def test_learning_after_t_is_not_yet_known(self):
        facts = Facts(first_known={(V, 7): 9})
        before_reveal = Hypothesis(BETRAYAL.binding, {"trust": [3], "harm": [7]})

        assert self.until_reveal.check(before_reveal, facts, t=8)
        assert not self.until_reveal.check(before_reveal, facts, t=10)

    def test_without_until_the_character_may_never_know(self):
        facts = Facts(first_known={(V, 7): 30})
        forever = NotKnows(role="V", step="harm")

        assert forever.check(BETRAYAL, facts, t=29)
        assert not forever.check(BETRAYAL, facts, t=30)

    def test_unfilled_step_does_not_violate_it(self):
        assert self.until_reveal.check(Hypothesis(BETRAYAL.binding), Facts(first_known={(V, 7): 1}), t=20)


class TestSamePlace:
    def test_roles_at_the_same_place_when_the_step_was_filled_satisfy_it(self):
        facts = Facts(locations={T: [(1, HALL)], V: [(2, HALL), (9, CELLAR)]})

        assert SamePlace(roles=("T", "V"), step="harm").check(BETRAYAL, facts, t=20)

    def test_roles_at_different_places_violate_it(self):
        facts = Facts(locations={T: [(1, HALL)], V: [(2, CELLAR)]})

        assert not SamePlace(roles=("T", "V"), step="harm").check(BETRAYAL, facts, t=20)

    def test_unknown_location_does_not_violate_it(self):
        facts = Facts(locations={T: [(1, HALL)]})

        assert SamePlace(roles=("T", "V"), step="harm").check(BETRAYAL, facts, t=20)

    def test_without_a_step_the_places_at_t_count(self):
        facts = Facts(locations={T: [(1, HALL)], V: [(2, CELLAR), (15, HALL)]})

        assert not SamePlace(roles=("T", "V")).check(BETRAYAL, facts, t=10)
        assert SamePlace(roles=("T", "V")).check(BETRAYAL, facts, t=15)


@pytest.mark.parametrize(
    "document",
    [
        {"type": "distinct", "roles": ["T", "V"]},
        {"type": "before", "steps": ["trust", "harm"]},
        {"type": "after", "steps": ["harm", "trust"]},
        {"type": "knows", "role": "T", "step": "harm"},
        {"type": "not_knows", "role": "V", "step": "harm", "until": "reveal"},
        {"type": "not_knows", "role": "V", "step": "harm"},
        {"type": "same_place", "roles": ["T", "V"], "step": "harm"},
        {"type": "same_place", "roles": ["T", "V"]},
    ],
)
def test_constraints_round_trip(document):
    constraint = parse_constraint(document, role_names={"T", "V", "S"}, step_ids={"trust", "harm", "reveal"})

    assert constraint.to_document() == document


def test_betrayal_constraints_are_typed():
    betrayal = parse_schema(
        yaml.safe_load((LIBRARY_DIR / "betrayal.yaml").read_text()), source="betrayal.yaml"
    )

    assert betrayal.constraints == (
        Distinct(roles=("T", "V")),
        Before(steps=("trust", "harm")),
        Knows(role="T", step="harm"),
        NotKnows(role="V", step="harm", until="reveal"),
    )


SCHEMA_WITH_CONSTRAINT = """
slug: rivalry
name: Rivalry
roles: {A: character, B: character}
constraints:
  - {type: distinct, roles: [A, B]}
  - CONSTRAINT
steps:
  - step_id: clash
    phase: setup
    patterns: [{pred: opposes, args: {who: $A, whom: $B}}]
"""


@pytest.mark.parametrize(
    ("constraint", "message"),
    [
        ("{type: loves, roles: [A, B]}", r"constraint 2: unknown type 'loves'"),
        ("{type: before, steps: [clash, showdown]}", r"constraint 2 \(before\): 'showdown' is not a step"),
        ("{type: knows, role: C, step: clash}", r"constraint 2 \(knows\): 'C' is not a role"),
        (
            "{type: not_knows, role: A, step: clash, until: finale}",
            r"constraint 2 \(not_knows\): 'finale' is not a step",
        ),
        ("{type: before, steps: [clash]}", r"constraint 2 \(before\): needs exactly two steps"),
        ("{type: knows, step: clash}", r"constraint 2 \(knows\): missing key 'role'"),
    ],
)
def test_invalid_constraints_are_rejected_by_the_loader(constraint, message):
    document = yaml.safe_load(SCHEMA_WITH_CONSTRAINT.replace("CONSTRAINT", constraint))

    with pytest.raises(SchemaDefinitionError, match=rf"test\.yaml: {message}"):
        parse_schema(document, source="test.yaml")
