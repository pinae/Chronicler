# WP-043: Evaluation stories

**Milestone:** M9 · **Serves:** RQ1

## Goal
Two complete hand-authored stories prove the pipeline end to end: the engine sees each twist
coming.

## Acceptance criteria
- Two stories under `fixtures/stories/` (our own material), each with transcript, beats,
  entities, `ground_truth.yaml` and a README with provenance and chronicle kind. `steward` may be
  extended to be one of them.
- A test replays both with the fixture ingester and the test reader and asserts twist recall at
  k = 5 on both.

## Dependencies
WP-042.

## Out of scope
Public-domain and recorded-session corpora (R1); LLM-backed ingest or readouts.

## Status
open
