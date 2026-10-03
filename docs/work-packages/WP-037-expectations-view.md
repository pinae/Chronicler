# WP-037: Expectations view

**Milestone:** M8 · **Serves:** RQ2

## Goal
For each hypothesis, show what the audience expects to happen next and how likely each
continuation is.

## Acceptance criteria
- An API endpoint returns, for a hypothesis, the latest expectation at or before `t` per open
  step, for the whole table or one player.
- The lattice screen shows the candidates of a selected hypothesis with their probabilities,
  including "nothing yet".
- A hypothesis without expectations shows **No expectations yet**.
- Usage doc and e2e tests cover the scenarios; usage events are written.

## Dependencies
WP-027, WP-036.

## Out of scope
Recomputing expectations from the UI; they come only from the Seed phase.

## Status
open
