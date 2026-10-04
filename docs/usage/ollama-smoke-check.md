# Ollama smoke check

Checks whether the configured Ollama server and models support what the engine needs: logprobs for
readouts, structured JSON output for ingest, and prompt logprobs for Bayes factors. Run it once per
server or model change and commit the output to `docs/llm-smoke.md`.

## Before you start
- The backend is installed (`cd backend && uv sync`) and `backend/.env` contains
  `DJANGO_SECRET_KEY` and `DATABASE_URL` (see `backend/.env.example`); the database runs
  (`docker compose up -d` in the repository root, see the README).
- The Ollama server is running and the models are pulled on it.

## Check the server
1. In `backend/`, set `OLLAMA_BASE_URL=http://gpu-box:11434` and `OLLAMA_READER_MODEL=qwen3:32b`
   (and `OLLAMA_INGEST_MODEL` and `OLLAMA_WRITER_MODEL` if they differ) in `.env` or the environment.
2. Run `uv run python -m llm.smoke`.

**Result:** the command prints `server version: …`, then for each model a block such as

```
model: qwen3:32b
  logprobs: yes
  top_logprobs max: 20
  json-schema: yes
  prompt-logprobs: no
```

and exits with status 0.

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
