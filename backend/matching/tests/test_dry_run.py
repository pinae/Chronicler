import pytest

from chronicle.beat_log import InvalidReference
from chronicle.models import Beat, EntityAttribute, ScopeGrant, Utterance
from evaluation.replay import replay_story
from matching.dry_run import CandidateBeat, dry_run
from matching.models import Hypothesis, StepFill
from matching.tests.story_runs import matched_story
from schemas.vocabulary import InvalidBeatArgs, UnknownPredicate

pytestmark = pytest.mark.django_db


def entity(chronicle, slug):
    return {"entity": chronicle.entities.get(slug=slug).pk}


def present(chronicle, *slugs):
    return [chronicle.entities.get(slug=slug).pk for slug in slugs]


def effects_by_binding(chronicle, effects):
    slug_of = dict(chronicle.entities.values_list("pk", "slug"))
    return {
        tuple(slug_of.get(entity_id) for entity_id in effect.binding.values()): effect for effect in effects
    }


def steal_the_seal(chronicle, players_present=()):
    return CandidateBeat(
        pred="steals",
        args={
            "who": entity(chronicle, "aldric"),
            "what": entity(chronicle, "seal"),
            "from": entity(chronicle, "mira"),
        },
        characters_present=present(chronicle, "aldric"),
        players_present=players_present,
    )


def test_a_candidate_beat_would_fill_a_matching_hypothesis():
    steward = matched_story("steward", until_t=11)

    effects = effects_by_binding(steward, dry_run(steward, steal_the_seal(steward)))

    effect = effects[("aldric", "mira", "seal")]
    assert effect.hypothesis_id is not None
    assert (effect.changes, effect.filled_step) == (["filled"], "harm")
    assert (effect.weight_before, effect.weight_after) == (0.0, 1.5)


def test_a_candidate_beat_would_seed_a_new_hypothesis():
    steward = matched_story("steward", until_t=11)
    edda_trusts_ronan = CandidateBeat(
        pred="trusts", args={"who": entity(steward, "edda"), "whom": entity(steward, "ronan")}
    )

    effects = effects_by_binding(steward, dry_run(steward, edda_trusts_ronan))

    effect = effects[("ronan", "edda", None)]
    assert (effect.hypothesis_id, effect.changes, effect.filled_step) == (None, ["seeded"], "trust")
    assert (effect.weight_before, effect.weight_after) == (None, -1.5)


def test_a_candidate_beat_would_refine_a_hypothesis_with_open_roles():
    steward = matched_story("steward", until_t=11)
    open_suspicion = Hypothesis.objects.get(
        chronicle=steward, binding={"T": steward.entities.get(slug="aldric").pk, "V": None, "S": None}
    )
    edda_trusts_aldric = CandidateBeat(
        pred="trusts", args={"who": entity(steward, "edda"), "whom": entity(steward, "aldric")}
    )

    effects = effects_by_binding(steward, dry_run(steward, edda_trusts_aldric))

    effect = effects[("aldric", "edda", None)]
    assert (effect.hypothesis_id, effect.changes, effect.refines) == (None, ["refined"], open_suspicion.pk)


def test_a_candidate_beat_would_complete_a_hypothesis():
    steward = matched_story("steward", until_t=21)
    the_theft = steward.beats.get(t=13)
    reveal = CandidateBeat(
        pred="learns",
        args={"who": entity(steward, "mira"), "what": {"beat": the_theft.t}, "from": entity(steward, "edda")},
        characters_present=present(steward, "mira", "edda"),
    )

    effects = effects_by_binding(steward, dry_run(steward, reveal))

    effect = effects[("aldric", "mira", "seal")]
    assert effect.changes == ["filled", "completed"]
    assert (effect.filled_step, effect.status) == ("reveal", "complete")


def test_a_candidate_beat_would_refute_the_hypotheses_it_contradicts():
    steward = matched_story("steward", until_t=11)
    aldric_dies = CandidateBeat(
        pred="kills", args={"who": entity(steward, "raider"), "whom": entity(steward, "aldric")}
    )

    effects = effects_by_binding(steward, dry_run(steward, aldric_dies))

    suspicions_of_aldric = {("aldric", "mira", None), ("aldric", None, None), ("aldric", "mira", "seal")}
    assert suspicions_of_aldric <= set(effects)
    assert {tuple(effects[binding].changes) for binding in suspicions_of_aldric} == {("refuted",)}


def row_counts():
    tables = [Beat, Utterance, Hypothesis, StepFill, ScopeGrant, EntityAttribute]
    return {table.__name__: table._default_manager.count() for table in tables}


def test_a_dry_run_keeps_nothing():
    steward = matched_story("steward", until_t=11)
    counts_before = row_counts()
    weights_before = list(Hypothesis.objects.order_by("pk").values_list("status", "weight"))

    dry_run(steward, steal_the_seal(steward))

    assert row_counts() == counts_before
    assert list(Hypothesis.objects.order_by("pk").values_list("status", "weight")) == weights_before


def test_a_candidate_beat_that_does_not_fit_the_vocabulary_is_rejected():
    steward = matched_story("steward", until_t=11)
    beats_before = Beat.objects.count()
    missing_whom = CandidateBeat(pred="trusts", args={"who": entity(steward, "edda")})
    unknown_predicate = CandidateBeat(pred="adores", args={"who": entity(steward, "edda")})

    with pytest.raises(InvalidBeatArgs, match="missing role 'whom'"):
        dry_run(steward, missing_whom)
    with pytest.raises(UnknownPredicate):
        dry_run(steward, unknown_predicate)
    assert Beat.objects.count() == beats_before


def test_a_candidate_beat_about_another_chronicles_entities_is_rejected():
    steward = matched_story("steward", until_t=11)
    other = matched_story("minimal")
    foreigner = other.entities.all()[0]
    trusts_a_foreigner = CandidateBeat(
        pred="trusts", args={"who": entity(steward, "edda"), "whom": {"entity": foreigner.pk}}
    )

    with pytest.raises(InvalidReference):
        dry_run(steward, trusts_a_foreigner)


def test_a_players_lattice_only_changes_if_the_player_would_see_the_beat():
    steward = replay_story("steward", reader=None, until_t=11, per_player=True)
    ben = steward.players.get(name="Ben")

    unseen = dry_run(steward, steal_the_seal(steward, players_present=[]), for_player=ben)
    seen = effects_by_binding(
        steward, dry_run(steward, steal_the_seal(steward, players_present=[ben.pk]), for_player=ben)
    )

    assert unseen == []
    assert seen[("aldric", "mira", "seal")].changes == ["filled"]
