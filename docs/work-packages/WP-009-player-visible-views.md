# WP-009: Player-visible chronicle views

**Milestone:** M2 · **Serves:** RQ1, RQ2

## Goal
Answer "which beats did this audience member know at time t": the only view of the chronicle
the reader model may ever see.

## Acceptance criteria
- `Chronicle.visible_to(player, t)` returns exactly the beats with a grant for that player at or
  before `t`, ordered by `t`.
- A private backstory beat granted only to player A is in A's view, absent from player B's view,
  and absent from the table view.
- The table view contains the beats granted to every player of the chronicle.
- In a `literature` chronicle, the implicit player's view at `t` is every beat with `t' ≤ t`.
- Every view at `t = 0` is empty.

## Dependencies
WP-008.

## Out of scope
Per-player lattices (WP-021), the chronicle screen (WP-035).

## Notes
- The concept uses "table view" without defining it. Proposed definition: common knowledge,
  i.e. beats granted to every player. Confirm before implementing.

## Status
open
