"""What the GM was shown, and whether they acted on it (RQ2, concept §11 R4).

A tried beat was acted on when the same beat (predicate and arguments) was narrated from the t it
was tried for on. An expected candidate was acted on when a later beat filled the step the audience
was asked about, with that candidate in the role, in the same lattice."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from chronicle.models import Chronicle
from gm_ui.models import UsageEvent
from matching.models import Expectation, Hypothesis, StepFill
from reader.expectations import latest_expectations

SUCCESS = 200


@dataclass(frozen=True)
class DryRunOutcome:
    t: int  # the t the tried beat would have had
    pred: str
    args: dict[str, Any]
    acted_on_t: int | None


@dataclass(frozen=True)
class ExpectationOutcome:
    asked_at_t: int
    question: str
    candidate: str
    p: float
    acted_on_t: int | None


def shown(chronicle: Chronicle, view: str) -> list[UsageEvent]:
    """Requests for the view that the engine answered: outputs the GM actually saw."""
    events = UsageEvent.objects.filter(chronicle=chronicle, view=view).order_by("created_at", "pk")
    return [event for event in events if event.params.get("status") == SUCCESS]


# Dry runs


def dry_run_outcomes(chronicle: Chronicle) -> list[DryRunOutcome]:
    outcomes = []
    for event in shown(chronicle, "dry_run_beat"):
        tried = event.params["body"]
        outcomes.append(
            DryRunOutcome(
                t=event.t or 0,
                pred=tried["pred"],
                args=tried["args"],
                acted_on_t=first_narrated_t(chronicle, tried["pred"], tried["args"], event.t or 0),
            )
        )
    return outcomes


def first_narrated_t(chronicle: Chronicle, pred: str, args: Mapping[str, Any], from_t: int) -> int | None:
    beats = chronicle.beats.filter(pred=pred, t__gte=from_t).order_by("t")
    return next((beat.t for beat in beats if beat.args == args), None)


# Expectations


def expectation_outcomes(chronicle: Chronicle) -> list[ExpectationOutcome]:
    """One outcome per candidate of every readout shown, however often it was shown."""
    seen: dict[tuple[int, str], ExpectationOutcome] = {}
    for event in shown(chronicle, "list_expectations"):
        hypothesis = Hypothesis.objects.get(pk=event.params["hypothesis_id"])
        for expectation in latest_expectations(hypothesis, event.t):
            for candidate in expectation.candidates:
                if candidate.get("null") or (expectation.pk, candidate["label"]) in seen:
                    continue
                seen[(expectation.pk, candidate["label"])] = ExpectationOutcome(
                    asked_at_t=expectation.computed_at_t,
                    question=expectation.question,
                    candidate=candidate["text"],
                    p=candidate["p"],
                    acted_on_t=first_fill_t(expectation, candidate["binding_delta"]),
                )
    return list(seen.values())


def first_fill_t(expectation: Expectation, binding_delta: Mapping[str, int]) -> int | None:
    """The first beat after the readout that filled its step with the candidate in its role."""
    asked = expectation.hypothesis
    wanted = {
        **{role: entity for role, entity in asked.binding.items() if entity is not None},
        **binding_delta,
    }
    fills = StepFill.objects.filter(
        hypothesis__chronicle=asked.chronicle,
        hypothesis__schema=asked.schema,
        hypothesis__for_player=asked.for_player,
        step=expectation.step,
        beat__t__gt=expectation.computed_at_t,
    ).select_related("hypothesis", "beat")
    for fill in fills.order_by("beat__t"):
        if all(fill.hypothesis.binding.get(role) == entity for role, entity in wanted.items()):
            return fill.beat.t
    return None
