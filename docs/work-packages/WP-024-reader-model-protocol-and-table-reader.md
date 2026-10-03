# WP-024: Reader model protocol, TableReader and dependency registry

**Milestone:** M6 · **Serves:** RQ1

## Goal
The reader model is an injected interface with a deterministic, table-backed implementation for
tests, chosen through a small settings-driven registry.

## Acceptance criteria
- `ReaderModel` is a `typing.Protocol` with a choice readout (context and question →
  probabilities over candidate labels) and a Bayes factor (one beat under two
  hypothesis-conditioned contexts → log Bayes factor).
- `TableReader` answers from a table keyed by `(t, question)` and raises a descriptive error on
  an unanticipated `(t, question)`.
- `narrative_engine/di.py` resolves injected interfaces from settings; test settings bind
  `ReaderModel → TableReader`.
- The Bayes-factor service passes the identical beat object under both hypotheses (asserted
  with a recording fake).

## Dependencies
WP-015.

## Out of scope
Question construction (WP-025), context building (WP-026), Ollama implementations
(WP-028, WP-044).

## Status
open
