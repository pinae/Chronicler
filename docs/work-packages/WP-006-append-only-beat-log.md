# WP-006: Append-only beat log

**Milestone:** M1 · **Serves:** RQ1

## Goal
Beats can be appended to a chronicle, are validated on the way in, and can never be changed
afterwards: the foundation of replayability.

## Acceptance criteria
- `Chronicle.append(...)` stores a beat with the next consecutive `t`: the first beat gets
  `t = 1`, each further beat the previous `t + 1`.
- Appending with an explicit `t` that is not the next consecutive value raises and stores nothing.
- Calling `save()` on an existing beat raises; calling `delete()` on a beat raises.
- `args` are validated against the vocabulary on append; invalid args raise and store nothing.
- A beat with an unknown predicate does not raise: it is stored with `pred = "unknown"` and the
  tag `quarantined`, and the original predicate name can be read from the stored beat.
- Every beat references its source utterance and has a `source_kind` of `narration`, `action`
  or `claim`.

## Dependencies
WP-004, WP-005.

## Out of scope
Scope grants (WP-008), entity attributes (WP-007).

## Notes
- Starting `t` at 1 lets `t = 0` mean "before the first beat" (empty lattice, empty view).
- Bulk queryset updates and deletes bypass model methods; the codebase does not use them on beats.

## Status
open
