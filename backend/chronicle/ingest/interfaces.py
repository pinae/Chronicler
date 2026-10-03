"""Ingest (concept §3): one utterance in, beat drafts out. All fuzziness lives here; the matcher is exact.

Ingesters refer to entities by slug in the compact argument notation of fixture stories ("@aldric",
"#13" for the beat at t=13, nested {pred, args} for propositions) and report entities they mention
for the first time. The pipeline creates those entities and appends the beats.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol

from chronicle.models import Chronicle, Utterance


@dataclass(frozen=True)
class IngestedBeat:
    pred: str
    args: Mapping[str, Any]
    present: tuple[str, ...] = ()  # slugs of the characters who witness the beat
    players: tuple[str, ...] | None = None  # names of the players who learn it; None: every player
    source_kind: str = "narration"
    text: str = ""
    tags: tuple[str, ...] = ()
    confidence: float = 1.0


@dataclass(frozen=True)
class IngestedTheory:
    schema: str
    binding: Mapping[str, str]  # role -> entity slug


@dataclass(frozen=True)
class NewEntity:
    slug: str
    kind: str
    name: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class IngestResult:
    beats: tuple[IngestedBeat, ...] = ()
    theories: tuple[IngestedTheory, ...] = ()
    new_entities: tuple[NewEntity, ...] = field(default_factory=tuple)


class Ingester(Protocol):
    def ingest(self, chronicle: Chronicle, utterance: Utterance) -> IngestResult: ...
