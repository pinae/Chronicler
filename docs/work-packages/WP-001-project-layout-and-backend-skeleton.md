# WP-001: Monorepo layout and backend skeleton

**Milestone:** M0 · **Serves:** infrastructure for RQ1–RQ4

## Goal
Create the repository layout from `CLAUDE.md` and a runnable, empty Django backend,
so every later package has a place to land and a green test suite to start from.

## Acceptance criteria
- `backend/` is a `uv` project with `requires-python = ">=3.12"`, the runtime and dev
  dependencies from concept §10, and a committed `uv.lock`.
- The Django project `narrative_engine` has settings split into `base`, `dev` and `test`;
  `test` uses in-memory SQLite, `dev` reads PostgreSQL connection settings from the environment.
- The apps `chronicle`, `schemas`, `matching`, `reader`, `llm`, `evaluation` and `gm_ui`
  exist and are installed.
- `test_healthz`: a `GET` on the URL named `healthz` returns 200 (written first, seen failing).
- `uv run pytest`, `uv run ruff check`, `uv run ruff format --check` and `uv run mypy` pass
  from `backend/`, configured as in concept §10.
- `docs/decisions/` contains ADR-001 (repository layout) and ADR-002 (Python toolchain);
  `docs/usage/` exists with a README pointing to the `usage-docs` skill.
- A root `README.md` explains how to install the backend and run its checks.

## Dependencies
None.

## Out of scope
- CI and pre-commit hooks (WP-002).
- Ollama settings (WP-003).
- Any domain model.
- `frontend/` and `e2e/`: scaffolded in WP-034, when the first screen needs them.

## Notes
- The concept (§10) puts the Django project at the repository root and the GM UI in a Django
  app; `CLAUDE.md` puts Django in `backend/` next to a React `frontend/`. Proposed
  reconciliation for ADR-001: everything the concept describes lives under `backend/`
  (including `fixtures/stories/` and `evaluation/runs/`), the `gm_ui` app serves `healthz`
  and the JSON API, and the GM/writer screens live in `frontend/`.
- ADR-002 mostly records choices the concept already makes (uv, Django 5.2 LTS,
  pytest-django, factory-boy, ruff for lint and format, mypy with django-stubs,
  django-environ); versions and configuration still get checked per the `infra-decision` skill.
- `docs/idea.md`, referenced by `CLAUDE.md`, does not exist; `docs/narrative-engine-concept.md`
  serves as the product description.

## Status
open
