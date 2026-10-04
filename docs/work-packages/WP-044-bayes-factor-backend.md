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
done

## Summary
The owner's server gives no prompt logprobs (Ollama 0.22.1), so ADR-009 chooses forced scoring
through the top logprobs of generated tokens: the story so far is sent raw, ending where the beat's
line begins, and the beat's text is walked token by token, taking the longest alternative that
continues it and charging an upper bound where none does. `OllamaChoiceReader.beat_log_likelihood`
uses it, so replays with a model record Bayes factors and `evaluate` reports retrospective fit. The
measurement on the deployed server is the `--llm` integration test; a vLLM sidecar with prompt
logprobs is the exact alternative if the bounds turn out too coarse.
