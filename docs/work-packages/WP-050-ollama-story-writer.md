# WP-050: Ollama story writer

**Milestone:** R2 · **Serves:** RQ3

## Goal
A real model writes the next beat and its prose, with or without the engine's structure in the
prompt.

## Acceptance criteria
- `OllamaStoryWriter` prompts with lattice, expectations and target hypothesis; a prose-only
  variant prompts with the prose prefix alone.
- Calls go through the LLM call cache; unit tests use a fake transport.
- Integration test (`--llm`): the beat draft passes validation and the prose is not empty.

## Dependencies
WP-023, WP-049.

## Out of scope
Comparing the two variants (WP-051).

## Status
open
