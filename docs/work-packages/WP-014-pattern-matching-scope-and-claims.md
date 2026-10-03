# WP-014: Pattern matching with scope and claims

**Milestone:** M4 · **Serves:** RQ1, RQ4

## Goal
Patterns can require that the audience knows a beat, and can match the content of claims while
binding who made them: the hook RQ4 depends on.

## Acceptance criteria
- A pattern with `scope: {players_know: true}` matches only beats in the table view at the beat's
  `t`, or in a given player's view when matching for that player.
- A pattern with `claimed_by: $Source` matches the proposition inside a `says` beat and binds
  `$Source` to the speaker of that `says` beat.
- A pattern with `claimed_by` does not match a beat that is not a claim.
- A pattern without `claimed_by` does not match propositions inside `says` beats: claims never
  count as facts.

## Dependencies
WP-009, WP-013.

## Out of scope
Negation (the "Lie" schema's ¬P); per-player lattices (WP-021).

## Notes
- The last criterion is an interpretation that protects the RQ4 boundary from §1. Confirm it.

## Status
open
