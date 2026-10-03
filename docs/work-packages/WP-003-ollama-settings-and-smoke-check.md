# WP-003: Ollama settings, opt-in integration tests and smoke check

**Milestone:** M0 (pulled forward from §8.2) · **Serves:** RQ1–RQ4 (LLM infrastructure)

## Goal
Make the external Ollama server configurable and checkable before any LLM-backed code exists,
so its capabilities (logprobs, structured output, prompt logprobs) are known early. The smoke
result decides the Bayes-factor backend (WP-044) and whether the choice readout needs its
sampling fallback (WP-028).

## Acceptance criteria
- `settings/base.py` reads `OLLAMA_BASE_URL`, `OLLAMA_READER_MODEL`, `OLLAMA_INGEST_MODEL`,
  `OLLAMA_NUM_CTX`, `OLLAMA_KEEP_ALIVE` and `OLLAMA_TIMEOUT_S` from the environment (§8.1);
  `settings/test.py` sets none of them.
- The `ollama` client version is pinned in `pyproject.toml`.
- `uv run pytest` deselects tests marked `llm`; `uv run pytest --llm` runs them; an `llm` test
  is skipped, not failed, when `OLLAMA_BASE_URL` is unset.
- In the default test run, any attempt to open a network connection fails the test.
- `uv run python -m llm.smoke` prints server version, model, logprobs yes/no, `top_logprobs`
  maximum, JSON-schema output yes/no and prompt logprobs yes/no. Unit tests drive it with a
  fake transport for a fully capable and for a minimal server.
- `docs/llm-smoke.md` contains the smoke output from the deployed server and model.

## Dependencies
WP-001.

## Out of scope
- The call log and cache (WP-023); smoke calls are not cached.
- Any reader or ingester implementation.

## Notes
- The last criterion needs the deployed GPU server. If the development environment cannot
  reach it, the human runs the command and commits the output.
- How network access is blocked in tests (a socket-guard fixture or a plugin) is a tooling
  choice → ADR.

## Status
open
