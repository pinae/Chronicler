# WP-036: Lattice screen

**Milestone:** M8 · **Serves:** RQ2

## Goal
Show the hypothesis lattice at a chosen `t` (default: now), so a GM can see which stories the
chronicle currently supports.

## Acceptance criteria
- An API endpoint returns `Lattice.at(chronicle, t)`, optionally for one player: schema, binding
  with entity names, weight, status, filled and open steps, and the `refines` parent.
- The screen shows hypotheses grouped by schema and ordered by weight, with a `t` control.
- Moving `t` back shows the lattice as it was then (the same data as `Lattice.at`).
- Usage doc and e2e tests cover the scenarios; usage events are written.

## Dependencies
WP-021, WP-035.

## Out of scope
Expectations (WP-037).

## Status
open
