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


def find(lattice, chronicle, **binding_slugs):
    ids = {slug: pk for pk, slug in chronicle.entities.values_list("pk", "slug")}
    wanted = {role: ids[slug] for role, slug in binding_slugs.items()}
    return next((hypothesis for hypothesis in lattice.hypotheses if dict(hypothesis.binding) == wanted), None)


def steward_with_lattices_for(*names, until_t=None):
    chronicle = load_story("steward", until_t=until_t)
    load_library()
    players = [chronicle.players.get(name=name) for name in names]
    for player in players:
        run(chronicle, for_player=player)
    return chronicle, players


def test_a_beat_a_player_learns_later_enters_their_lattice_when_they_learn_it():
    """Regression (steward, t=22): the players hear Edda tell Mira of the theft (t=13, which the
    table never saw), but their lattices never took the theft up, so no betrayal could complete."""
    chronicle, [anna, ben] = steward_with_lattices_for("Anna", "Ben")
    seal_betrayal = {"T": "aldric", "V": "mira", "S": "seal"}

    before = find(Lattice.at(chronicle, 21, for_player=anna), chronicle, **seal_betrayal)
    annas = find(Lattice.at(chronicle, 22, for_player=anna), chronicle, **seal_betrayal)
    bens = find(Lattice.at(chronicle, 22, for_player=ben), chronicle, **seal_betrayal)

    assert before is None
    assert {(fill.step_id, fill.beat_t, fill.filled_at_t) for fill in annas.fills} >= {
        ("harm", 13, 22),
        ("reveal", 22, 22),
    }
    # Only Ben saw how Aldric learned where the seal is hidden (t=7): Anna's betrayal lacks access.
    assert (annas.status, bens.status) == ("live", "complete")


def test_a_player_lattice_with_learned_beats_obeys_the_replay_guarantee():
    whole, [anna_whole] = steward_with_lattices_for("Anna")
    prefix, [anna_prefix] = steward_with_lattices_for("Anna", until_t=22)

    assert statuses(Lattice.at(whole, 22, for_player=anna_whole), whole) == statuses(
        Lattice.at(prefix, 22, for_player=anna_prefix), prefix
    )
    assert statuses(Lattice.at(whole, 21, for_player=anna_whole), whole) == statuses(
        Lattice.at(prefix, 21, for_player=anna_prefix), prefix
    )
