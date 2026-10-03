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
done

## Summary
ADR-007 records the choices: Vite 8, React 19, React Router 8 and strict TypeScript 5.9. Tests use
Vitest with Testing Library; linting uses ESLint (typescript-eslint, react-hooks) and Prettier. API
types are generated from the OpenAPI schema, and Playwright 1.56.1 runs in `e2e/`. Development uses
Vite's proxy; production and browser tests use Django serving the build through WhiteNoise, with a
catch-all for client routes and a 503 hint when the build is missing. The start page lists chronicles
with kind and beat count and shows **No chronicles yet** when empty; component tests cover list, empty
and error states. `docs/usage/browse-chronicles.md` has a browser test per runnable scenario, against
a throwaway database seeded by `manage.py seed_e2e`. CI has frontend and e2e jobs.
