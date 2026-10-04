# WP-048: RQ1 report

**Milestone:** R1 · **Serves:** RQ1

## Goal
Report how well beats and schemas capture the stories that have been replayed.

## Acceptance criteria
- A `report` command writes, per story: the §9.2 metrics, coverage, and the beats the vocabulary
  could not express (quarantined beats with their original predicates). The command is tested
  on synthetic run files.
- A baseline report on the evaluation stories is committed under `docs/research/`.

## Dependencies
WP-042, WP-043, WP-045, WP-046, WP-047.

## Out of scope
The real corpus and its report (split off as WP-057: it needs the human for story selection and
beat review, and WP-044); weight calibration (§13); closing the vocabulary gaps the report finds.

## Notes
- Split on 2026-10-04: the original package also held the corpus. Its code part did not need the
  human, so it was done first.

## Status
done

## Summary
`manage.py report <story>… --output FILE` writes a Markdown report with one section per story: its
latest run, the metric table of `evaluate` for the unfiltered lattice, and the quarantined beats
with the predicate the ingester proposed (run files now record `original_pred`). Finding the latest
run file moved to `evaluation/run_files.py`, shared with `evaluate`. The baseline report on
`steward` and `ferryman` (uniform reader) is `docs/research/rq1-baseline.md`, with notes in
`docs/research/README.md`; usage doc `docs/usage/report.md`.
