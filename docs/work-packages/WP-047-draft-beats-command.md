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
done

## Summary
`manage.py draft_beats <story> [--stories-dir] [--force]` runs the configured ingester over the
transcript through the pipeline inside a rolled-back transaction (so each utterance sees the
entities and beats drafted before it, and nothing is kept) and writes `beats.yaml` and
`entities.yaml` in fixture notation, every beat with its confidence. `review` marks flag beats with
predicates outside the vocabulary, ingester problems and utterances whose beats could not be
appended; `read_story` refuses a story while any mark is left. Drafting `steward` with the fixture
ingester reproduces its beats, entities and theories. Usage doc: `docs/usage/draft-beats.md`.
