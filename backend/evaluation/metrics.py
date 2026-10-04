"""Evaluation metrics (concept §9.2) over a run file (docs/run-file-format.md).

Pure functions: a parsed run file and a ground truth in, numbers out. A metric whose inputs are
missing answers None (or a Share without a total) rather than failing."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from itertools import pairwise
from typing import Any

from evaluation.ground_truth import GroundTruth, TrueHypothesis
from matching.engine import COMPLETE, LIVE

ALL = "all"  # the unfiltered lattice; other audiences are player names
HELD = {LIVE, COMPLETE}  # statuses in which the lattice still holds a reading
RECALL_KS = (1, 5, 20)

Run = Mapping[str, Any]
LatticeEntry = Mapping[str, Any]


@dataclass(frozen=True)
class Share:
    count: int
    total: int

    @property
    def value(self) -> float | None:
        return self.count / self.total if self.total else None


@dataclass(frozen=True)
class Coverage:
    filling: Share  # beats that fill at least one step of any hypothesis
    quarantined: Share  # beats whose predicate the vocabulary did not know


def lattice_at(run: Run, t: int, audience: str = ALL) -> list[LatticeEntry]:
    entry = next(entry for entry in run["timeline"] if entry["t"] == t)
    return list(entry["lattice"].get(audience, []))


def last_t(run: Run) -> int:
    return max(entry["t"] for entry in run["timeline"])


# Twist recall and lead time


def twist_recall(run: Run, truth: GroundTruth, k: int, audience: str = ALL) -> bool | None:
    """Did the lattice hold the true hypothesis k beats before the reveal? None before the story."""
    t = truth.reveal_t - k
    if t < 0:
        return None
    return holds_truth(run, truth.true_hypothesis, t, audience)


def first_held_t(run: Run, truth: GroundTruth, audience: str = ALL) -> int | None:
    """The first t, up to the reveal, at which the lattice held the true hypothesis."""
    return next(
        (t for t in range(truth.reveal_t + 1) if holds_truth(run, truth.true_hypothesis, t, audience)), None
    )


def lead_time(run: Run, truth: GroundTruth, audience: str = ALL) -> int | None:
    """How many beats before the reveal the lattice first held the true hypothesis."""
    first_t = first_held_t(run, truth, audience)
    return None if first_t is None else truth.reveal_t - first_t


def holds_truth(run: Run, true_hypothesis: TrueHypothesis, t: int, audience: str) -> bool:
    """A held hypothesis of the true schema binds every role of the truth as the truth does; roles
    the truth leaves out may be bound to anyone or open."""
    entity_ids = {entity["slug"]: int(entity_id) for entity_id, entity in run["entities"].items()}
    if not set(true_hypothesis.binding.values()) <= entity_ids.keys():
        return False
    true_binding = {role: entity_ids[slug] for role, slug in true_hypothesis.binding.items()}
    return any(
        hypothesis["status"] in HELD and reads_as(hypothesis, true_hypothesis.schema, true_binding)
        for hypothesis in lattice_at(run, t, audience)
    )


def reads_as(hypothesis: LatticeEntry, schema: str, binding: Mapping[str, int | None]) -> bool:
    """The hypothesis is of the schema and binds every bound role of `binding` the same way."""
    return hypothesis["schema"] == schema and all(
        hypothesis["binding"].get(role) == entity for role, entity in binding.items() if entity is not None
    )


# Coverage


def coverage(run: Run) -> Coverage:
    beat_ts = {beat["t"] for beat in run["beats"]}
    # The last lattice holds every hypothesis ever made, refuted, pruned and merged ones too.
    filled_ts = {t for hypothesis in lattice_at(run, last_t(run)) for _, t in hypothesis["fills"]}
    return Coverage(
        filling=Share(len(filled_ts & beat_ts), len(beat_ts)),
        quarantined=Share(sum(1 for beat in run["beats"] if beat["quarantined"]), len(beat_ts)),
    )


# Voiced-hypothesis agreement


def voiced_agreement(run: Run, k: int, audience: str = ALL) -> Share:
    """Of the theories players voiced, how many matched a reading among the engine's top k at the
    t they were voiced?"""
    voicings = first_voicings(lattice_at(run, last_t(run), audience))
    agreeing = sum(
        1
        for voiced in voicings
        if any(
            reads_as(reading, voiced["schema"], voiced["binding"])
            for reading in top_readings(lattice_at(run, voiced["voiced_at_t"], audience), k)
        )
    )
    return Share(agreeing, len(voicings))


def first_voicings(hypotheses: Iterable[LatticeEntry]) -> list[LatticeEntry]:
    """One hypothesis per voiced theory (utterance): the one it was voiced as first. Later ones
    carry the same theory after a merge."""
    first: dict[int, LatticeEntry] = {}
    for hypothesis in sorted(
        (h for h in hypotheses if h["voiced_in"] is not None), key=lambda h: h["voiced_at_t"]
    ):
        first.setdefault(hypothesis["voiced_in"], hypothesis)
    return list(first.values())


def top_readings(hypotheses: Iterable[LatticeEntry], k: int) -> list[LatticeEntry]:
    """The engine's k strongest held readings. A hypothesis no beat fills yet exists only because a
    player voiced it, so it is not the engine's reading. Ties: the older first, as when pruning."""
    readings = [h for h in hypotheses if h["status"] in HELD and h["fills"]]
    return sorted(readings, key=lambda h: (-h["weight"], h["created_at_t"]))[:k]


# Reader-based metrics, over the run file's `truth` record (evaluation/truth_readouts.py)


def retrospective_fit(run: Run) -> Share:
    """Of the dormant-window beats the table saw, how many favour the truth over the strongest
    other reading (Bayes factor > 1)? High: the clues were there."""
    bayes_factors = run.get("truth", {}).get("bayes_factors") or []
    favouring = sum(1 for record in bayes_factors if record["log_bayes_factor"] > 0)
    return Share(favouring, len(bayes_factors))


def surprise_curve(run: Run) -> list[tuple[int, float]]:
    """(t, change in the belief in the truth since the previous readout). A good twist rises at
    the reveal, not before."""
    beliefs = sorted(run.get("truth", {}).get("beliefs") or [], key=lambda belief: belief["t"])
    return [(current["t"], current["p"] - previous["p"]) for previous, current in pairwise(beliefs)]


def largest_surprise_t(run: Run) -> int | None:
    """The t of the largest rise in belief in the truth (ties: the earliest)."""
    curve = surprise_curve(run)
    if not curve:
        return None
    return max(curve, key=lambda point: (point[1], -point[0]))[0]


def calibration(run: Run) -> float | None:
    """Brier score of the readouts against the annotated beliefs: the mean, over the annotated
    questions, of the squared differences summed over the answers. 0 is perfect."""
    answered = run.get("truth", {}).get("reader_beliefs") or []
    if not answered:
        return None
    scores = [
        sum((record["readout"].get(answer, 0.0) - p) ** 2 for answer, p in record["annotated"].items())
        for record in answered
    ]
    return sum(scores) / len(scores)
