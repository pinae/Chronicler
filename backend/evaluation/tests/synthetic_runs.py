"""Hand-built run files (docs/run-file-format.md) with known metric values."""

from collections.abc import Sequence
from typing import Any

from evaluation.ground_truth import GroundTruth, TrueHypothesis

ALDRIC, MIRA, EDDA, SEAL = 1, 2, 3, 4
ENTITIES = {
    str(ALDRIC): {"slug": "aldric", "name": "Aldric", "kind": "character"},
    str(MIRA): {"slug": "mira", "name": "Mira", "kind": "character"},
    str(EDDA): {"slug": "edda", "name": "Edda", "kind": "character"},
    str(SEAL): {"slug": "seal", "name": "The family seal", "kind": "secret"},
}
ALDRIC_BETRAYS_MIRA = GroundTruth(
    reveal_t=10,
    true_hypothesis=TrueHypothesis(schema="betrayal", binding={"T": "aldric", "V": "mira"}),
    dormant_window=(4, 9),
)


def hypothesis(
    hypothesis_id: int,
    traitor: int | None,
    victim: int | None = None,
    secret: int | None = None,
    *,
    schema: str = "betrayal",
    status: str = "live",
    weight: float = 0.0,
    created_at_t: int = 0,
    fills: tuple[tuple[str, int], ...] = (),
    voiced_by: int | None = None,
    voiced_in: int | None = None,
    voiced_at_t: int | None = None,
) -> dict[str, Any]:
    return {
        "id": hypothesis_id,
        "schema": schema,
        "binding": {"T": traitor, "V": victim, "S": secret},
        "status": status,
        "weight": weight,
        "created_at_t": created_at_t,
        "status_changed_at_t": None,
        "fills": [list(fill) for fill in fills],
        "refines": None,
        "merged_into": None,
        "refuted_by_t": None,
        "voiced_by": voiced_by,
        "voiced_in": voiced_in,
        "voiced_at_t": voiced_at_t,
    }


def run_file(
    last_t: int,
    held: list[tuple[range, dict[str, Any]]],
    beats: list[dict[str, Any]] | None = None,
    audience: str = "all",
) -> dict[str, Any]:
    """A run whose lattice at t holds every hypothesis whose range contains t."""
    return {
        "format": "chronicler-run/1",
        "story": "synthetic",
        "created_at": "2026-10-04T00:00:00+00:00",
        "reader": None,
        "entities": ENTITIES,
        "beats": beats if beats is not None else [beat(t) for t in range(1, last_t + 1)],
        "timeline": [
            {
                "t": t,
                "lattice": {audience: [entry for during, entry in held if t in during]},
                "expectations": [],
            }
            for t in range(last_t + 1)
        ],
    }


def beat(t: int, quarantined: bool = False, original_pred: str = "adores") -> dict[str, Any]:
    return {
        "t": t,
        "pred": "unknown" if quarantined else "trusts",
        "original_pred": original_pred if quarantined else "",
        "text": f"beat {t}",
        "quarantined": quarantined,
    }


def with_truth(
    run: dict[str, Any],
    beliefs: Sequence[tuple[int, float]] = (),
    log_bayes_factors: Sequence[tuple[int, float]] | None = None,
    reader_beliefs: Sequence[tuple[dict[str, float], dict[str, float]]] = (),
) -> dict[str, Any]:
    """The run with a `truth` record: beliefs as (t, p), Bayes factors as (t, log factor), reader
    beliefs as (annotated, readout)."""
    truth = ALDRIC_BETRAYS_MIRA
    return {
        **run,
        "truth": {
            "reveal_t": truth.reveal_t,
            "schema": truth.true_hypothesis.schema,
            "binding": {"T": ALDRIC, "V": MIRA},
            "dormant_window": list(truth.dormant_window),
            "beliefs": [{"t": t, "p": p, "llm_call": None} for t, p in beliefs],
            "bayes_factors": None
            if log_bayes_factors is None
            else [{"t": t, "log_bayes_factor": factor, "dominant": None} for t, factor in log_bayes_factors],
            "reader_beliefs": [
                {"t": 5, "question": "Who will harm Mira?", "annotated": annotated, "readout": readout}
                for annotated, readout in reader_beliefs
            ],
        },
    }
