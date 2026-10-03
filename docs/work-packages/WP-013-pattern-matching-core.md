# WP-013: Beat pattern matching

**Milestone:** M4 · **Serves:** RQ1

## Goal
An exact, pure function decides whether a beat matches a step pattern under a binding, and
returns the (possibly extended) binding: the core of the matcher (§7).

## Acceptance criteria
`match(pattern, beat, binding, fills) -> binding | None`, with one test per case:
- A different predicate does not match.
- `"*"` and omitted roles match anything.
- A literal matches only an equal literal.
- A bound `$R` matches only the bound entity.
- An unbound `$R` matches and returns a binding extended with `R`; the input binding is unchanged.
- `$step` matches only the beat that filled that step; an unfilled step never matches.
- A nested pattern recurses into a `prop` argument, including binding extension inside it;
  against a value that is not a `prop` it does not match.
- `tags_any` / `tags_all` constrain the beat's tags.
- Binding a role to an entity of the wrong kind (e.g. an `object` for a `character` role)
  does not match.
- Quarantined beats never match.
- The tests run on plain data, without the database.

## Dependencies
WP-011.

## Out of scope
The `scope` and `claimed_by` options (WP-014); creating hypotheses (WP-015).

## Status
open
