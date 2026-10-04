# WP-046: Session transcript importer

**Milestone:** R1 · **Serves:** RQ1

## Goal
Turn recorded play-session transcripts into `session` fixture transcripts.

## Acceptance criteria
- Each turn becomes an utterance whose speaker is the matching player, or the GM (no player).
- Players are created from the transcript's speakers.
- The importer writes `transcript.yaml` and a README skeleton.
- Tested on a short sample transcript.

## Dependencies
WP-029.

## Out of scope
Audio transcription; producing beats (WP-047).

## Notes
- Blocked on input: which transcript format(s) are in use? A sample transcript is needed before
  this package starts.

## Status
done

## Summary
No sample transcript was available, so the importer reads the common denominator of chat logs and
diarized transcriptions: one turn per line, `Speaker: text`, optionally after a `[hh:mm:ss]`
timestamp, continuation lines appended to the previous turn. `manage.py import_session <file>
<slug> --title … [--gm NAME …]` makes every non-GM speaker a player (order of first appearance),
writes the GM's turns as `gm` with `source: {line}`, and a README skeleton. When real transcripts
arrive in another format, add a parser that produces the same `SessionTranscript`. Usage doc:
`docs/usage/import-session.md`.
