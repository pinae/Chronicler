# WP-059: Learned beats enter players' views and lattices

**Milestone:** M5 (follow-up) · **Serves:** RQ1, RQ2

## Goal
Knowledge changes over time: when the players hear a character learn of an earlier beat, they learn
of it too, and their lattices take that beat up when they learn it, not never.

## Acceptance criteria
- A `learns(who, what={beat: n})` beat grants beat n to the players who witness it (and did not
  know it yet), from the learns beat's t, via that beat.
- A player's lattice matches the earlier beats the player learns of at t together with the beat of
  t, before Maintain, so a reveal is matched together with what it reveals.
- Every fill records when it was made; the lattice at t shows only fills made by t, so the replay
  guarantee holds for player lattices with learned beats.

## Dependencies
WP-008, WP-021.

## Out of scope
Characters learning beats through other predicates (`reveals`, `says` with a beat reference).

## Status
done

## Summary
Found while preparing the Macbeth and Broken Jug examples, whose twists are characters learning of
past crimes. `grant_learned_beat` now also grants the learned beat to the witnessing players.
`IncrementalMatcher.step_together(beats, world, now)` fills several beats that become known at the
same moment before Maintain (otherwise "V must not know the harm until the reveal" refuted the
betrayal before its reveal was matched); `Fill.at_t` and `StepFill.filled_at_t` record when a fill
was made, and `Lattice.at` filters by it. In `steward` the table now knows the theft from t=22; Ben's
seal betrayal completes then, Anna's stays live because she never saw how Aldric got access.
