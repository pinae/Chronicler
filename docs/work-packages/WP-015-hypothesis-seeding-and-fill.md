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
- `harms(Aldric, Mira)` fills `harm` of the hypothesis bound to `T=Aldric, V=Mira`, and not of one
  bound to `T=Ronan, V=Mira`. (The concept's `steals(Aldric, S, from=Mira)` binds the open role `S`,
  which per §7 creates a refinement; it is tested in WP-016.)
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
done

## Summary
`matching/engine.py` holds the pure incremental matcher. Live hypotheses are plain `HypothesisState`s;
a beat fills the first open step whose pattern matches under the unchanged binding, then seeds new
hypotheses from trigger steps unless a live hypothesis of the schema already holds the beat under a
compatible binding. `matching/store.py` (`StoredMatcher`) loads the stored lattice, steps one beat
and saves new hypotheses, field changes and new `StepFill`s, so a fresh matcher continues where the
last one stopped. Matches that would extend the binding are left to refinement (WP-016).
