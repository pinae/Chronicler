# WP-049: Story writer protocol and generate command

**Milestone:** R2 · **Serves:** RQ3

## Goal
The engine can write a story toward a target twist and evaluate its own output.

## Acceptance criteria
- `StoryWriter` is a `typing.Protocol`: (chronicle prefix, lattice, target hypothesis,
  expectations) → (next beat draft, prose).
- `FixtureStoryWriter` returns scripted beats and prose for tests.
- `manage.py generate <seed-story> --target <schema and binding> --beats N` writes a `literature`
  chronicle, re-ingests the prose and evaluates it with the §9.2 metrics.

## Dependencies
WP-029, WP-042.

## Out of scope
LLM-backed writing (WP-050); the rater export (WP-051).

## Status
open
