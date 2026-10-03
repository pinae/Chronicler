# WP-016: Hypothesis refinement

**Milestone:** M4 · **Serves:** RQ1

## Goal
A fill that extends a binding creates a more specific child hypothesis instead of changing the
parent. This is what makes the set of hypotheses a lattice.

## Acceptance criteria
- `Betrayal(T=?, V=Mira)` plus `helps(Aldric, Mira)` creates `Betrayal(T=Aldric, V=Mira)` with
  `refines` pointing to the parent and the new beat filling `trust`.
- The child carries the parent's existing fills plus the new one; its `created_at_t` is the
  beat's `t`.
- The parent stays live with its binding and fills unchanged.
- A fill that does not extend the binding fills the hypothesis itself (no child).

## Dependencies
WP-015.

## Out of scope
Deduplicating identical children (WP-019).

## Status
open
