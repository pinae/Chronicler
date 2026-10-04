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
done

## Summary
- `manage.py evaluate <story> [--run FILE] [--runs-dir DIR] [--audience NAME] [--top-k K]` reads
  the latest run file of the story (file names are UTC timestamps) or the given one, reads the
  story's ground truth if it has one, and prints a header (story, reader, lattice, run) and a
  metric table built by `evaluation/report.py`.
- Every row reads `n/a` when its inputs are missing: no ground truth, no reader, no voiced theory,
  no annotated beliefs, or a run that ends before the t asked about (twist recall outside the run
  is now `None`; lead time only looks at the beats the run has).
- An unknown `--audience` and a missing run file stop the command with a message saying what
  exists or what to run.
- Tested through the command's output (`evaluation/tests/test_evaluate_command.py`); usage doc
  `docs/usage/evaluate.md`.
