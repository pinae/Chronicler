"""The metrics table the evaluate command prints: every §9.2 metric of one run, as text."""

from evaluation.ground_truth import GroundTruth
from evaluation.metrics import (
    RECALL_KS,
    Run,
    Share,
    calibration,
    coverage,
    first_held_t,
    largest_surprise_t,
    lead_time,
    retrospective_fit,
    twist_recall,
    voiced_agreement,
)

NOT_AVAILABLE = "n/a"


def metric_rows(run: Run, truth: GroundTruth | None, audience: str, top_k: int) -> list[tuple[str, str]]:
    """(metric, value) per metric; a metric whose inputs are missing reads n/a."""
    beats_coverage = coverage(run)
    return [
        *((f"twist recall at reveal - {k}", recall_text(run, truth, k, audience)) for k in RECALL_KS),
        ("lead time", lead_time_text(run, truth, audience)),
        ("coverage: beats filling a step", share_text(beats_coverage.filling)),
        ("coverage: beats quarantined", share_text(beats_coverage.quarantined)),
        (f"voiced agreement (top {top_k})", share_text(voiced_agreement(run, top_k, audience))),
        ("retrospective fit", share_text(retrospective_fit(run))),
        ("largest surprise", surprise_text(run)),
        ("calibration (Brier score)", calibration_text(run)),
    ]


def recall_text(run: Run, truth: GroundTruth | None, k: int, audience: str) -> str:
    recalled = twist_recall(run, truth, k, audience) if truth else None
    if recalled is None:
        return NOT_AVAILABLE
    return "yes" if recalled else "no"


def lead_time_text(run: Run, truth: GroundTruth | None, audience: str) -> str:
    beats = lead_time(run, truth, audience) if truth else None
    if truth is None or beats is None:
        return NOT_AVAILABLE
    return f"{beats} beats (first held at t = {first_held_t(run, truth, audience)})"


def share_text(share: Share) -> str:
    if share.value is None:
        return NOT_AVAILABLE
    return f"{share.value:.0%} ({share.count} of {share.total})"


def surprise_text(run: Run) -> str:
    t = largest_surprise_t(run)
    if t is None:
        return NOT_AVAILABLE
    return f"at t = {t} (reveal at t = {run['truth']['reveal_t']})"


def calibration_text(run: Run) -> str:
    score = calibration(run)
    return NOT_AVAILABLE if score is None else f"{score:.3f}"


def table(rows: list[tuple[str, str]]) -> str:
    width = max(len(metric) for metric, _ in [("Metric", ""), *rows])
    lines = [
        f"{'Metric'.ljust(width)}  Value",
        *(f"{metric.ljust(width)}  {value}" for metric, value in rows),
    ]
    return "\n".join(lines)
