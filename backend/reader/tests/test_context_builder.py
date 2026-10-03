import pytest

from narrative_engine import di
from reader.context import RecentAndSupportingBeats, Supporting, bounded_context
from reader.interfaces import ContextBeat

VISIBLE = tuple(ContextBeat(t=t, text=f"beat {t}") for t in range(1, 11))


def test_context_holds_the_most_recent_beats():
    context = bounded_context(10, VISIBLE, supporting=[], recent_beats=3, top_hypotheses=2)

    assert context.included_beat_ts == [8, 9, 10]
    assert context.t == 10


def test_context_adds_the_beats_supporting_the_strongest_hypotheses_in_t_order():
    supporting = [Supporting(weight=1.0, beat_ts=(2, 9)), Supporting(weight=0.5, beat_ts=(4,))]

    context = bounded_context(10, VISIBLE, supporting, recent_beats=3, top_hypotheses=2)

    assert context.included_beat_ts == [2, 4, 8, 9, 10]


def test_hypotheses_beyond_the_top_k_add_nothing():
    supporting = [
        Supporting(weight=-1.0, beat_ts=(1,)),
        Supporting(weight=2.0, beat_ts=(3,)),
        Supporting(weight=1.0, beat_ts=(5,)),
    ]

    context = bounded_context(10, VISIBLE, supporting, recent_beats=1, top_hypotheses=2)

    assert context.included_beat_ts == [3, 5, 10]


def test_supporting_beats_the_audience_did_not_see_are_left_out():
    private_beats_missing = tuple(beat for beat in VISIBLE if beat.t != 4)

    context = bounded_context(
        10, private_beats_missing, [Supporting(1.0, (4, 6))], recent_beats=1, top_hypotheses=1
    )

    assert context.included_beat_ts == [6, 10]


def test_same_inputs_give_the_same_context():
    supporting = [Supporting(weight=1.0, beat_ts=(2,)), Supporting(weight=1.0, beat_ts=(5,))]

    first = bounded_context(10, VISIBLE, supporting, recent_beats=2, top_hypotheses=1)
    second = bounded_context(10, VISIBLE, list(supporting), recent_beats=2, top_hypotheses=1)

    assert first == second
    assert first.included_beat_ts == [2, 9, 10]


@pytest.mark.django_db
def test_builder_only_feeds_beats_visible_to_the_player(chronicle, players, entity_factory, beat_factory):
    anna, ben = players
    mira, aldric = entity_factory(canonical_name="Mira"), entity_factory(canonical_name="Aldric")
    beat_factory("trusts", who=mira, whom=aldric, players=[anna, ben], text="Mira trusts Aldric.")
    beat_factory("is", who=aldric, trait="a smuggler", players=[anna], text="Aldric was a smuggler.")
    beat_factory("is", who=aldric, trait="nervous", players=[anna, ben], text="Aldric is nervous.")
    builder = RecentAndSupportingBeats(recent_beats=10, top_hypotheses=3)

    for_ben = builder.build(chronicle, ben, t=3, supporting=[])
    for_anna = builder.build(chronicle, anna, t=3, supporting=[])

    assert [beat.text for beat in for_ben.beats] == ["Mira trusts Aldric.", "Aldric is nervous."]
    assert for_anna.included_beat_ts == [1, 2, 3]


@pytest.mark.django_db
def test_beats_without_a_note_are_phrased_from_their_predicate(
    chronicle, players, entity_factory, beat_factory
):
    mira, aldric = entity_factory(canonical_name="Mira"), entity_factory(canonical_name="Aldric")
    beat_factory("trusts", who=mira, whom=aldric, players=players)

    context = RecentAndSupportingBeats(recent_beats=5, top_hypotheses=1).build(
        chronicle, None, t=1, supporting=[]
    )

    assert [beat.text for beat in context.beats] == ["Mira trusts Aldric."]


def test_registry_builds_the_default_context_builder():
    assert isinstance(di.make("ContextBuilder"), RecentAndSupportingBeats)
