# WP-033: Admin for all models

**Milestone:** M8 · **Serves:** RQ1, RQ2

## Goal
Every model can be inspected in the Django admin, with the views a researcher needs to debug the
lattice and the LLM calls.

## Acceptance criteria
- Every model is registered in the admin.
- The `Hypothesis` admin shows its fills inline; the `LLMCall` admin shows request and response
  as readable JSON.
- Beats and scope grants (and every other record the engine derives or logs) are read-only in the admin.
- For a superuser, the list and detail page of every model return 200.
- `docs/usage/admin.md` describes how to inspect hypotheses and LLM calls.

## Dependencies
WP-027, WP-032.

## Out of scope
Editing fact labels (WP-053).

## Status
done

## Summary
Every model of the seven apps is registered (checked by a test). Only chronicles, players and
entities can be edited. Beats, scope grants, entity attributes, utterances, schemas and steps (the
YAML is the spec), hypotheses, fills, expectations, LLM calls and usage events use
`narrative_engine.read_only_admin.ReadOnlyAdmin`. The hypothesis page lists its fills inline, and
the LLM call page shows request, response and metadata as indented JSON. For a superuser every list
and detail page returns 200. `docs/usage/admin.md` describes the workflows.
