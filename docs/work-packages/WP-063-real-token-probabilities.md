# WP-063: Readouts read the model's real answer probabilities

**Milestone:** M6 (follow-up) · **Serves:** RQ1, RQ2

## Goal
Readouts use the language model's real token probabilities for the answer, and a user can see those
probabilities and check the model and server configuration that they depend on.

## Acceptance criteria
- Readout requests turn thinking off (`think: false`), forbid silent truncation (`truncate: false`)
  and sample neutrally (temperature 1, no repeat, presence or frequency penalty), so the reported
  logprobs are the model's own distribution over the answer.
- A readout whose response still holds thinking is an error that says so.
- Ingest and writer requests also fail instead of losing the beginning of an over-long prompt.
- The transport sends every request field to the native API as it is, and asks `/api/show` what the
  server knows about a model.
- The smoke check reports whether the model thinks by default, its context length against
  `OLLAMA_NUM_CTX`, its quantization, the probability mass on the answer letters with thinking off
  and with the model's defaults, and whether logprobs depend on the temperature.
- `manage.py inspect_readouts <chronicle or story> --t T [--audience PLAYER]` prints, per stored
  readout, the question, the prompt length, the first token, the raw alternatives with their
  probabilities, the answers and the share outside the letters, and flags readouts in which the
  model was thinking.

## Dependencies
WP-003, WP-024, WP-028.

## Out of scope
Bayes factors (WP-044); choosing a model (the smoke check and `evaluate` give the evidence).

## Status
done

## Summary
The owner's smoke run showed logprobs working, yet readouts scored worse than the uniform reader.
Ollama turns thinking on for thinking models such as `gemma4:e4b` unless asked not to, so the one
token a readout asked for was the start of the model's reasoning. Readouts now share
`llm.next_token.next_token_request` with the smoke check, which measures the answer-letter mass
both ways; the transport posts plain JSON over httpx (the official client cannot send `truncate`),
and `inspect_readouts` shows the raw numbers behind every expectation. ADR-004 is amended.
