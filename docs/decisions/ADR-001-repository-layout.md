# ADR-001: Repository layout

**Status:** accepted (2026-10-03) · **Work package:** WP-001

## Context
`CLAUDE.md` describes a monorepo with a Django backend in `backend/`, a React frontend in
`frontend/` and browser tests in `e2e/`. The concept (`docs/narrative-engine-concept.md` §10)
was written for a Django project at the repository root, with a Django app `gm_ui` for the
GM/writer views and story fixtures in `fixtures/stories/`. The two must be reconciled before the
first line of code. Constraints: one small team, TDD, readable structure, a newcomer should find
things where they expect them.

## Options considered
1. **Django at the root, React in a subfolder.** Matches the concept's commands verbatim, but mixes
   Python tooling files with the frontend and contradicts `CLAUDE.md`.
2. **`backend/` and `frontend/` side by side, each with its own tooling.** The most common layout
   for Django + React monorepos; each side keeps its native tools (`uv`, `npm`) and lock file.
3. **uv workspace at the root with the backend as a member.** Useful when several Python packages
   share one environment; we have exactly one Python project, so it adds indirection for nothing.

## Decision
Option 2.

- `backend/` is the `uv` project: `pyproject.toml`, `uv.lock`, `.python-version`, `manage.py`, the
  `narrative_engine` project package and the apps `chronicle`, `schemas`, `matching`, `reader`,
  `llm`, `evaluation`, `gm_ui`. Everything the concept places at the root lives here, including
  `fixtures/stories/` and `evaluation/runs/`. Commands from the concept run inside `backend/`.
- `gm_ui` serves `healthz` and the JSON API; the GM/writer screens are React components in
  `frontend/`. `frontend/` and `e2e/` are created by WP-034, when the first screen needs them.
- `docs/` stays at the root: work packages, ADRs, usage documentation and the concept.
- `docs/narrative-engine-concept.md` plays the role of `docs/idea.md` referenced in `CLAUDE.md`.

## Reasoning
Separate `backend/` and `frontend/` directories are the layout most Django + React monorepos use
and recommend, with docs and CI configuration at the root:
[Vinta Software: Django React monorepo](https://www.vintasoftware.com/blog/django-react-monorepo),
[app-monorepo-boilerplate (Vite + Django)](https://github.com/awwester/app-monorepo-boilerplate),
[GitHub community discussion on monorepo folders](https://github.com/orgs/community/discussions/168684).
uv workspaces exist for several interdependent Python packages
([uv workspaces in a monorepo](https://matekole.com/tils/monorepo-uv-workspaces/),
[astral-sh/uv#10960](https://github.com/astral-sh/uv/issues/10960)); with one Python project a
plain uv project in `backend/` is simpler.

## Consequences
- Every backend command runs from `backend/` (`cd backend && uv run pytest`); CI sets that working
  directory.
- Paths in the concept (`schemas/library/`, `fixtures/stories/`) are relative to `backend/`.
- The frontend can later get its own toolchain without touching Python configuration.
