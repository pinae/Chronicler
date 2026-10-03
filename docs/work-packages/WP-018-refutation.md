# WP-018: Refutation

**Milestone:** M4 · **Serves:** RQ1

## Goal
The Maintain phase refutes hypotheses that a beat contradicts or that violate a hard constraint.

## Acceptance criteria
- A beat matching a step's `contradicts` pattern under the hypothesis' binding sets
  `status = refuted`, `refuted_by` to the beat and `status_changed_at_t` to its `t`.
- After every Fill, constraints are checked; a hypothesis that violates one (e.g. `distinct`
  with `T = V`) is refuted with the same fields set.
- Refuted hypotheses receive no further fills.

## Dependencies
WP-012, WP-015.

## Out of scope
Soft constraints (all v1 constraints are hard).

## Notes
- Reading of the §6 example ("T dead before harm"): a step's `contradicts` patterns apply only
  while that step is still open. Confirm.

## Status
open
