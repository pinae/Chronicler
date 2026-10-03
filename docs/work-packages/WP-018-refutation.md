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
done

## Summary
Maintain now refutes before it completes. A live hypothesis is refuted when the beat matches a
`contradicts` pattern of a step it has not filled, without needing new bindings (so a murder of an
unbound `T` refutes nothing). It is also refuted when one of its schema's constraints fails as of the
beat's `t`. `refuted_by` and `status_changed_at_t` point to that beat, and refuted hypotheses take no
further fills. The engine checks constraints only when given chronicle facts; `StoredMatcher` always
passes `StoredChronicleFacts`. With the time-scoped `not_knows`, a victim who learns of the harm at
the reveal completes the betrayal, while one who knew earlier refutes it.
