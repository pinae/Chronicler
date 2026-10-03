# WP-053: Fact labels

**Milestone:** R3 · **Serves:** RQ4

## Goal
External factuality labels can be attached to claim beats by annotators or by import, never by
the engine.

## Acceptance criteria
- `FactLabel` exists with the fields from §4; `verdict` is one of `verified`, `false`,
  `unverified` or `misleading`.
- An import command reads an annotation sheet and attaches labels to beats; rows that refer to
  unknown beats are reported, not silently skipped.
- Fact labels are editable in the admin.
- A test fails if engine code (matching, reader, evaluation) writes fact labels.

## Dependencies
WP-033, WP-052.

## Out of scope
Automatic fact checking: the engine never judges truth.

## Notes
- Open: the format of the annotation sheet or fact-check source.

## Status
open
