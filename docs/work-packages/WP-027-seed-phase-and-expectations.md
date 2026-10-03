# WP-027: Seed phase and expectations

**Milestone:** M6 · **Serves:** RQ1, RQ2

## Goal
After each beat, the matcher asks the reader model what the audience expects next for each live
hypothesis, and stores the answers per `t`.

## Acceptance criteria
- `Expectation` exists with the fields from §4.
- The Seed phase asks the reader model about every live hypothesis with open steps, and stores an
  expectation with `computed_at_t`, `for_player` (empty = whole table), candidates as
  `binding_delta` with `p` plus the null candidate, and `llm_call` when the reader made one.
- A per-player readout receives only `visible_to(player, t)` (asserted on the context passed to a
  recording reader).
- Expectations from earlier `t` are kept, never overwritten.

## Dependencies
WP-023, WP-024, WP-025, WP-026.

## Out of scope
Ollama-backed readouts (WP-028).

## Status
open
