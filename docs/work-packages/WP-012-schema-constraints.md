# WP-012: Schema constraints

**Milestone:** M3 · **Serves:** RQ1

## Goal
Schema constraints become typed objects that can check a partial hypothesis against the chronicle.

## Acceptance criteria
- Constraint entries deserialize into typed classes for `distinct`, `before`, `after`, `knows`,
  `not_knows` and `same_place`; an unknown type is rejected by the loader.
- Each class has `check(hypothesis, chronicle) -> bool`, tested with a satisfying and a violating
  case per type.
- `before` / `after` compare the `t` of the beats that filled the referenced steps.
- `knows` / `not_knows` use the scope grants of the character bound to the role.
- `same_place` uses `is_at` attributes as of the relevant step's `t`.
- A constraint that refers to an unbound role or an unfilled step is not (yet) violated.
- `check` works on a plain-data hypothesis (binding plus fills), so its tests need no
  `Hypothesis` model.

## Dependencies
WP-007, WP-008, WP-011.

## Out of scope
Refuting hypotheses on violation (WP-018).

## Notes
- The §6 example `not_knows: {role: V, step: harm}  # until reveal` cannot hold forever, because
  the `reveal` step is V learning about the harm. Proposed reading: `not_knows` is checked only
  up to the fill of the payoff step(s). Confirm before implementing.
- §6.2 does not give the arguments of `same_place`; define them here.

## Status
open
