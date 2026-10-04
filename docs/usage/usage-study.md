# Exporting and summarizing usage for the study

Every request the GM/writer interface makes to the API is recorded as a usage event: which view,
for which chronicle, at which `t`, with which parameters, whether the engine answered (`status`),
and for a tried beat what was tried (`body`). These events are the raw material for RQ2: which
engine outputs does a game master or writer actually act on?

## Before you start
- The backend is installed and migrated, and the interface has been used (`docs/usage/chronicle.md`,
  `docs/usage/expectations.md`, `docs/usage/try-a-beat.md`).
- Recordings of real tables may only be used with everyone's consent (WP-056).

## Export the usage events
1. In `backend/`, run `uv run python manage.py export_usage --chronicle 3 --since 2026-10-01 --until 2026-10-31 --output usage.jsonl`.

**Result:** `Exported <n> usage events to usage.jsonl`. Each line is one event in order of time:
`{"id", "view", "chronicle", "t", "params", "created_at"}`. Every option is optional: without
`--chronicle` all chronicles are exported, without `--output` the lines are printed. A day that is
not written like `2026-10-04` stops the command with `--since must be a day like 2026-10-04`.

## Summarize what was acted on
1. Run `uv run python manage.py usage_summary 3`.

**Result:** the engine outputs shown for chronicle 3, each with whether a matching beat followed:

```
Engine outputs shown for The Steward of Wend, and whether a matching beat followed

Dry runs: 1 of 2 acted on
  t=25  Mira is at The great hall.  not acted on
  t=25  Mira is at The cellar.  acted on at t=25

Expectations shown: 1 of 6 acted on
  t=10  Next: ___ trusts Aldric.  Mira (17%)  acted on at t=17
  t=10  Next: ___ trusts Aldric.  Edda (17%)  not acted on
```

What counts as acted on:
- a **tried beat** (`docs/usage/try-a-beat.md`) when the same beat, with the same predicate and
  arguments, was narrated from the `t` it was tried for on; tries the engine rejected are left out;
- an **expected candidate** (`docs/usage/expectations.md`) when a later beat filled the step the
  audience was asked about with that candidate in the role, in the same lattice. Each candidate of
  each readout is listed once, however often it was shown.
