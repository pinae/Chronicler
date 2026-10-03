# WP-039: Candidate beat dry run

**Milestone:** M8 · **Serves:** RQ2

## Goal
A GM can ask "which hypotheses would this beat strengthen?" before narrating it.

## Acceptance criteria
- An API endpoint takes a draft beat, runs the matcher's Fill and Maintain phases on it without
  committing, and returns which hypotheses would be seeded, filled, refined, completed or
  refuted, with their weight changes.
- Nothing is persisted: beat, hypothesis and fill counts are unchanged afterwards.
- An invalid draft returns the validation errors.
- The screen has a form to compose a draft beat (predicate, role values from the chronicle's
  entities) and shows the result.
- Usage doc and e2e tests cover the scenarios; usage events are written.

## Dependencies
WP-036.

## Out of scope
Readouts for the draft beat: a dry run makes no LLM calls.

## Status
open
