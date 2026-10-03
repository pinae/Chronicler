# WP-013: Beat pattern matching

**Milestone:** M4 · **Serves:** RQ1

## Goal
An exact, pure function decides whether a beat matches a step pattern under a binding, and
returns the (possibly extended) binding: the core of the matcher (§7).

## Acceptance criteria
`match(pattern, beat, binding, context) -> binding | None` (the context carries role kinds, entity
kinds and the hypothesis' fills), with one test per case:
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
done

## Summary
`matching/match.py` matches a `PlainBeat` against a typed `BeatPattern` under a binding, exactly and
without side effects. It returns an extended copy of the binding or None. A `MatchContext` carries the
schema's role kinds, the chronicle's entity kinds and the hypothesis' fills. `$step` compares beat
`t`s (ADR-005), nested patterns recurse into propositions, and role variables only bind entities of
the role's kind. A wildcard also matches an omitted optional role; a concrete pattern value for a
role the beat lacks does not match.
