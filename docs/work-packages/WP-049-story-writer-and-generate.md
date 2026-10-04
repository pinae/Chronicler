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
done

## Summary
New app `writing`: `StoryWriter.continue_story(WritingRequest(prefix, lattice, target,
expectations)) -> Continuation(prose, intended beat or None)` and `FixtureStoryWriter` (scripted).
`generate_story` replays the seed as a `literature` chronicle and appends each continuation's prose
as an utterance that the configured ingester re-ingests, so the next request and the evaluation
rest on what the prose conveys; the intended beat is kept in `utterance.source` for comparison.
`manage.py generate <seed> --target "betrayal T=aldric V=mira" --beats N [--reader]` checks the
target against the seed, writes a run (`<seed>-generated`) with the target as ground truth
(revealed at the last beat, dormant over the generated beats before) and prints the metric table.
No writer is configured in settings until WP-050, so the usage doc comes with it.
