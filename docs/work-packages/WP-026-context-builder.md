# WP-026: Context builder

**Milestone:** M6 (§9.3) · **Serves:** RQ1

## Goal
Feed the reader model a bounded, player-visible context that fits the model's window, even for
long stories.

## Acceptance criteria
- `ContextBuilder` is a `typing.Protocol`; the default implementation returns the most recent
  N beats verbatim plus the beats that fill steps of the top-k live hypotheses (N and k from
  settings), in `t` order and without duplicates.
- It reports which beats it included.
- It never includes a beat outside `visible_to(player, t)`.
- The same inputs always give the same context.

## Dependencies
WP-020, WP-024.

## Out of scope
Prose vs. canonical context experiments (§13).

## Status
open
