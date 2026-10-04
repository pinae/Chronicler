"""What narrating a beat next would do to a lattice, without keeping any of it.

The candidate beat goes through the same path as a narrated one (validation, scope, Fill and
Maintain), inside a transaction that is always rolled back. That way the dry run cannot drift from
what narrating the beat would really do."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from django.db import transaction
from django.db.models import Max

from chronicle.beat_log import BeatDraft, append_beat
from chronicle.models import Chronicle, Player, Utterance
from matching.engine import COMPLETE, MERGED, PRUNED, REFUTED, HypothesisState, StepResult
from matching.store import StoredMatcher
from schemas.vocabulary import default_vocabulary

STATUS_CHANGES = {COMPLETE: "completed", REFUTED: "refuted", MERGED: "merged", PRUNED: "pruned"}


@dataclass(frozen=True)
class CandidateBeat:
    pred: str
    args: Mapping[str, Any]
    text: str = ""
    characters_present: Sequence[int] = ()
    players_present: Sequence[int] = ()


@dataclass(frozen=True)
class Effect:
    """How one hypothesis would change. `hypothesis_id` and `weight_before` are None for a
    hypothesis the beat would create."""

    hypothesis_id: int | None
    schema_slug: str
    binding: dict[str, int | None]
    changes: list[str]
    status: str
    filled_step: str | None
    weight_before: float | None
    weight_after: float
    refines: int | None


@dataclass(frozen=True)
class Before:
    status: str
    weight: float


def dry_run(chronicle: Chronicle, candidate: CandidateBeat, for_player: Player | None = None) -> list[Effect]:
    """The effects on the unfiltered lattice, or on `for_player`'s lattice, of narrating the
    candidate as the next beat. Raises the errors appending it would raise."""
    # Appending would quarantine an unknown predicate, which no schema matches: say so instead.
    default_vocabulary().validate_args(candidate.pred, candidate.args)
    with transaction.atomic():
        beat = append_beat(chronicle, draft_of(chronicle, candidate))
        matcher = StoredMatcher(chronicle, for_player)
        before = {
            state: Before(state.status, matcher.engine.weight(state)) for state in matcher.engine.hypotheses
        }
        result = matcher.step(beat)
        effects = effects_of(result, before, matcher, beat.t)
        transaction.set_rollback(True)
    return effects


def draft_of(chronicle: Chronicle, candidate: CandidateBeat) -> BeatDraft:
    return BeatDraft(
        pred=candidate.pred,
        args=candidate.args,
        source_utterance=placeholder_utterance(chronicle),
        text=candidate.text,
        characters_present=candidate.characters_present,
        players_present=candidate.players_present,
    )


def placeholder_utterance(chronicle: Chronicle) -> Utterance:
    latest_order = chronicle.utterances.aggregate(latest=Max("order"))["latest"] or 0
    return Utterance.objects.create(chronicle=chronicle, order=latest_order + 1, text="(dry run)")


def effects_of(
    result: StepResult, before: Mapping[HypothesisState, Before], matcher: StoredMatcher, beat_t: int
) -> list[Effect]:
    existing = [effect_on(state, before[state], matcher, beat_t) for state in result.changed]
    created = [effect_on(state, None, matcher, beat_t) for state in result.new]
    return existing + created


def effect_on(state: HypothesisState, before: Before | None, matcher: StoredMatcher, beat_t: int) -> Effect:
    filled_step = next((fill.step_id for fill in state.fills if fill.beat_t == beat_t), None)
    return Effect(
        # The ids of hypotheses the beat would create are rolled back with them.
        hypothesis_id=state.record_id if before else None,
        schema_slug=state.schema.slug,
        binding=dict(state.binding),
        changes=changes_of(state, before, filled_step),
        status=state.status,
        filled_step=filled_step,
        weight_before=before.weight if before else None,
        weight_after=matcher.engine.weight(state),
        # Only stored hypotheses are refined, so this id survives the rollback.
        refines=state.refines.record_id if state.refines else None,
    )


def changes_of(state: HypothesisState, before: Before | None, filled_step: str | None) -> list[str]:
    if before is None:
        changes = ["refined" if state.refines else "seeded"]
    else:
        changes = ["filled"] if filled_step else []
    status_before = before.status if before else None
    if state.status != status_before and state.status in STATUS_CHANGES:
        changes.append(STATUS_CHANGES[state.status])
    return changes
