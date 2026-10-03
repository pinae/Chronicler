# Replaying a story

Runs a fixture story (`backend/fixtures/stories/<slug>/`) through the whole pipeline (ingest, beats,
scope, matcher and readouts) one utterance at a time, and writes a run file with the lattice and the
expectations at every `t` (format: `docs/run-file-format.md`).

## Before you start
- The backend is installed and migrated (`cd backend && uv run python manage.py migrate`).
- For readouts from the language model: the Ollama settings are configured (see
  `docs/usage/ollama-smoke-check.md`).

## Replay with the language model
1. In `backend/`, run `uv run python manage.py replay steward`.

**Result:** the command prints `Replayed 24 beats of steward; run file: …/evaluation/runs/steward/<timestamp>.json`.
Running it again asks the language model nothing: every readout is answered from the call log.

## Replay without a language model
1. Run `uv run python manage.py replay steward --reader uniform`.

**Result:** the same message; every readout in the run file spreads its probability evenly over the
candidates (`"reader": "UniformReader"`).

2. Run `uv run python manage.py replay steward --reader none`.

**Result:** the same message; the run file contains the lattice at every `t` and no expectations
(`"reader": null`).

## Replay part of a story
1. Run `uv run python manage.py replay steward --reader none --until 10`.

**Result:** `Replayed 10 beats of steward; …`.
