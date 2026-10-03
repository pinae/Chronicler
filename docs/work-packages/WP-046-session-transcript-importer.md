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
open
