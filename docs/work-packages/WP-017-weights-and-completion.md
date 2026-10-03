# WP-017: Weights and completion

**Milestone:** M4 · **Serves:** RQ1

## Goal
Hypothesis weights follow the §7 arithmetic, and hypotheses complete when all required steps
are filled.

## Acceptance criteria
- `weight = schema.prior + Σ step.weight` over filled steps.
- A repeatable step contributes its weight once per fill, up to a cap from settings (default 3);
  further fills add nothing.
- An optional step adds its weight when filled but is not needed for completion.
- A hypothesis becomes `complete` when all required steps are filled; `status_changed_at_t` is
  the `t` of the completing beat.

## Dependencies
WP-015.

## Out of scope
Weight calibration (deferred, §13).

## Notes
- Open: may a complete hypothesis still collect fills, e.g. further repeatable `trust` beats?
  Proposed: yes for repeatable steps, within the cap. Confirm.

## Status
done

## Summary
`weight_of(schema, fills, repeat_cap)` adds the schema prior to each filled step's weight, counting a
repeatable step once per fill up to `MATCHER_REPEATABLE_FILL_CAP` (default 3). The matcher and the
store use it via `MatcherConfig`. A new Maintain step marks a hypothesis `complete`, with
`status_changed_at_t` at the completing beat, once all required steps are filled; optional steps add
weight but are not needed. Decision on the open question: a complete hypothesis is no longer live and
takes no further fills, since its arc has finished. That reverses the earlier proposal.
