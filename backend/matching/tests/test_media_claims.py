"""Media chronicles (R3): every statement is a claim by its outlet, and claimed_by patterns match it."""

import pytest

from matching.lattice import Lattice
from matching.tests.story_runs import matched_story

pytestmark = pytest.mark.django_db


def slugs_of(chronicle, binding):
    slug_of = dict(chronicle.entities.values_list("pk", "slug"))
    return {role: slug_of.get(entity) for role, entity in binding.items()}


def test_an_outlets_claims_complete_the_blame_narrative_attributed_to_it():
    harbour_fire = matched_story("harbour-fire")

    lattice = Lattice.at(harbour_fire, harbour_fire.beats.count())

    [blame] = [hypothesis for hypothesis in lattice.hypotheses if hypothesis.schema == "blame"]
    assert slugs_of(harbour_fire, blame.binding) == {"O": "courier", "A": "holt", "V": "petra"}
    assert blame.status == "complete"
    assert {fill.step_id for fill in blame.fills} == {"accusation", "motive", "sympathy", "condemnation"}


def test_claims_are_not_taken_as_facts_by_schemas_without_claimed_by():
    harbour_fire = matched_story("harbour-fire")

    lattice = Lattice.at(harbour_fire, harbour_fire.beats.count())

    assert not [hypothesis for hypothesis in lattice.hypotheses if hypothesis.schema == "betrayal"]
