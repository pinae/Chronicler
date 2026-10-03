# WP-002: CI pipeline and pre-commit hooks

**Milestone:** M0 · **Serves:** infrastructure

## Goal
Every push and pull request is checked with the same commands a contributor runs locally,
so a red suite is caught before review.

## Acceptance criteria
- A CI workflow runs on every push and pull request: `uv sync --frozen`, `ruff check`,
  `ruff format --check`, `mypy` and `pytest` in `backend/`.
- CI fails when any of those steps fails: each command exits non-zero on a planted lint error,
  formatting error, type error and failing test (checked locally, since pushing a throwaway
  branch is not allowed).
- A pre-commit configuration runs ruff (lint and format), mypy and pytest for the backend;
  the root `README.md` explains how to install it.
- ADR-003 records the CI platform and the pre-commit approach.

## Dependencies
WP-001.

## Out of scope
- Frontend and e2e jobs (added in WP-034).
- Deployment.
- Running `llm` integration tests in CI (they need the GPU server).

## Status
done

## Summary
`.github/workflows/ci.yml` runs `uv sync --frozen`, ruff, ruff format, mypy and pytest in `backend/`
on every push and pull request, using `astral-sh/setup-uv` pinned by SHA. `.pre-commit-config.yaml`
runs ruff's official hooks plus local `uv run` hooks for mypy and pytest. Every command was shown
to fail on a planted error. ADR-003 explains the choices, including running the whole (fast) pytest
suite instead of only changed apps.
