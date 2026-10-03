# WP-030: Replay command and run files

**Milestone:** M7 · **Serves:** RQ1 (evaluation)

## Goal
One command runs a fixture story through the whole pipeline beat by beat and exports everything
evaluation needs.

## Acceptance criteria
- `manage.py replay <story>` loads the story's transcript into a fresh chronicle and runs ingest →
  append → scope → entity view → `Matcher.step` (Fill, Seed, Maintain) for every utterance,
  issuing LLM calls sequentially.
- It writes `evaluation/runs/<story>/<timestamp>.json` with the lattice and expectations at every
  `t` and the ids of the `LLMCall`s used.
- The run file format is versioned and documented.
- A second run of the same story makes no transport calls (everything is served from the cache).

## Dependencies
WP-020, WP-027, WP-029.

## Out of scope
Metrics (WP-040 onwards).

## Notes
- Running whole stories in tests with `TableReader` would need a table entry for every
  `(t, question)`. Decide here between a readout-free mode (Fill and Maintain only) and a trivial
  reader bound for lattice-only tests.
- Decide whether run files are committed or git-ignored. Proposed: ignored, except small
  reference runs used by tests.

## Status
open
