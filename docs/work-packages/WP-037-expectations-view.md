# WP-037: Expectations view

**Milestone:** M8 · **Serves:** RQ2

## Goal
For each hypothesis, show what the audience expects to happen next and how likely each
continuation is.

## Acceptance criteria
- An API endpoint returns, for a hypothesis, the latest expectation at or before `t` per open
  step. (A hypothesis belongs to one lattice, so its expectations already are the table's or one
  player's.)
- The lattice screen shows the candidates of a selected hypothesis with their probabilities,
  including "nothing yet".
- A hypothesis without expectations shows **No expectations yet**.
- Usage doc and e2e tests cover the scenarios; usage events are written.

## Dependencies
WP-027, WP-036.

## Out of scope
Recomputing expectations from the UI; they come only from the Seed phase.

## Status
done

## Summary
`GET /api/chronicles/{id}/hypotheses/{hid}/expectations?t=` returns, per step, the latest readout at
or before `t`: question, when it was asked, candidates with probabilities and the mass outside them.
Each hypothesis row on the lattice page has an **Expectations** button. The selection is kept in the
address (`?hypothesis=`), and a panel shows each candidate's probability as a percentage, or
**No expectations yet**. `docs/usage/expectations.md` has two scenarios, each with a browser test; the
older lattice browser test now finds the open-steps column by position.
