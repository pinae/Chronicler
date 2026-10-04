# Writing the RQ1 report

`report` collects the evaluation metrics of several stories into one Markdown report: per story
the metrics of `docs/usage/evaluate.md` for the unfiltered lattice, and the beats the vocabulary
could not express (quarantined beats, with the predicate the ingester proposed). Reports are kept
under `docs/research/`.

## Before you start
- Each story has been replayed at least once (`docs/usage/replay.md`).

## Write a report
1. In `backend/`, run `uv run python manage.py report steward ferryman --output ../docs/research/rq1-baseline.md`.

**Result:** the command prints `Wrote the report on 2 stories to ../docs/research/rq1-baseline.md`.
The report starts with `# RQ1 report` and the date, followed by one section per story (`## steward`)
naming its latest run file, the reader and the number of beats, a table of the metrics and either
`Every beat could be expressed in the vocabulary.` or a table of the quarantined beats with their
`t`, proposed predicate and text.

## A story that was never replayed
1. Run the report with a story that has no run file, e.g. `report steward alice --output report.md`.

**Result:** the command stops with `no run file for alice; run `manage.py replay alice` first`.
