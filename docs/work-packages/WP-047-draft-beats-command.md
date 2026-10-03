# WP-047: Draft beats command

**Milestone:** R1 · **Serves:** RQ1

## Goal
Use the LLM ingester to draft `beats.yaml` and `entities.yaml` for a large story, for human review.

## Acceptance criteria
- `manage.py draft_beats <story>` runs the configured ingester over `transcript.yaml` and writes
  draft `beats.yaml` and `entities.yaml` with each beat's confidence; quarantined beats are
  marked for review.
- It refuses to overwrite existing files unless `--force` is given.
- Tested with a fake ingester; usage doc in `docs/usage/`.

## Dependencies
WP-031.

## Out of scope
A review UI; reviewers edit the YAML files directly.

## Status
open
