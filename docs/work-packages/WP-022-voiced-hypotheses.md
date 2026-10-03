# WP-022: Voiced hypotheses

**Milestone:** M5 · **Serves:** RQ1, RQ2 (calibration labels)

## Goal
Theories that players state out loud become hypotheses in the lattice, flagged with who voiced
them and where.

## Acceptance criteria
- A player utterance tagged as a theory (fixture: a `theories` entry such as
  `{schema: betrayal, binding: {T: aldric}}`) creates a hypothesis with `voiced_by`, `voiced_in`
  and the stated binding, even when no step is filled.
- A voiced hypothesis that matches an existing engine hypothesis is merged: the engine
  hypothesis gains `voiced_by` / `voiced_in` and no duplicate is created.
- Voiced hypotheses take part in Fill like any other hypothesis.
- The fixture format documentation (WP-010) describes the `theories` entry.

## Dependencies
WP-010, WP-019.

## Out of scope
- Detecting theories in live speech (ingester work, after WP-031).
- Player-authored new schemas (`origin = voiced`).

## Notes
- Open, to settle before implementing: does "matches" mean an identical binding, or also an
  engine hypothesis that refines the voiced one? Which `t` does a voiced hypothesis get
  (proposed: the `t` of the latest beat when the utterance was made)? Are voiced hypotheses
  exempt from pruning?

## Status
open
