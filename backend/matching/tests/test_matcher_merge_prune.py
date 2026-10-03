import pytest

from matching.engine import Fill, HypothesisState, IncrementalMatcher, MatcherConfig
from matching.models import Hypothesis
from matching.store import StoredMatcher
from matching.tests.betrayal_world import (
    ALDRIC,
    KEY,
    LETTER,
    MIRA,
    RONAN,
    WORLD,
    beat,
    betrayal,
    entity,
    trusts,
)
from schemas.library import load_library


def betrays(t_entity, s_entity=None, fills=(), created_at_t=1, voiced_by=None):
    return HypothesisState(
        schema=betrayal(),
        binding={"T": t_entity, "V": MIRA, "S": s_entity},
        created_at_t=created_at_t,
        fills=list(fills),
        voiced_by=voiced_by,
    )


def unrelated_beat(t):
    return beat(t, "is", who=entity(RONAN), trait={"literal": "tired"})


class TestMerging:
    def test_identical_hypotheses_merge_into_the_older_one(self):
        older = betrays(ALDRIC, fills=[Fill("trust", 1)], created_at_t=1)
        younger = betrays(ALDRIC, fills=[Fill("trust", 1)], created_at_t=3)
        matcher = IncrementalMatcher([betrayal()], [older, younger])

        result = matcher.step(unrelated_beat(4), WORLD)

        assert (younger.status, younger.merged_into, younger.status_changed_at_t) == ("merged", older, 4)
        assert older.status == "live"
        assert younger in result.changed
        assert younger in matcher.hypotheses

    def test_same_binding_with_different_fills_does_not_merge(self):
        first = betrays(ALDRIC, fills=[Fill("trust", 1)])
        second = betrays(ALDRIC, fills=[Fill("trust", 2)])
        matcher = IncrementalMatcher([betrayal()], [first, second])

        matcher.step(unrelated_beat(4), WORLD)

        assert first.status == second.status == "live"

    def test_survivor_keeps_who_voiced_the_merged_hypothesis(self):
        older = betrays(ALDRIC, fills=[Fill("trust", 1)], created_at_t=1)
        voiced = betrays(ALDRIC, fills=[Fill("trust", 1)], created_at_t=2, voiced_by=7)
        matcher = IncrementalMatcher([betrayal()], [older, voiced])

        matcher.step(unrelated_beat(4), WORLD)

        assert older.voiced_by == 7

    def test_merged_hypothesis_takes_no_further_fills(self):
        older = betrays(ALDRIC, fills=[Fill("trust", 1)], created_at_t=1)
        younger = betrays(ALDRIC, fills=[Fill("trust", 1)], created_at_t=3)
        matcher = IncrementalMatcher([betrayal()], [older, younger])
        matcher.step(unrelated_beat(4), WORLD)

        matcher.step(trusts(5, MIRA, ALDRIC), WORLD)

        assert younger.fill_ts("trust") == [1]
        assert older.fill_ts("trust") == [1, 5]


class TestPruning:
    def test_hypothesis_below_the_weight_floor_is_pruned(self):
        matcher = IncrementalMatcher([betrayal()], config=MatcherConfig(weight_floor=-1.0))

        [seeded] = matcher.step(trusts(2, MIRA, ALDRIC), WORLD).new

        assert (seeded.status, seeded.status_changed_at_t) == ("pruned", 2)

    def test_voiced_hypothesis_is_never_pruned(self):
        voiced = betrays(ALDRIC, voiced_by=7)
        matcher = IncrementalMatcher([betrayal()], [voiced], config=MatcherConfig(weight_floor=-1.0))

        matcher.step(unrelated_beat(2), WORLD)

        assert voiced.status == "live"

    def test_lowest_weighted_hypotheses_beyond_the_maximum_per_schema_are_pruned(self):
        strong = betrays(ALDRIC, fills=[Fill("trust", 1), Fill("harm", 2)], created_at_t=1)
        medium = betrays(RONAN, fills=[Fill("trust", 1)], created_at_t=1)
        weak = betrays(None, created_at_t=1)
        matcher = IncrementalMatcher(
            [betrayal()], [weak, medium, strong], config=MatcherConfig(max_live_per_schema=2)
        )

        result = matcher.step(unrelated_beat(5), WORLD)

        assert [weak.status, medium.status, strong.status] == ["pruned", "live", "live"]
        assert result.changed == [weak]

    def test_ties_at_the_maximum_prune_the_newest_first(self):
        first = betrays(ALDRIC, s_entity=KEY, created_at_t=1)
        second = betrays(ALDRIC, s_entity=LETTER, created_at_t=2)
        matcher = IncrementalMatcher(
            [betrayal()], [second, first], config=MatcherConfig(max_live_per_schema=1)
        )

        matcher.step(unrelated_beat(5), WORLD)

        assert [first.status, second.status] == ["live", "pruned"]


@pytest.mark.django_db
def test_merge_and_prune_are_stored(chronicle, entity_factory, beat_factory, settings):
    settings.MATCHER_MAX_LIVE_PER_SCHEMA = 1
    load_library()
    mira, aldric, ronan = entity_factory(), entity_factory(), entity_factory()
    StoredMatcher(chronicle).step(beat_factory("trusts", who=mira, whom=aldric))
    StoredMatcher(chronicle).step(beat_factory("trusts", who=mira, whom=aldric))

    StoredMatcher(chronicle).step(beat_factory("trusts", who=mira, whom=ronan))

    statuses = dict(Hypothesis.objects.values_list("binding__T", "status"))
    assert statuses == {aldric.id: "live", ronan.id: "pruned"}
