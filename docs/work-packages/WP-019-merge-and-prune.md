# WP-019: Merging and pruning

**Milestone:** M4 · **Serves:** RQ1

## Goal
Keep the lattice small and free of duplicates: identical hypotheses merge and weak ones are
pruned, without losing history.

## Acceptance criteria
- `Hypothesis.STATUS` gains `merged`, and `Hypothesis` gains a nullable `merged_into`
  self-reference.
- Two live hypotheses of the same schema with identical binding and identical fills are merged
  into the older one: the other gets `status = merged`, `merged_into` pointing to the survivor
  and `status_changed_at_t` set. No row is deleted.
- The survivor keeps `voiced_by` / `voiced_in` from either side.
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
- Decision (user, 2026-10-03): add `merged` and `merged_into` to the §4 model. Deleting rows
  would break the replay guarantee.

## Status
done

## Summary
Maintain now refutes, completes, merges and prunes, in that order. Live hypotheses with the same
identity (schema, binding and fills) merge into the oldest: the others get `status = merged`,
`merged_into` and `status_changed_at_t`, and the survivor inherits `voiced_by` / `voiced_in`. Pruning
removes live hypotheses below `MATCHER_WEIGHT_FLOOR` (default −6) and, per schema, the lowest-weighted
beyond `MATCHER_MAX_LIVE_PER_SCHEMA` (default 50), newest first on ties. Decision: voiced hypotheses
are never pruned, since they record what the table believes. No row is ever deleted; the stored
matcher creates new rows before linking `refines` and `merged_into`.
