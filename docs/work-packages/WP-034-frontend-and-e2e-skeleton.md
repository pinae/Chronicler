# WP-034: Frontend and end-to-end test skeleton

**Milestone:** M8 · **Serves:** RQ2

## Goal
A React frontend and browser tests exist and run in CI, with a first real screen: the list of
chronicles.

## Acceptance criteria
- ADRs record: the frontend build tool, the component test stack, lint and format tooling, the
  e2e tool, and how the frontend reaches the API in development and is served in production.
- `frontend/` is a strict-TypeScript React app; its start page lists chronicles from
  `/api/chronicles/` (title and kind) and shows **No chronicles yet** when there are none.
- Component tests find elements by role, label and text.
- `docs/usage/browse-chronicles.md` describes both scenarios; `e2e/` has a browser test for each.
- CI runs frontend lint, type check, component tests and the e2e tests.

## Dependencies
WP-002, WP-032.

## Out of scope
Any other screen.

## Status
open
