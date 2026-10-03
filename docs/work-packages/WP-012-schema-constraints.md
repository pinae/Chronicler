# WP-012: Schema constraints

**Milestone:** M3 · **Serves:** RQ1

## Goal
Schema constraints become typed objects that can check a partial hypothesis against the chronicle.

## Acceptance criteria
- Constraint entries deserialize into typed classes for `distinct`, `before`, `after`, `knows`,
  `not_knows` and `same_place`; an unknown type is rejected by the loader.
- Each class has `check(hypothesis, chronicle, t) -> bool`, evaluated as of time `t`, and is
  tested with a satisfying and a violating case per type.
- `before` / `after` compare the `t` of the beats that filled the referenced steps.
- `knows` / `not_knows` use the scope grants of the character bound to the role, and are
  time-scoped: knowledge changes while a story is narrated, so a schema states *when* knowledge
  must (not) hold instead of leaving it to a comment.
  - `knows: {role, step}` holds if the character knew the step's beat when that step was filled.
  - `not_knows: {role, step, until: <step>}` holds if the character does not know the step's beat
    at any `t` from the step's fill up to (not including) the fill of the `until` step. Once the
    `until` step is filled the constraint is settled. Without `until` the window is open-ended.
  - The `betrayal` library schema uses `not_knows: {role: V, step: harm, until: reveal}`.
- Evaluating a constraint at an earlier `t` gives the answer it had then (needed by `Lattice.at`).
- `same_place` uses `is_at` attributes as of the relevant step's `t`.
- A constraint that refers to an unbound role or an unfilled step is not (yet) violated.
- `check` works on a plain-data hypothesis (binding plus fills), so its tests need no
  `Hypothesis` model.

## Dependencies
WP-007, WP-008, WP-011.

## Out of scope
Refuting hypotheses on violation (WP-018).

## Notes
- Decision (user, 2026-10-03): the §6 comment `# until reveal` becomes the explicit `until` key.
  The concept's example is otherwise unchanged.
- §6.2 does not give the arguments of `same_place`; define them here.

## Status
open
