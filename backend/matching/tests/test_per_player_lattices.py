import pytest

from chronicle.facts import StoredChronicleFacts
from chronicle.story_fixtures import load_story
from matching.lattice import Lattice
from matching.models import Hypothesis
from matching.store import StoredMatcher
from schemas.library import load_library

pytestmark = pytest.mark.django_db


def run(chronicle, for_player=None):
    matcher = StoredMatcher(chronicle, for_player=for_player)
    for beat in chronicle.beats.order_by("t"):
        matcher.step(beat)


def backstory(until_t=None):
    load_library()
    chronicle = load_story("backstory", until_t=until_t)
    return chronicle, chronicle.players.get(name="Anna"), chronicle.players.get(name="Ben")


def statuses(lattice, chronicle):
    slug_of = dict(chronicle.entities.values_list("pk", "slug"))
    return {
        tuple(slug_of.get(entity) for entity in hypothesis.binding.values()): hypothesis.status
        for hypothesis in lattice.hypotheses
    }


def test_private_backstory_completes_the_betrayal_in_that_players_lattice():
    chronicle, anna, _ = backstory()

    run(chronicle, for_player=anna)

    assert (
        statuses(Lattice.at(chronicle, 4, for_player=anna), chronicle)[("aldric", "mira", "seal")]
        == "complete"
    )


def test_player_who_never_saw_the_backstory_has_no_complete_betrayal():
    chronicle, _, ben = backstory()

    run(chronicle, for_player=ben)

    assert set(statuses(Lattice.at(chronicle, 4, for_player=ben), chronicle).values()) == {"live"}


def test_the_unfiltered_lattice_sees_every_beat_like_the_game_master():
    chronicle, anna, ben = backstory()

    run(chronicle)
    run(chronicle, for_player=anna)
    run(chronicle, for_player=ben)

    assert statuses(Lattice.at(chronicle, 4), chronicle)[("aldric", "mira", "seal")] == "complete"


def test_each_lattice_only_holds_its_own_hypotheses():
    chronicle, anna, ben = backstory()

    run(chronicle, for_player=anna)
    run(chronicle, for_player=ben)

    assert Lattice.at(chronicle, 4).hypotheses == ()
    assert {row.for_player for row in Hypothesis.objects.all()} == {anna, ben}


def test_per_player_lattice_obeys_the_replay_guarantee():
    whole, anna_whole, _ = backstory()
    run(whole, for_player=anna_whole)
    prefix, anna_prefix, _ = backstory(until_t=3)
    run(prefix, for_player=anna_prefix)

    assert statuses(Lattice.at(whole, 3, for_player=anna_whole), whole) == statuses(
        Lattice.at(prefix, 3, for_player=anna_prefix), prefix
    )


def test_players_only_know_of_character_knowledge_conveyed_by_beats_they_saw(
    chronicle, players, entity_factory, beat_factory
):
    anna, ben = players
    mira, aldric = entity_factory(), entity_factory()
    secret = beat_factory("hides", who=mira, what=aldric, characters=[mira], players=[anna, ben])
    beat_factory("learns", who=aldric, what=secret, players=[anna])

    assert StoredChronicleFacts(chronicle, for_player=anna).first_known_at(aldric.id, secret.t) == 2
    assert StoredChronicleFacts(chronicle, for_player=ben).first_known_at(aldric.id, secret.t) is None
    assert StoredChronicleFacts(chronicle).first_known_at(aldric.id, secret.t) == 2


def test_players_only_know_of_locations_from_beats_they_saw(chronicle, players, entity_factory, beat_factory):
    anna, ben = players
    aldric, hall, cellar = entity_factory(), entity_factory(kind="place"), entity_factory(kind="place")
    beat_factory("is_at", who=aldric, where=hall, players=[anna, ben])
    beat_factory("is_at", who=aldric, where=cellar, players=[anna])

    assert StoredChronicleFacts(chronicle, for_player=anna).location_at(aldric.id, 2) == {"entity": cellar.id}
    assert StoredChronicleFacts(chronicle, for_player=ben).location_at(aldric.id, 2) == {"entity": hall.id}


def test_a_players_matcher_ignores_the_hypotheses_of_other_lattices():
    chronicle, anna, ben = backstory()
    run(chronicle)

    run(chronicle, for_player=ben)

    ben_lattice = Lattice.at(chronicle, 4, for_player=ben)
    assert statuses(ben_lattice, chronicle) == {
        ("aldric", "mira", None): "live",
        ("aldric", "mira", "seal"): "live",
    }
    assert {hypothesis.created_at_t for hypothesis in ben_lattice.hypotheses} == {1, 3}
