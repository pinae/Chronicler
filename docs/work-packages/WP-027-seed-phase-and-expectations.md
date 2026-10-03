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
done

## Summary
`Expectation` stores, per hypothesis, open step, `computed_at_t` and audience: the question text, the
candidates (label, text, `binding_delta` or `null`, `p`), the mass outside the candidates and the
`LLMCall`. `reader.expectations.seed_expectations(chronicle, t, audience, reader, context_builder)`
asks about every live hypothesis of the audience's lattice. Each readout's context comes from the
context builder, so a player's readout only sees `visible_to(player, t)`. Earlier rows are never
overwritten. Decisions: the Seed phase runs after Maintain, so refuted hypotheses are not asked about.
An audience is only asked about hypotheses whose fills it saw and whose bound entities it knows, so
questions cannot give away GM-only beats. Each candidate page becomes one row.
