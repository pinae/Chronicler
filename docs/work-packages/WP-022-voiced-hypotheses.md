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
done

## Summary
`IncrementalMatcher.voice` (and `StoredMatcher.voice`) turns a player's theory into a hypothesis
bound as stated, with `voiced_by` / `voiced_in`. If a live hypothesis of the schema has exactly that
binding, it is marked as voiced instead of being duplicated. Voiced hypotheses fill, refine and get
refuted like any other, and are never pruned (WP-019). Fixture utterances carry `theories` entries;
a theory is voiced at the `t` of the last beat before its utterance and must be spoken by a player.
Decisions on the open questions: "matches" means an identical binding, since a less specific theory
is a reading of its own; the voicing `t` is the last beat before the utterance. In `steward`, Anna's
theory becomes Betrayal(T=Aldric) at t=4.
