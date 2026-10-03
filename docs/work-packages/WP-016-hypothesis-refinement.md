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
done

## Summary
`IncrementalMatcher.step` now works in three passes. First, every live hypothesis that can take the
beat under its unchanged binding gets the fill. Next, every other live hypothesis whose binding the
beat would extend gets a refined child, which carries the parent's fills plus the new one. Last,
trigger steps seed. A child or seed is only created when no live hypothesis of the schema already
holds the beat under a compatible binding, so a repeated beat goes to the existing child instead of
spawning duplicates. Parents stay live and unchanged; `refines` is stored and reloaded. The concept's
`steals(Aldric, S, from=Mira)` example creates `Betrayal(T=Aldric, V=Mira, S=key)` as a child.
