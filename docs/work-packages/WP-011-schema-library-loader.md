# WP-011: Schema library loader

**Milestone:** M3 · **Serves:** RQ1

## Goal
Narrative schemas are authored in YAML, validated, and loaded into the database as typed
patterns the matcher can use.

## Acceptance criteria
- `Schema` and `Step` exist with the fields from §4.
- Beat patterns parse into typed objects covering the full §6.1 grammar: `pred`, `$Role`, `"*"`,
  literals, nested patterns, `$step_id` references, omitted roles, `tags_any` / `tags_all`,
  `scope` and `claimed_by`.
- Loading the `betrayal` example from §6 and serializing it back yields an equivalent structure.
- `manage.py load_schemas` loads every file in `schemas/library/`; loading an unchanged library
  twice creates no duplicates.
- The loader rejects, with a message naming the file and location: an unknown predicate in a
  pattern; a `$Role` not declared in `roles`; a `$step` reference to a step that does not exist;
  a `payoff_steps` entry that is not a step; a role whose kind is not an entity kind.

## Dependencies
WP-005.

## Out of scope
Constraints (WP-012), matching (WP-013).

## Notes
- `$Role` and `$step_id` share the `$` prefix. Proposed rule: resolve against `roles` first,
  then against step ids, and reject a name that is both. Confirm.

## Status
open
