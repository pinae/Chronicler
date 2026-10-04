import json

import pytest

from evaluation.ground_truth import GroundTruth, TrueHypothesis
from evaluation.metrics import Share, coverage, first_held_t, lead_time, twist_recall, voiced_agreement
from evaluation.replay import build_run, replay_story
from evaluation.tests.synthetic_runs import (
    ALDRIC,
    ALDRIC_BETRAYS_MIRA,
    EDDA,
    MIRA,
    SEAL,
    beat,
    hypothesis,
    run_file,
)

TRUTH = ALDRIC_BETRAYS_MIRA  # reveal_t = 10


class TestTwistRecall:
    def test_the_twist_is_recalled_while_the_true_hypothesis_is_live(self):
        run = run_file(10, [(range(3, 11), hypothesis(1, ALDRIC, MIRA))])

        assert twist_recall(run, TRUTH, k=1) is True
        assert twist_recall(run, TRUTH, k=5) is True

    def test_the_twist_is_not_recalled_after_the_true_hypothesis_was_refuted(self):
        run = run_file(
            10,
            [
                (range(3, 7), hypothesis(1, ALDRIC, MIRA)),
                (range(7, 11), hypothesis(1, ALDRIC, MIRA, status="refuted")),
            ],
        )

        assert twist_recall(run, TRUTH, k=1) is False
        assert twist_recall(run, TRUTH, k=5) is True

    def test_recall_before_the_story_began_is_not_available(self):
        run = run_file(10, [(range(3, 11), hypothesis(1, ALDRIC, MIRA))])

        assert twist_recall(run, TRUTH, k=20) is None

    def test_a_more_specific_hypothesis_holds_the_truth(self):
        run = run_file(10, [(range(0, 11), hypothesis(1, ALDRIC, MIRA, SEAL))])

        assert twist_recall(run, TRUTH, k=1) is True

    def test_a_complete_hypothesis_holds_the_truth(self):
        run = run_file(10, [(range(0, 11), hypothesis(1, ALDRIC, MIRA, status="complete"))])

        assert twist_recall(run, TRUTH, k=1) is True

    @pytest.mark.parametrize(
        "near_miss",
        [
            hypothesis(1, ALDRIC, None),
            hypothesis(1, ALDRIC, EDDA),
            hypothesis(1, ALDRIC, MIRA, schema="heist"),
            hypothesis(1, ALDRIC, MIRA, status="pruned"),
            hypothesis(1, ALDRIC, MIRA, status="merged"),
        ],
        ids=["victim open", "other victim", "other schema", "pruned", "merged"],
    )
    def test_near_misses_do_not_hold_the_truth(self, near_miss):
        run = run_file(10, [(range(0, 11), near_miss)])

        assert twist_recall(run, TRUTH, k=1) is False

    def test_recall_is_measured_in_the_chosen_audiences_lattice(self):
        run = run_file(10, [(range(0, 11), hypothesis(1, ALDRIC, MIRA))], audience="Ben")

        assert twist_recall(run, TRUTH, k=1, audience="Ben") is True


class TestLeadTime:
    def test_lead_time_counts_the_beats_from_the_first_holding_to_the_reveal(self):
        run = run_file(
            10,
            [
                (range(3, 5), hypothesis(1, ALDRIC, MIRA)),
                (range(5, 11), hypothesis(1, ALDRIC, MIRA, status="refuted")),
                (range(8, 11), hypothesis(2, ALDRIC, MIRA, SEAL)),
            ],
        )

        assert first_held_t(run, TRUTH) == 3
        assert lead_time(run, TRUTH) == 7

    def test_a_truth_never_held_before_the_reveal_has_no_lead_time(self):
        run = run_file(12, [(range(11, 13), hypothesis(1, ALDRIC, MIRA))])

        assert first_held_t(run, TRUTH) is None
        assert lead_time(run, TRUTH) is None


class TestCoverage:
    def test_coverage_counts_beats_that_fill_a_step_of_any_hypothesis_ever(self):
        beats = [beat(1), beat(2), beat(3), beat(4, quarantined=True)]
        refuted = hypothesis(1, ALDRIC, MIRA, status="refuted", fills=(("trust", 1), ("harm", 3)))
        live = hypothesis(2, EDDA, MIRA, fills=(("trust", 1),))
        run = run_file(4, [(range(0, 5), refuted), (range(0, 5), live)], beats=beats)

        result = coverage(run)

        assert result.filling == Share(2, 4)
        assert result.quarantined == Share(1, 4)
        assert (result.filling.value, result.quarantined.value) == (0.5, 0.25)

    def test_a_run_without_beats_has_no_coverage(self):
        run = run_file(0, [], beats=[])

        assert coverage(run).filling.value is None


class TestVoicedAgreement:
    def test_a_theory_agrees_when_the_engine_ranks_a_matching_reading_in_its_top_k(self):
        voiced = hypothesis(1, ALDRIC, created_at_t=4, voiced_by=70, voiced_in=3, voiced_at_t=4)
        engine_reading = hypothesis(2, ALDRIC, MIRA, weight=-1.5, created_at_t=2, fills=(("trust", 2),))
        stronger = hypothesis(3, EDDA, MIRA, weight=-1.0, created_at_t=3, fills=(("trust", 3), ("trust", 4)))
        run = run_file(6, [(range(4, 7), voiced), (range(2, 7), engine_reading), (range(3, 7), stronger)])

        assert voiced_agreement(run, k=2) == Share(1, 1)
        assert voiced_agreement(run, k=1) == Share(0, 1)

    def test_a_theory_backed_by_no_beat_does_not_count_as_the_engines_reading(self):
        voiced = hypothesis(1, ALDRIC, MIRA, created_at_t=4, voiced_by=70, voiced_in=3, voiced_at_t=4)
        run = run_file(6, [(range(4, 7), voiced)])

        assert voiced_agreement(run, k=5) == Share(0, 1)

    def test_a_theory_that_marked_an_engine_hypothesis_agrees_if_that_hypothesis_is_ranked(self):
        marked = hypothesis(
            1, ALDRIC, MIRA, created_at_t=2, fills=(("trust", 2),), voiced_by=70, voiced_in=3, voiced_at_t=5
        )
        run = run_file(6, [(range(2, 7), marked)])

        assert voiced_agreement(run, k=1) == Share(1, 1)

    def test_each_theory_is_judged_once_at_the_t_it_was_voiced(self):
        """After a merge the survivor carries the same theory (same utterance) from a later t."""
        voiced = hypothesis(1, ALDRIC, MIRA, created_at_t=2, voiced_by=70, voiced_in=3, voiced_at_t=2)
        survivor = hypothesis(
            2, ALDRIC, MIRA, created_at_t=1, fills=(("trust", 1),), voiced_by=70, voiced_in=3, voiced_at_t=5
        )
        run = run_file(6, [(range(2, 7), voiced), (range(1, 7), survivor)])

        assert voiced_agreement(run, k=1) == Share(1, 1)

    def test_without_voiced_theories_agreement_is_not_available(self):
        run = run_file(6, [(range(0, 7), hypothesis(1, ALDRIC, MIRA, fills=(("trust", 1),)))])

        assert voiced_agreement(run, k=5).value is None


@pytest.mark.django_db
def test_the_metrics_read_a_run_file_written_by_replay():
    steward = replay_story("steward", reader=None, per_player=True)
    run = json.loads(json.dumps(build_run(steward, "steward", audiences=[None, *steward.players.all()])))
    truth = GroundTruth(
        reveal_t=22,
        true_hypothesis=TrueHypothesis(schema="betrayal", binding={"T": "aldric", "V": "mira"}),
        dormant_window=(8, 21),
    )

    assert twist_recall(run, truth, k=5) is True
    assert lead_time(run, truth) == 20  # Mira trusts Aldric at t=2
    assert voiced_agreement(run, k=1, audience="Anna") == Share(1, 1)
    assert coverage(run).quarantined == Share(0, 24)
