# WP-044: Production Bayes-factor estimator

**Milestone:** R1 (deferred decision, §13) · **Serves:** RQ1

## Goal
Bayes factors computed by a real model, so retrospective fit can be measured on real stories.

## Acceptance criteria
- An ADR chooses the backend, based on the WP-003 smoke result and a measurement on one fixture
  story: Ollama prompt logprobs (if exposed), a vLLM / llama.cpp sidecar, or token-by-token
  forced scoring.
- The chosen estimator implements the `ReaderModel` Bayes factor and goes through the LLM call
  cache.
- Integration test (`--llm`): identical contexts give a log Bayes factor of ≈ 0.

## Dependencies
WP-003, WP-028, WP-043.

## Out of scope
Weight calibration (deferred, §13).

## Status
blocked

The smoke result is in (`docs/llm-smoke.md`, 2026-10-04): Ollama 0.22.1 with `gemma4:e4b` gives
no prompt logprobs, so the first option is out. Choosing between a sidecar and forced scoring
needs a measurement against the deployed server, which the development environment cannot reach.
Until then `OllamaChoiceReader.beat_log_likelihood` raises `NotImplementedError`, and replays record
`bayes_factors: null`, which `evaluate` shows as `n/a` (WP-041, WP-042).
