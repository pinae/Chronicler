import pytest

from evaluation.metrics import Share, calibration, largest_surprise_t, retrospective_fit, surprise_curve
from evaluation.tests.synthetic_runs import run_file, with_truth

EMPTY_RUN = run_file(10, [])


class TestRetrospectiveFit:
    def test_retrospective_fit_is_the_share_of_dormant_beats_that_favour_the_truth(self):
        run = with_truth(EMPTY_RUN, log_bayes_factors=[(4, 0.7), (5, -0.2), (6, 0.0), (8, 1.5)])

        assert retrospective_fit(run) == Share(2, 4)

    def test_without_bayes_factors_retrospective_fit_is_not_available(self):
        assert retrospective_fit(with_truth(EMPTY_RUN, log_bayes_factors=None)).value is None
        assert retrospective_fit(EMPTY_RUN).value is None


class TestSurpriseCurve:
    def test_the_surprise_curve_is_the_change_in_belief_from_one_beat_to_the_next(self):
        run = with_truth(EMPTY_RUN, beliefs=[(2, 0.25), (3, 0.25), (5, 0.5), (10, 0.875)])

        assert surprise_curve(run) == [(3, 0.0), (5, 0.25), (10, 0.375)]

    def test_the_largest_surprise_is_the_largest_rise_in_belief(self):
        run = with_truth(EMPTY_RUN, beliefs=[(2, 0.25), (3, 0.75), (4, 0.25), (10, 0.75)])

        assert largest_surprise_t(run) == 3  # ties: the earliest

    def test_without_beliefs_there_is_no_surprise_curve(self):
        assert surprise_curve(EMPTY_RUN) == []
        assert largest_surprise_t(with_truth(EMPTY_RUN, beliefs=[(2, 0.5)])) is None


class TestCalibration:
    def test_calibration_is_the_brier_score_of_the_readouts_against_the_annotated_beliefs(self):
        exact = ({"aldric": 0.5, "none": 0.5}, {"aldric": 0.5, "none": 0.5})
        off = ({"aldric": 1.0, "none": 0.0}, {"aldric": 0.5, "none": 0.5})
        run = with_truth(EMPTY_RUN, reader_beliefs=[exact, off])

        assert calibration(run) == pytest.approx((0.0 + 0.5) / 2)

    def test_without_annotated_beliefs_calibration_is_not_available(self):
        assert calibration(with_truth(EMPTY_RUN)) is None
        assert calibration(EMPTY_RUN) is None
