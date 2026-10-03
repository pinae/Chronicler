# WP-020: Lattice at t and the replay guarantee

**Milestone:** M4 · **Serves:** RQ1 (all evaluation depends on it)

## Goal
The full lattice at any past `t` is a filter over stored data, proven by the single most
important test in the project.

## Acceptance criteria
- `Lattice.at(chronicle, t)` returns the hypotheses created at or before `t`, with their status,
  weight and fills as they were at `t` (fills whose beat has `t' ≤ t`; status derived from
  `status_changed_at_t`).
- `Lattice.at(chronicle, 0)` is empty.
- A hand-authored `steward` fixture story (`session`, more than 20 beats) in which seeding,
  refinement, refutation, merging or pruning, and completion all occur.
- **Replay test:** running `steward` to the end and then calling `Lattice.at(chronicle, 20)`
  equals running a fresh chronicle only to beat 20 (compared on schema, binding, status, weight,
  fill beats and `refines` structure).

## Dependencies
WP-010, WP-016, WP-017, WP-018, WP-019.

## Out of scope
Expectations (WP-027), per-player lattices (WP-021).

## Status
open
