# WP-025: Readout questions and candidates

**Milestone:** M6 · **Serves:** RQ1

## Goal
For a live hypothesis and an open step, build a deterministic multiple-choice question about
which entity will fill it.

## Acceptance criteria
- The question text comes from a template per predicate of the step's pattern.
- Candidates are the entities of the open role's kind that appear in the asking audience's view
  at `t` and were introduced at or before `t`, plus one "none / nothing yet" candidate.
- Candidate order is deterministic, and labels (`A`, `B`, …) are stable across calls with the
  same inputs.
- Candidate lists longer than a configured maximum (the server's `top_logprobs` limit) are split
  into pages.

## Dependencies
WP-009, WP-015.

## Out of scope
Asking the question and storing answers (WP-027).

## Notes
- When several steps are open, which one is asked? Proposed: the open required step with the
  lowest `order`. Decide here.

## Status
open
