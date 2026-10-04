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

What follows from it (revised with WP-063, see below):

- The server returns token logprobs, so readouts (WP-028) need no sampling fallback. With at most
  20 top logprobs, a question pages its candidates at 20 labels (`READER_MAX_CANDIDATES`).
- Structured output by JSON schema works, as the ingester (WP-031) needs.
- Ollama does not score prompt tokens, so the Bayes-factor estimator (WP-044) cannot read
  log P(beat | context) from the prompt. The remaining options are a vLLM or llama.cpp sidecar, or
  forced scoring token by token; WP-044 needs a measurement against the server to choose.

### Why the readouts of this run were not usable (WP-063)

`gemma4:e4b` is a thinking model, and Ollama turns thinking on for such models unless a request says
`think: false` (`server/routes.go`, `GenerateHandler`). Readouts asked for one token, so that token
was the start of the model's reasoning, not an answer letter, and the answer distributions were
mostly empty. This explains why the steward run scored a Brier score of 0.316 against the annotated
belief, worse than the uniform reader's 0.047 (an answer with no mass on any letter scores 0.38).
The smoke check of this run could not see it: it only checked that logprobs exist.

Since WP-063 readouts say `think: false`, `truncate: false` and use neutral sampling (temperature 1,
no repeat penalty, which would lower the answer letters because they all appear in the prompt), and
the smoke check measures how much probability lands on the answer letters, with thinking off and
with the model's defaults. **Re-run `uv run python -m llm.smoke` and replace the output above.**
Old readouts can be checked with `manage.py inspect_readouts` (`docs/usage/inspect-readouts.md`);
replaying a story asks again, because the changed requests are not answered from the call log.
