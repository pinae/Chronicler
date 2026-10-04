import pytest

from evaluation.metrics import Share
from evaluation.outlets import OutletLattice, Reading, completion, step_overlap, suspect_weight_share
from matching.engine import Fill
from schemas.library import read_library

BLAME = next(
    schema for schema in read_library() if schema.slug == "blame"
)  # required: accusation, motive, condemnation
HOLT_BLAMED = (("O", "outlet"), ("A", "holt"), ("V", "petra"))
ROSS_BLAMED = (("O", "outlet"), ("A", "ross"), ("V", "petra"))


def by_herald(binding):
    return tuple((role, "herald" if role == "O" else slug) for role, slug in binding)


def reading(binding, *fills, status="live", weight=0.0):
    return Reading(
        schema="blame",
        binding=binding,
        status=status,
        weight=weight,
        fills=tuple(Fill(s, t) for s, t in fills),
    )


def outlet(*readings, suspect_ts=()):
    return OutletLattice(outlet="The Courier", readings=readings, suspect_ts=frozenset(suspect_ts))


class TestCompletion:
    def test_completion_is_the_share_of_required_steps_the_best_reading_filled(self):
        courier = outlet(
            reading(HOLT_BLAMED, ("accusation", 1), ("motive", 4), ("sympathy", 5)),
            reading(ROSS_BLAMED, ("accusation", 2)),
        )

        assert completion(courier, BLAME) == Share(2, 3)

    def test_refuted_and_pruned_readings_do_not_count(self):
        courier = outlet(reading(HOLT_BLAMED, ("accusation", 1), ("motive", 4), status="refuted"))

        assert completion(courier, BLAME) == Share(0, 3)


class TestStepOverlap:
    def test_overlap_compares_the_steps_both_outlets_filled_for_the_same_reading(self):
        """Each outlet is the source of its own claims, so the source role is left out."""
        courier = outlet(reading(HOLT_BLAMED, ("accusation", 1), ("motive", 4), ("condemnation", 6)))
        herald = outlet(
            reading(by_herald(HOLT_BLAMED), ("accusation", 2)),
            reading(by_herald(ROSS_BLAMED), ("accusation", 3)),
        )

        # Shared: Holt's accusation. Either: Holt's accusation, motive, condemnation; Ross's accusation.
        assert step_overlap(courier, herald, BLAME) == Share(1, 4)

    def test_outlets_that_filled_nothing_have_no_overlap(self):
        assert step_overlap(outlet(), outlet(), BLAME).value is None


class TestWeightOnSuspectClaims:
    def test_the_share_of_the_strongest_readings_weight_that_rests_on_false_or_unverified_claims(self):
        # accusation 1.0 (t=1, unverified), motive 0.5 (t=4, false), condemnation 1.5 (t=6, unlabeled)
        courier = outlet(
            reading(HOLT_BLAMED, ("accusation", 1), ("motive", 4), ("condemnation", 6), weight=1.0),
            reading(ROSS_BLAMED, ("accusation", 2), weight=-1.0),
            suspect_ts={1, 4, 2},
        )

        assert suspect_weight_share(courier, BLAME, repeat_cap=3) == pytest.approx(1.5 / 3.0)

    def test_without_a_held_reading_no_weight_rests_on_anything(self):
        assert suspect_weight_share(outlet(suspect_ts={1}), BLAME, repeat_cap=3) is None
