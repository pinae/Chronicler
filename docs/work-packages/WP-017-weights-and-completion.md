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
open
