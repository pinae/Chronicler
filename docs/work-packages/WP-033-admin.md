# WP-033: Admin for all models

**Milestone:** M8 · **Serves:** RQ1, RQ2

## Goal
Every model can be inspected in the Django admin, with the views a researcher needs to debug the
lattice and the LLM calls.

## Acceptance criteria
- Every model is registered in the admin.
- The `Hypothesis` admin shows its fills inline; the `LLMCall` admin shows request and response
  as readable JSON.
- Beats and scope grants are read-only in the admin.
- For a superuser, the list and detail page of every model return 200.
- `docs/usage/admin.md` describes how to inspect hypotheses and LLM calls.

## Dependencies
WP-027, WP-032.

## Out of scope
Editing fact labels (WP-053).

## Status
open
