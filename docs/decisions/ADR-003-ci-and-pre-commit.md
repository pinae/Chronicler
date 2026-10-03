# ADR-003: CI platform and pre-commit hooks

**Status:** accepted (2026-10-03) · **Work package:** WP-002

## Context
Every push and pull request must run the same checks a contributor runs locally (ruff, ruff
format, mypy, pytest), from the lock file. Contributors should get the same feedback before they
commit. The repository lives on GitHub; the backend is a uv project in `backend/` (ADR-001).

## Options considered
- **CI platform:** GitHub Actions (built into the hosting platform, no extra account) vs. an
  external CI service (more setup, nothing gained at this size).
- **Installing uv in CI:** `astral-sh/setup-uv` (official, caches uv and dependencies, reads
  `.python-version` from a working directory) vs. `pip install uv` after `actions/setup-python`.
- **Pre-commit:** the pre-commit framework vs. a hand-written `.git/hooks` script (not versioned,
  no per-hook file filters).
- **mypy hook:** `pre-commit/mirrors-mypy` with django-stubs listed again as
  `additional_dependencies` vs. a local hook running `uv run mypy` in the project environment.

## Decision
- GitHub Actions workflow `.github/workflows/ci.yml`, triggered on every push and pull request,
  running in `backend/`: `uv sync --frozen`, `ruff check`, `ruff format --check`, `mypy`, `pytest`.
- `astral-sh/setup-uv` pinned to a commit SHA (v10.1.0) with caching enabled.
- The pre-commit framework, configured in `.pre-commit-config.yaml` at the root and installed as a
  backend dev dependency: ruff's official hooks (`ruff-check --fix`, `ruff-format`) and local hooks
  that run `uv run mypy` and `uv run pytest` inside the project environment.
- The pytest hook runs the whole backend suite. The concept suggests "changed apps only"; the suite
  takes well under a second today, and selecting apps by changed paths would be logic to maintain.
  Revisit when the suite gets slow.

## Reasoning
- setup-uv's README documents `working-directory` for projects in a subdirectory and recommends SHA
  pinning ([astral-sh/setup-uv](https://github.com/astral-sh/setup-uv)); ruff publishes official
  pre-commit hooks ([astral-sh/ruff-pre-commit](https://github.com/astral-sh/ruff-pre-commit)).
- mirrors-mypy runs in an isolated environment, so django-stubs and the settings module must be
  repeated and kept in sync by hand, and it adds opinionated defaults such as
  `--ignore-missing-imports`; a local hook through uv uses exactly the CI environment
  ([Running mypy in pre-commit](https://jaredkhan.com/blog/mypy-pre-commit),
  [django-stubs#1087](https://github.com/typeddjango/django-stubs/issues/1087),
  [uv template: mypy](https://python-boilerplate.github.io/uv-template/features/code_quality/mypy/),
  [How to set up pre-commit hooks](https://pydevtools.com/handbook/how-to/how-to-set-up-pre-commit-hooks-for-a-python-project/)).
- A core CI for Django runs lint, format check, type check and tests as separate steps so the
  failing step is obvious ([Core CI steps for Django](https://hodovi.cc/blog/core-continuous-integration-ci-steps-for-python-and-django-applications/)).

## Consequences
- Local hooks need `uv` on the contributor's machine (already required by ADR-002).
- The ruff version in `.pre-commit-config.yaml` must be bumped together with the dev dependency.
- Frontend and e2e jobs are added to the same workflow by WP-034.
