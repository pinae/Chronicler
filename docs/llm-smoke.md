# Ollama smoke check results

Output of `uv run python -m llm.smoke` against the deployed server (see
[`docs/usage/ollama-smoke-check.md`](usage/ollama-smoke-check.md)). The results decide the
Bayes-factor backend (WP-044) and whether readouts need the sampling fallback (WP-028).

## Latest run

2026-10-04, run by the project owner against their Ollama server, reader and ingest model
`gemma4:e4b`:

```
server version: 0.22.1
model: gemma4:e4b
  logprobs: yes
  top_logprobs max: 20
  json-schema: yes
  prompt-logprobs: no
```

What follows from it:

- Readouts (WP-028) can use token logprobs directly; the sampling fallback is not needed. With
  at most 20 top logprobs, a question pages its candidates at 20 labels (`READER_MAX_CANDIDATES`).
- Structured output by JSON schema works, as the ingester (WP-031) needs.
- Ollama does not score prompt tokens, so the Bayes-factor estimator (WP-044) cannot read
  log P(beat | context) from the prompt. The remaining options are a vLLM or llama.cpp sidecar, or
  forced scoring token by token; WP-044 needs a measurement against the server to choose.
