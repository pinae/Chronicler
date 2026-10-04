# WP-061: Example stories and a guided tour

**Milestone:** M9 (follow-up) · **Serves:** RQ1, RQ2

## Goal
A user can tell whether the engine works as it should by running it on two stories they already
know and comparing what they see with what the tour says they should see: *Macbeth* as a
roleplaying session in which each player plays a main character, and Kleist's *The Broken Jug*
as a pen-and-paper adventure in which the players investigate a crime only the game master knows.

## Acceptance criteria
- Both stories are fixture stories with transcript, entities, beats, ground truth and a README
  stating their provenance (public-domain plays, our own adaptation).
- With the full schema library, the game master's lattice of Macbeth holds the play's plot lines
  (usurpation, both prophecies about Macbeth and a hidden crime, complete; Fleance's prophecy live).
- In both stories each lattice first holds the true reading when its audience could know or guess
  it: Macbeth t=17 for the game master, Anna and Ben, t=23 for Clara, t=32 for Dora; The Broken Jug
  t=3 for the game master, t=19 for Ben, t=24 for Anna, t=25 for Clara.
- The game master's secret (t=3 in The Broken Jug) enters a player's lattice at the confession.
- `docs/usage/guided-tour.md` walks through both stories screen by screen, with what to expect and
  why, the `evaluate` comparison per player, a checklist, the known limits and what changes with a
  language model; every screen scenario has a browser test.

## Dependencies
WP-043, WP-059, WP-060.

## Out of scope
Ingesting the stories' transcripts with a language model; changing the engine's known limits that
the tour lists (rival theories are not refuted by a confession, readings the dead cannot complete).

## Status
done

## Summary
`fixtures/stories/macbeth` (36 beats, four players) and `fixtures/stories/broken-jug` (32 beats,
three players, game master notes with `players: []`). Building them found two flaws, fixed here:
every new piece of evidence for a suspicion started another hidden-crime reading (`suspicion` is
now repeatable), and Eve was never named in a beat the players saw before the reveal, so the reader
could not offer her as an answer (a public beat now puts her in court). The engine's limits the
stories show are listed in the tour instead of fixed. `evaluation/tests/test_example_stories.py`
checks the tour's claims on the run files; `e2e/tests/guided-tour.spec.ts` runs its screen
scenarios. The README now starts "Trying it out" with the tour.
