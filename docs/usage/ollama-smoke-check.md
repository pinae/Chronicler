# Ollama smoke check

Checks whether the configured Ollama server and models support what the engine needs: real token
probabilities (logprobs) for readouts, structured JSON output for ingest, and prompt logprobs for
Bayes factors. It also measures what readouts depend on: how much probability the model puts on the
answer letters when it is asked as readouts ask (thinking off, neutral sampling) and as it would
answer by default. Run it once per server or model change and commit the output to
`docs/llm-smoke.md`.

## Before you start
- The backend is installed (`cd backend && uv sync`) and `backend/.env` contains
  `DJANGO_SECRET_KEY` and `DATABASE_URL` (see `backend/.env.example`); the database runs
  (`docker compose up -d` in the repository root, see the README).
- The Ollama server is running and the models are pulled on it.

## Check the server
1. In `backend/`, set `OLLAMA_BASE_URL=http://gpu-box:11434` and `OLLAMA_READER_MODEL=gemma4:e4b`
   (and `OLLAMA_INGEST_MODEL` and `OLLAMA_WRITER_MODEL` if they differ) in `.env` or the environment.
2. Run `uv run python -m llm.smoke`.

**Result:** the command prints `server version: …`, then for each model a block such as

```
model: gemma4:e4b
  thinks unless told not to: yes
  context length: 131072 (requests ask for 16384)
  quantization: Q4_K_M
  logprobs: yes
  top_logprobs max: 20
  answer-letter mass, thinking off: 98.7%
  answer-letter mass, model defaults: 0.4%
  logprobs depend on temperature: no
  json-schema: yes
  prompt-logprobs: no
```

and exits with status 0. (The numbers above illustrate the format; yours depend on the model.)

What the lines mean:

| Line | Means | Good value |
|---|---|---|
| thinks unless told not to | the model reasons before it answers when a request does not say `think: false`; readouts always say it | either |
| context length | the most tokens the model can read; requests ask for `OLLAMA_NUM_CTX`, and a longer prompt fails instead of being cut | larger than the second number |
| quantization | how the weights are compressed; stronger compression blurs probabilities a little | any |
| logprobs, top_logprobs max | the server returns token probabilities, and how many alternatives per token | yes, 20 |
| answer-letter mass, thinking off | the probability that the first token of a two-letter multiple-choice answer is A or B, asked as readouts ask | close to 100% |
| answer-letter mass, model defaults | the same with the model's defaults; a thinking model puts its first token on its reasoning, which is why readouts turn thinking off | anything |
| logprobs depend on temperature | whether the server scales the reported probabilities by the temperature; readouts use temperature 1, so either way they see the model's own distribution | either |
| json-schema | structured output for ingest | yes |
| prompt-logprobs | probabilities of the prompt's tokens, which would give Bayes factors in one call; without them they are scored token by token (ADR-009) | either |

If **answer-letter mass, thinking off** is low (say below 50%), readouts see mostly other tokens and
their answers mean little: check the model name, update Ollama, or try another model.

## Server not configured
1. Remove `OLLAMA_BASE_URL` from `.env` and the environment.
2. Run `uv run python -m llm.smoke`.

**Result:** the command prints `OLLAMA_BASE_URL is not set; point it to the Ollama server, e.g.
http://gpu-box:11434` and exits with status 2.

## Server unreachable
1. Set `OLLAMA_BASE_URL=http://127.0.0.1:9` (nothing listens there).
2. Run `uv run python -m llm.smoke`.

**Result:** the command prints `cannot reach the Ollama server at http://127.0.0.1:9: …` and exits
with status 1.

## Integration tests
Run `uv run pytest --llm` with `OLLAMA_BASE_URL` and `OLLAMA_READER_MODEL` (and
`OLLAMA_INGEST_MODEL`, `OLLAMA_WRITER_MODEL`) set in the environment, e.g.
`export OLLAMA_BASE_URL=http://gpu-box:11434`. The tests do not read `backend/.env`, so that a
developer's file cannot change what they check. Without `OLLAMA_BASE_URL` the integration tests are
reported as skipped.
