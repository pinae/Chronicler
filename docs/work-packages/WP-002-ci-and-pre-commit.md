# WP-002: CI pipeline and pre-commit hooks

**Milestone:** M0 · **Serves:** infrastructure

## Goal
Every push and pull request is checked with the same commands a contributor runs locally,
so a red suite is caught before review.

## Acceptance criteria
- A CI workflow runs on every push and pull request: `uv sync --frozen`, `ruff check`,
  `ruff format --check`, `mypy` and `pytest` in `backend/`.
- CI fails when any of those steps fails (verified once on a throwaway branch containing a
  lint error, a type error and a failing test).
- A pre-commit configuration runs ruff (lint and format), mypy and pytest for the changed apps;
  the root `README.md` explains how to install it.
- ADR-003 records the CI platform and the pre-commit approach.

## Dependencies
WP-001.

## Out of scope
- Frontend and e2e jobs (added in WP-034).
- Deployment.
- Running `llm` integration tests in CI (they need the GPU server).

## Status
open
