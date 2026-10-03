# WP-042: Evaluate command

**Milestone:** M9 · **Serves:** RQ1

## Goal
One command turns a run file into a metrics table.

## Acceptance criteria
- `manage.py evaluate <story>` reads the latest run file (or one given by path), computes all
  §9.2 metrics and prints a table.
- Metrics whose inputs are missing (e.g. no `reader_beliefs`) are shown as `n/a`, not as errors.
- Tested via the command's output; usage doc in `docs/usage/`.

## Dependencies
WP-041.

## Out of scope
Comparing several runs or stories in one table (WP-048).

## Status
open
