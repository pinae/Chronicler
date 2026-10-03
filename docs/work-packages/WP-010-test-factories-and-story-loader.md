# WP-010: Test factories and fixture-story loader

**Milestone:** M0 · **Serves:** RQ1

## Goal
Tests can build chronicles cheaply with factories and load whole hand-written stories from the
§9.1 fixture format.

## Acceptance criteria
- A root `conftest.py` provides the fixtures `chronicle`, `players`, `entity_factory` and
  `beat_factory` (factory-boy).
- The fixture format (`transcript.yaml`, `beats.yaml` with presence per beat, `entities.yaml`,
  `README.md`) is documented in `backend/fixtures/stories/README.md`.
- `load_story("minimal")` loads a hand-written 5-beat story into a `session` chronicle:
  utterances, entities with aliases, beats with consecutive `t`, and scope grants.
- Loading a story whose `beats.yaml` references an unknown entity raises an error naming the
  file and the beat.
- The `minimal` fixture README records provenance, license and chronicle kind.

## Dependencies
WP-006, WP-008.

## Out of scope
- Parsing `ground_truth.yaml` (WP-040).
- Voiced theories in fixtures (WP-022).
- The pipeline-driven `FixtureIngester` (WP-029).

## Status
open
