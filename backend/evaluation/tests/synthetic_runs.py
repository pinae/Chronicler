"""Hand-built run files (docs/run-file-format.md) with known metric values."""

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


def beat(t: int, quarantined: bool = False) -> dict[str, Any]:
    return {
        "t": t,
        "pred": "unknown" if quarantined else "trusts",
        "text": f"beat {t}",
        "quarantined": quarantined,
    }
