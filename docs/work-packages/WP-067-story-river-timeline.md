# WP-067: Story river timeline API

**Milestone:** M8 (follow-up) · **Serves:** RQ1, RQ2

## Goal
The data the story river draws: for each audience, the readings it holds at every beat, grouped into
threads, with their share of plausibility, events and, for the game master, what is secret.

## Acceptance criteria
- `GET /api/chronicles/{id}/river` returns, for the game master and each player, the threads (a
  reading with its refinements, labelled by its strongest member, coloured by schema) and for every
  t each thread's share, status and whether only the game master holds it.
- A share is `exp(weight)` normalised over the readings held at t; at most seven threads per
  audience (those strongest at some t), the rest summed as "other".
- Events per thread: steps filled, completion, refutation, voicing, with their t.
- In Macbeth, the game master's usurpation thread is secret until t=32 for Dora's lattice and not
  secret for Anna's from t=17; the shares at every t add up to 1.

## Dependencies
WP-021, WP-059.

## Out of scope
Drawing (WP-068).

## Status
open
