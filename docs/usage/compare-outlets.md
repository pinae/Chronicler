# Comparing outlets

`compare_outlets` compares media chronicles of the same event, one per outlet
(`docs/usage/import-media.md`): how strongly each outlet's coverage instantiates each narrative
schema, how much the outlets agree on it, and how much of it rests on claims that fact-checkers
doubt.

**The boundary (concept §1):** the engine measures narrative instantiation. It does not adjudicate
truth. Whether a claim is false comes only from fact labels that annotators or fact-checking
sources attached (`docs/usage/fact-labels.md`); the engine reads them and never writes them.
Nothing here says which outlet is right.

## Before you start
- Each outlet's story has been replayed, e.g.
  `uv run python manage.py replay harbour-fire --reader none` and
  `uv run python manage.py replay harbour-fire-herald --reader none`, and you know the chronicle ids
  (the admin's chronicle list shows them).
- Optionally, fact labels have been imported for the chronicles.

## Compare two outlets
1. In `backend/`, run `uv run python manage.py compare_outlets <Courier chronicle id> <Herald chronicle id>`.

**Result:** after the boundary statement, one section per schema that at least one outlet
instantiates, e.g. for **Blame**:

```
Blame
Outlet                             Completion     Weight on false or unverified claims
The Harbour Fire (The Courier)     100% (3 of 3)  43%
The Harbour Fire (Harbour Herald)  33% (1 of 3)   0%
Overlap of filled steps, The Harbour Fire (The Courier) and The Harbour Fire (Harbour Herald): 25% (1 of 4)
```

- **Completion**: the share of the schema's required steps that the outlet's best reading filled
  with its claims.
- **Weight on false or unverified claims**: of the step weight of the outlet's strongest reading,
  the share that rests on claims labeled `false` or `unverified` by any labeler (here: the Courier's
  accusation is unverified and its motive false); `n/a` without a reading.
- **Overlap of filled steps**: of the steps either outlet filled for the same reading (the same
  people in the same roles; the outlet itself is left out), the share both filled.

## Only one chronicle
1. Run the command with a single chronicle id.

**Result:** the command stops with `compare at least two chronicles`.
