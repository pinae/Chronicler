# Evaluating a run

`evaluate` turns a run file (see `docs/usage/replay.md`) into a table of the evaluation metrics of
concept §9.2: did the engine see the twist coming, since when, how much of the story the schemas
cover, whether players' theories match the engine's top readings, and what the reader model made
of the truth. The metrics are defined in `backend/evaluation/metrics.py`; the inputs the reader
model adds to a run are described in `docs/run-file-format.md`.

## Before you start
- The backend is installed and migrated (`cd backend && uv run python manage.py migrate`).
- The story has been replayed at least once, e.g. `uv run python manage.py replay steward --reader uniform`.
- Metrics about the twist need the story's `ground_truth.yaml` (format:
  `backend/fixtures/stories/README.md`).

## Evaluate the latest run of a story
1. In `backend/`, run `uv run python manage.py evaluate steward`.

**Result:** the first line names the story, the reader, the lattice and the run file
(`Evaluation of steward: reader UniformReader, lattice all, run of …`), followed by a table with one
row per metric. For `steward` replayed with the uniform reader:

```
Metric                          Value
twist recall at reveal - 1      yes
twist recall at reveal - 5      yes
twist recall at reveal - 20     yes
lead time                       20 beats (first held at t = 2)
coverage: beats filling a step  50% (12 of 24)
coverage: beats quarantined     0% (0 of 24)
voiced agreement (top 5)        100% (1 of 1)
retrospective fit               0% (0 of 10)
largest surprise                n/a
calibration (Brier score)       0.047
```

The uniform reader believes nothing in particular, so no beat fits the truth better than its rival
and the belief in the truth never rises; a language model gives these rows meaning. The rows:

| Metric | Means |
|---|---|
| twist recall at reveal - 1 / 5 / 20 | `yes` if the lattice held the true hypothesis that many beats before the reveal |
| lead time | how many beats before the reveal the lattice first held it |
| coverage: beats filling a step | share of beats that filled a step of any hypothesis, e.g. `50% (12 of 24)` |
| coverage: beats quarantined | share of beats whose predicate the vocabulary did not know |
| voiced agreement (top 5) | share of players' theories that matched one of the engine's five strongest readings when voiced |
| retrospective fit | share of beats in the dormant window that fit the truth better than the strongest rival |
| largest surprise | the beat at which the reader's belief in the truth rose most, next to the reveal (`n/a` if it never rose) |
| calibration (Brier score) | how far the reader's answers are from the annotated beliefs (0 is perfect) |

## A metric without inputs
1. Run `uv run python manage.py replay minimal --reader none`.
2. Run `uv run python manage.py evaluate minimal`.

**Result:** the rows about the twist and the reader read `n/a`: `minimal` has no ground truth and
the run asked no reader. The coverage rows still have values.

## Evaluate a particular run or a player's lattice
1. Run `uv run python manage.py replay steward --reader none --per-player`.
2. Run `uv run python manage.py evaluate steward --audience Anna`.

**Result:** the first line says `lattice Anna`; twist recall, lead time and voiced agreement are
measured in the lattice built from what Anna saw.

3. Run `uv run python manage.py evaluate steward --run evaluation/runs/steward/<timestamp>.json` with
   the name of an older run file.

**Result:** the table for that run instead of the latest one.

## Without a run file
1. Run `uv run python manage.py evaluate steward --runs-dir /tmp/empty`.

**Result:** the command stops with `no run file for steward; run `manage.py replay steward` first`.
