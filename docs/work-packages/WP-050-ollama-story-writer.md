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
done

## Summary
`OllamaStoryWriter` prompts with the last 20 paragraphs, the five strongest held readings (with
their fills), the table's current expectations, the target and the vocabulary, and asks for a
paragraph plus the beat it conveys; a beat draft that does not fit the vocabulary or names an
unknown entity is dropped, the prose kept. `OllamaProseWriter` prompts with the prose alone. Both
use `OLLAMA_WRITER_MODEL` at temperature 0.7, go through the LLM call cache, and share the new
`llm.json_answers.JsonAnswers` (schema-constrained JSON with a prompt fallback) with the ingester,
which now uses it too. Bound as `StoryWriter` and `ProseOnlyStoryWriter`; usage doc
`docs/usage/generate.md`; the `--llm` integration test continues `steward` at t=12.
