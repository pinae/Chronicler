# WP-021: Per-player lattices

**Milestone:** M4 (§9.3) · **Serves:** RQ1, RQ2

## Goal
The matcher can run with a player scope filter, so a player's private beats complete schemas
only in that player's view.

## Acceptance criteria
- A matcher run `for_player` considers only beats in `visible_to(player, t)`.
- A private backstory beat completes a schema in that player's lattice, and not in the table
  lattice or another player's.
- `Lattice.at(chronicle, t, for_player=...)` obeys the same replay guarantee as WP-020.

## Dependencies
WP-014, WP-020.

## Out of scope
Per-player screens (WP-036).

## Notes
- `Hypothesis` has no `for_player` field. Options: add a nullable `for_player` (mirrors
  `Expectation.for_player` and lets per-player hypotheses have expectations), or compute
  per-player lattices on demand without storing them. Recommended: the nullable field.
  Confirm before implementing.
- Make explicit what the unfiltered lattice consumes. Proposed: every beat (the GM's view);
  `scope` patterns restrict where a schema needs audience knowledge.

## Status
open
