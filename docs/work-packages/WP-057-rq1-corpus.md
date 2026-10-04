# WP-057: RQ1 corpus

**Milestone:** R1 · **Serves:** RQ1

## Goal
Run real stories end to end and report how well beats and schemas capture them.

## Acceptance criteria
- Three public-domain stories with a known twist and at least one recorded session exist as
  fixtures with `ground_truth.yaml`; their `beats.yaml` were drafted by the Ollama ingester
  (`draft_beats`) and reviewed by a human.
- Their report (`manage.py report`) is committed under `docs/research/`, with notes on what the
  vocabulary and the schema library could not express.

## Dependencies
WP-044, WP-048.

## Out of scope
Weight calibration (§13); closing the vocabulary gaps the report finds (separate, reviewed changes).

## Notes
- Split off WP-048 on 2026-10-04. Mostly research and review work; expect to split it per story.
- Blocked on the human: story selection (public domain, known twist), a recorded session with
  consent (WP-056), beat review, and the Ollama smoke result for WP-044.

## Status
blocked
