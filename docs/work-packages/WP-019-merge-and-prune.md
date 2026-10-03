# WP-019: Merging and pruning

**Milestone:** M4 · **Serves:** RQ1

## Goal
Keep the lattice small and free of duplicates: identical hypotheses merge and weak ones are
pruned, without losing history.

## Acceptance criteria
- Two live hypotheses of the same schema with identical binding and identical fills are merged
  into the older one; the other leaves the live set with `status_changed_at_t` set, and no row
  is deleted.
- Live hypotheses whose weight falls below a weight floor (setting) become `pruned`, with
  `status_changed_at_t` set.
- When a schema has more live hypotheses than a maximum (setting), the lowest-weighted ones are
  pruned, with a deterministic tie-break.
- Merging and pruning run in Maintain, after refutation.

## Dependencies
WP-016, WP-017, WP-018.

## Out of scope
Merging voiced hypotheses (WP-022); revisiting the pruning policy (§13).

## Notes
- The §4 `STATUS` choices have no value for "merged into another". Proposed: add `merged` plus
  a `merged_into` reference. Deleting rows would break the replay guarantee. Confirm before
  implementing, since it extends the §4 model.

## Status
open
