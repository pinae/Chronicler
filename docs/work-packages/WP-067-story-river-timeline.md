# WP-067: Story river timeline API

**Milestone:** M8 (follow-up) · **Serves:** RQ1, RQ2

## Goal
The data the story river draws: for each audience, the readings it holds at every beat, grouped into
threads, with their share of plausibility, events and, for the game master, what is secret.

## Acceptance criteria
- `GET /api/chronicles/{id}/river` returns a column for the game master ("All beats") and one per
  player; each column lists its threads (a reading with the readings refined from it, named by its
  core reading and schema) and, for every t from 0, each thread's share, the status of its
  strongest reading and whether it is secret, plus the share of all other readings.
- A reading's share is `exp(weight)` over the sum for the readings held at t; at most seven threads
  per column (the seven with the largest peak share, in order of appearance), the rest is "other";
  the shares of a moment add up to 1.
- A thread of the game master's column is secret while no player holds a reading of its schema that
  binds every role of its core the same way; in The Broken Jug, "the judge harmed Frau Marthe" is
  secret from t=3 to t=18 and not from t=19, when Ben voices it.
- Events per thread: steps filled, completion, refutation and voicing, each once, with its t.
- The river is computed from one load of the stored rows per audience (`Lattice.timeline`).

## Dependencies
WP-021, WP-059.

## Out of scope
Drawing (WP-068).

## Status
done

## Summary
`gm_ui/river.py` computes the river from `Lattice.timeline` (new: the lattice at every t from one
load, equal to `Lattice.at` at each t), which cut the Macbeth river from 3.4 s and 2227 queries to
0.2 s and 112. Threads are grouped by their core reading (the root of the refinement chain), so a
reading that gets more specific keeps its band. `GET /api/chronicles/{id}/river` serves it with
entity and schema names resolved.
