"""Beats as plain, immutable data, so matching runs on in-memory objects (concept §12)."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from chronicle.models import QUARANTINE_TAG, Beat


@dataclass(frozen=True)
class PlainBeat:
    t: int
    pred: str
    args: Mapping[str, Any]
    tags: tuple[str, ...] = ()
    # Players granted the beat by its own t: what `scope: {players_know: true}` patterns check.
    known_by_players: frozenset[int] = field(default_factory=frozenset)

    @property
    def is_quarantined(self) -> bool:
        return QUARANTINE_TAG in self.tags

    @classmethod
    def from_model(cls, beat: Beat, as_of: int | None = None) -> "PlainBeat":
        """`as_of`: who knows the beat at that t (default: at the beat's own t)."""
        known_until = beat.t if as_of is None else as_of
        known_by_players = frozenset(
            grant.player_id
            for grant in beat.grants.all()
            if grant.player_id is not None and grant.t <= known_until
        )
        return cls(
            t=beat.t, pred=beat.pred, args=beat.args, tags=tuple(beat.tags), known_by_players=known_by_players
        )
