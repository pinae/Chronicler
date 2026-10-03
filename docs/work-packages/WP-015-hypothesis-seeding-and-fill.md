# WP-015: Hypotheses, seeding and fill

**Milestone:** M4 · **Serves:** RQ1

## Goal
The matcher's Fill phase: new beats start partial matches of schemas and fill open steps of
existing ones.

## Acceptance criteria
- `Hypothesis` and `StepFill` exist with the fields from §4.
- A `Matcher` protocol with `step(beat)`, and a naive incremental implementation
  (new beat × open steps of live hypotheses, plus new beat × trigger steps).
- A `trusts(Mira, Aldric)` beat seeds `Betrayal(T=Aldric, V=Mira)` with `trust` filled,
  `created_at_t` equal to the beat's `t`, and weight `prior + weight(trust)`.
- A second identical `trusts` beat creates no duplicate; it adds a second fill to the
  repeatable `trust` step.
- Beats that match only non-trigger steps never seed.
- `steals(Aldric, S, from=Mira)` fills `harm` of the hypothesis bound to `T=Aldric, V=Mira`,
  and not of one bound to `T=Ronan, V=Mira`.
- A beat fills at most one step per hypothesis.

## Dependencies
WP-011, WP-013.

## Out of scope
Refinement (WP-016), weight caps and completion (WP-017), refutation (WP-018), merging and
pruning (WP-019), Seed-phase readouts (WP-027).

## Notes
- §7 allows several steps per beat "only if those steps allow it", but `Step` has no field for
  that. v1 keeps the default of one step per beat per hypothesis until a schema needs more.

## Status
open
