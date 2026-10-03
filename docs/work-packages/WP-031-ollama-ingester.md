# WP-031: Ollama ingester

**Milestone:** M7 · **Serves:** RQ1, RQ4

## Goal
Production ingest: an utterance becomes canonical beats via Ollama, with entity resolution and a
confidence per beat. All fuzziness lives here.

## Acceptance criteria
- `OllamaIngester` requests JSON-schema constrained output derived from the vocabulary; when the
  server lacks it, it falls back to prompted JSON with repair and validation.
- Entity mentions are resolved against existing entities and their aliases; unknown ones become
  new entities; each beat carries a confidence.
- Drafts pass the same `args` validation as any beat; unknown predicates are quarantined, not
  dropped.
- Calls go through the LLM call cache; unit tests use a fake transport.
- Integration tests (`--llm`): a three-sentence utterance yields valid beats; an utterance with
  no narrative content yields zero beats.

## Dependencies
WP-003, WP-023, WP-029.

## Out of scope
- Detecting voiced theories in speech.
- Wrapping media statements as claims (WP-052).

## Notes
- Probably the largest package in M7. If entity resolution grows, split it off before starting.

## Status
open
