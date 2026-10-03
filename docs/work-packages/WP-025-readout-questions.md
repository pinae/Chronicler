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
done

## Summary
`reader/questions.py` builds deterministic questions. `next_open_step` takes the first unfilled
required step, then the first unfilled optional one. The question phrases that step's first pattern
with the per-predicate templates in `reader/templates.py` (every vocabulary predicate has one),
showing the first unbound role as a blank and step references as the text of their beat. Candidates
are the entities of the open role's kind introduced by `t`, ordered by introduction and id and
labelled A, B, … plus "nothing like this yet". When every role of the step is bound, the question is
whether it happens next. Lists longer than `max_candidates` are paged, each page with its own
"nothing yet". `entities_in_view(chronicle, player, t)` lists the entities mentioned in the beats an
audience saw.
