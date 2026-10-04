# Fact labels

A fact label is an external verdict on a beat, usually on a claim of a media outlet: `verified`,
`false`, `unverified` or `misleading`, with who judged it and a note. Labels come from annotators
or fact-checking sources, never from the engine: the engine measures how strongly a story or an
outlet instantiates a narrative; it does not judge what is true (concept §1, RQ4). A test fails if
engine code ever creates, changes or deletes a label.

## Before you start
- The chronicle exists, e.g. replayed from a media story (`uv run python manage.py replay harbour-fire --reader none`),
  and you know its id (the admin's chronicle list shows it).

## Import an annotation sheet
1. Write a CSV file with the columns `t`, `verdict`, `labeler` and optionally `note`:

```
t,verdict,labeler,note
1,unverified,FactDesk,No witness is named.
4,false,FactDesk,Holt gave up his claim to the land in 2024.
```

2. In `backend/`, run `uv run python manage.py import_fact_labels <chronicle id> labels.csv`.

**Result:** `Imported 2 fact labels into The Harbour Fire (The Courier).` Each label is attached to
the beat at its `t`. Importing a sheet again replaces a labeler's earlier verdict on the same beat
instead of adding a second one.

## Rows that cannot be attached
1. Import a sheet with a row for `t = 99` (no such beat) or with the verdict `probably`.

**Result:** the other rows are imported, and the command lists the rest, e.g.

```
Imported 1 fact label into The Harbour Fire (The Courier).
2 rows could not be imported:
  line 3: the chronicle has no beat at t=99
  line 4: unknown verdict 'probably' (verified, false, unverified, misleading)
```

## Edit labels in the admin
1. Open the admin (`docs/usage/admin.md`) and choose **Fact labels**.

**Result:** the labels are listed with their beat, verdict and labeler and can be filtered by
verdict and labeler. Unlike beats, labels can be added, changed and deleted here.
