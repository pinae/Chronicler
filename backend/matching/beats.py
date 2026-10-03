"""Beats as plain, immutable data, so matching runs on in-memory objects (concept §12)."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from chronicle.models import QUARANTINE_TAG, Beat


@dataclass(frozen=True)
class PlainBeat:
    t: int
    pred: str
    args: Mapping[str, Any]
    tags: tuple[str, ...] = ()

    @property
    def is_quarantined(self) -> bool:
        return QUARANTINE_TAG in self.tags

    @classmethod
    def from_model(cls, beat: Beat) -> "PlainBeat":
        return cls(t=beat.t, pred=beat.pred, args=beat.args, tags=tuple(beat.tags))
