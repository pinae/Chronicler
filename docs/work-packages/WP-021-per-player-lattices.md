# WP-021: Per-player lattices

**Milestone:** M4 (§9.3) · **Serves:** RQ1, RQ2

## Goal
The matcher can run with a player scope filter, so a player's private beats complete schemas
only in that player's view.

## Acceptance criteria
- `Hypothesis` gains a nullable `for_player` reference; empty means the unfiltered lattice.
- A matcher run `for_player` considers only beats in `visible_to(player, t)` and stores its
  hypotheses with that `for_player`.
- A private backstory beat completes a schema in that player's lattice, and not in another
  player's. (The unfiltered lattice is the GM's view of every beat, so it sees the backstory too.)
- `Lattice.at(chronicle, t, for_player=...)` obeys the same replay guarantee as WP-020.

## Dependencies
WP-014, WP-020.

## Out of scope
Per-player screens (WP-036).

## Notes
- Decision (user, 2026-10-03): add the nullable `for_player` field. It mirrors
  `Expectation.for_player` and lets per-player hypotheses have expectations of their own.
- The unfiltered lattice consumes every beat (the GM's view); `scope` patterns restrict where a
  schema needs audience knowledge.

## Status
done

## Summary
`Hypothesis.for_player` (decision of 2026-10-03) separates lattices: empty for the unfiltered (GM)
lattice, set for one player's. `StoredMatcher(chronicle, for_player=…)` skips beats the player never
saw and matches `players_know` patterns against that player. Its constraints use
`StoredChronicleFacts(chronicle, for_player)`, which only counts character knowledge conveyed by
beats the player saw and locations from `is_at` beats the player saw. `Lattice.at(…, for_player=…)`
reads one lattice. In the `backstory` story, Anna's private beat completes the betrayal in her
lattice and the GM's but not in Ben's, and her lattice obeys the replay guarantee.
