# WP-023: LLM call log and cache

**Milestone:** M6 · **Serves:** RQ1–RQ4 (reproducibility)

## Goal
Every LLM request is stored, and identical requests are served from the database, so
evaluation runs are reproducible and re-runs are free.

## Acceptance criteria
- `LLMCall` exists with the fields from §8.4.
- `request_hash` is the SHA-256 of model, endpoint and the canonical JSON of the parameters;
  key order does not change the hash.
- An identical request is served from the table without touching the transport (asserted with
  a fake transport).
- A changed parameter (e.g. temperature or sampling draw index) makes a new call.
- The server version is stored with each call.
- A test fails if any module outside the `llm` app imports the `ollama` package.

## Dependencies
WP-003.

## Out of scope
Specific estimators and ingesters (WP-028, WP-031, WP-044).

## Status
done

## Summary
`LLMCall` stores every request with its response and server version. `CachedOllama(transport)`
hashes the endpoint and the canonical JSON of the request (model included, key order irrelevant;
SHA-256). It answers an identical request from the table without touching the server and returns
the `LLMCall` row, so callers keep provenance. A sampling draw index is hashed but not sent; failed
requests are not logged, and the server version is asked once per client. A test fails if any
module outside `llm` imports `ollama`.
