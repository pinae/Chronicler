"""Recorded play sessions as `session` story transcripts (concept §9.1, R1).

The format is one turn per line, `Speaker: text`, optionally after a `[hh:mm:ss]` timestamp; lines
without a speaker continue the previous turn. It is the common denominator of chat logs and
diarized transcriptions; other formats can be converted to it."""

import re
from collections.abc import Collection
from dataclasses import dataclass

TURN = re.compile(r"^(\[[\d:.]+\]\s*)?(?P<speaker>[^:\[\]]{1,40}):\s*(?P<text>.*)$")


class TranscriptFormatError(ValueError):
    pass


@dataclass(frozen=True)
class SessionTurn:
    speaker: str | None  # a player's name; None for the GM
    text: str
    line: int  # where the turn starts in the transcript


@dataclass(frozen=True)
class SessionTranscript:
    turns: list[SessionTurn]

    @property
    def players(self) -> list[str]:
        return list(dict.fromkeys(turn.speaker for turn in self.turns if turn.speaker is not None))


def parse_session(text: str, gm_names: Collection[str]) -> SessionTranscript:
    turns: list[tuple[str | None, list[str], int]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        turn = TURN.match(line.strip())
        if turn is not None:
            speaker = turn.group("speaker").strip()
            turns.append((None if speaker in gm_names else speaker, [turn.group("text")], number))
        elif turns:
            turns[-1][1].append(line.strip())
        else:
            raise TranscriptFormatError(f"line {number}: expected 'Speaker: text'")
    return SessionTranscript(
        turns=[
            SessionTurn(speaker, " ".join(" ".join(lines).split()), line) for speaker, lines, line in turns
        ]
    )
