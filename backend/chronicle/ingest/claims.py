"""Media utterances (concept §9.4, R3): whatever an outlet states is a claim by that outlet, never a
fact. Schemas see it only through `claimed_by` patterns."""

from dataclasses import replace

from chronicle.ingest.interfaces import IngestedBeat, IngestResult
from chronicle.models import Entity, SourceKind


def as_claims(result: IngestResult, outlet: Entity) -> IngestResult:
    return replace(result, beats=tuple(claim_by(outlet, beat) for beat in result.beats))


def claim_by(outlet: Entity, beat: IngestedBeat) -> IngestedBeat:
    """says(who=outlet, what=the statement). A statement already attributed to the outlet stays."""
    speaker = f"@{outlet.slug}"
    if beat.pred == "says" and beat.args.get("who") == speaker:
        return beat
    return IngestedBeat(
        pred="says",
        args={"who": speaker, "what": {"pred": beat.pred, "args": dict(beat.args)}},
        players=beat.players,
        source_kind=SourceKind.CLAIM,
        text=f"{outlet.canonical_name} says: {beat.text}" if beat.text else "",
        tags=beat.tags,
        confidence=beat.confidence,
    )
