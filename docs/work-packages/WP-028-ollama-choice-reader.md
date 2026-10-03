# WP-028: Ollama choice reader

**Milestone:** M6 · **Serves:** RQ1

## Goal
Production readouts: a multiple-choice prompt to Ollama whose answer distribution is read from
the first token's logprobs.

## Acceptance criteria
- `OllamaChoiceReader` builds a prompt that lists candidates with single-token labels plus a
  "none" label and asks for the label only; it uses no constrained decoding.
- The distribution comes from `top_logprobs` of the first generated token, requested with at
  least as many entries as candidates; the result reports the renormalized distribution and the
  probability mass outside the candidate labels.
- Every call goes through the LLM call cache, with the full prompt, candidate set and included
  beats recorded.
- Unit tests use a fake transport with canned logprobs.
- Integration test (`--llm`): over four labels the renormalized distribution sums to ≈ 1, and the
  "none" label gets non-zero mass on an empty chronicle.

## Dependencies
WP-003, WP-023, WP-024.

## Out of scope
- The sampling fallback (§8.3): only needed if the smoke check shows no logprobs support; it then
  becomes its own package.
- Bayes factors (WP-044).

## Status
open
