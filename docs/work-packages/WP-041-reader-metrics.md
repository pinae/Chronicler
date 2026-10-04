# WP-041: Reader-based metrics

**Milestone:** M9 · **Serves:** RQ1

## Goal
The metrics that need the reader model: retrospective fit, surprise curve and calibration.

## Acceptance criteria
- When a story has a `ground_truth.yaml`, replay also records: the Bayes factor of the true vs.
  the dominant hypothesis for each beat in the dormant window, the readout belief toward the true
  hypothesis per beat, and readouts for the annotated `reader_beliefs` questions.
- Pure functions for retrospective fit, surprise curve and calibration (Brier score), tested
  against a synthetic run file with known answers.

## Dependencies
WP-027, WP-040.

## Out of scope
Lattice-only metrics (WP-040); the evaluate command (WP-042).

## Notes
- Needs precise definitions before coding: the "dominant hypothesis" (highest-weight live
  hypothesis of any schema?), the "readout belief toward the true hypothesis", and how a free
  question like "Who will harm Mira?" maps onto a readout. Agree on them at the start.

## Status
done

## Summary
The open definitions were decided as follows (the user asked for autonomous work; revisit with
the LLM smoke result, WP-044):
- **Audience**: the table (common knowledge). Its context comes from the context builder; its
  readings are the hypotheses of the unfiltered lattice whose fills it saw and whose entities it
  knows (as for expectations).
- **Phrasing**: every hypothesis is put to the reader the same way, "a Betrayal with T = Aldric,
  V = Mira", so the truth and its rival differ only in the story they tell.
- **Dominant hypothesis** (the rival in the Bayes factor): the strongest reading the table could
  hold before the beat that is *not* the truth, with at least one fill (ties: the older). The
  truth itself comes from the ground truth, not from the lattice, so retrospective fit measures
  whether the clues were in the story, independent of whether the matcher found them (twist recall
  measures that). Without a rival the truth is compared with the reader assuming nothing
  (`bayes_factor` now accepts `assumption_b=None`).
- **Readout belief toward the truth**: P(yes) to "Is the story <truth>?" at every t at which the
  table knows the truth's entities (asking earlier would name a stranger).
- **Free reader-belief questions**: asked as annotated, with the annotated answers (entity names,
  "nothing like this" for `none`) as candidates in their order; the readout is mapped back to slugs.

Implementation: `evaluation/truth_readouts.py` (`read_truth`) produces the run file's `truth`
record after the replay; the replay command adds it for whole stories with a ground truth and a
reader (not for `--until`). A reader that cannot score beats yet (the Ollama reader before WP-044)
records `bayes_factors: null`. Pure metric functions in `evaluation/metrics.py`, tested against
synthetic run files: `retrospective_fit` (share of window beats with log BF > 0),
`surprise_curve` (change in belief per readout), `largest_surprise_t` (ties: earliest) and
`calibration` (Brier score against the annotated beliefs, mean over questions). The run file
format is documented in `docs/run-file-format.md`.
