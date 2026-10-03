# WP-048: RQ1 corpus and report

**Milestone:** R1 · **Serves:** RQ1

## Goal
Run real stories end to end and report how well beats and schemas capture them.

## Acceptance criteria
- Three public-domain stories with a known twist and at least one recorded session exist as
  fixtures with `ground_truth.yaml`; their `beats.yaml` were drafted by the Ollama ingester and
  reviewed by a human.
- A `report` command writes, per story: the §9.2 metrics, coverage, and the beats the vocabulary
  could not express (quarantined beats with their original predicates). The command is tested
  on synthetic run files.
- The report is committed under `docs/research/`.

## Dependencies
WP-044, WP-045, WP-046, WP-047.

## Out of scope
Weight calibration (§13); closing the vocabulary gaps the report finds (separate, reviewed changes).

## Notes
- Mostly research and review work rather than code; expect to split it per story. Needs the human
  for story selection and beat review.

## Status
open
