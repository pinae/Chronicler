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
open
