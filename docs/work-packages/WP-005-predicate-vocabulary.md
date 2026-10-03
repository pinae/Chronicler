# WP-005: Predicate vocabulary and argument validation

**Milestone:** M1 · **Serves:** RQ1 (and RQ4 through `says`)

## Goal
The closed predicate vocabulary exists as data, and every beat's arguments can be validated
against it, including propositions nested inside claims.

## Acceptance criteria
- `schemas/vocabulary.yaml` contains the starter set from §5 (at most ~40 predicates), each with
  its role names, which roles are optional, and the allowed value kinds per role
  (`entity`, `literal`, `beat`, `prop`).
- Loading the vocabulary returns typed predicate definitions; a malformed entry raises an error
  naming the predicate.
- `validate_args(pred, args)`: an unknown role raises; a missing required role raises; an
  optional role may be omitted; a value of a kind the role does not allow raises (e.g. a literal
  where an entity is required).
- `prop` values are validated recursively against their own predicate, at any depth.
- Validation is a pure function: its tests run without the database.

## Dependencies
WP-001.

## Out of scope
- Storing beats and handling unknown predicates (WP-006).
- Checking entity kinds of bound roles (WP-013).

## Notes
- §5 lists roles per group loosely (`from`/`to`, `what`/`where`/`trait`, "beat or prop"). The
  exact role list per predicate is a spec decision and the YAML is the spec, so the first
  version is reviewed by the user before this package is marked done.

## Status
open
