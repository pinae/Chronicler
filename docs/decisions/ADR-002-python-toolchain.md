# ADR-002: Python toolchain

**Status:** accepted (2026-10-03) · **Work package:** WP-001 · **Amended:** 2026-10-04 (WP-062),
Django 6.1 instead of 5.2 LTS, see *Amendment* below.

## Context
The concept (§10, §12) already fixes most of the Python toolchain: `uv`, Django LTS, pytest with
pytest-django, ruff, mypy with django-stubs, django-environ, PostgreSQL in development and SQLite in
tests, Python ≥ 3.12 as a floor. This ADR records the concrete versions and configuration, and the
checks made, so later packages do not re-decide them.

## Options considered
- **Django version:** 5.2 LTS (supported until April 2028) vs. 6.1 (newest feature release,
  shorter support). The concept asks for the current LTS.
- **Formatter:** ruff format vs. black. Ruff is already the linter; one tool fewer.
- **Settings:** one `settings.py` with `if` branches vs. a `settings/` package
  (`base`, `dev`, `test`) vs. django-split-settings. The package is the conventional, dependency-free
  choice and is what the concept prescribes.
- **Type checking:** mypy + django-stubs vs. pyright. django-stubs ships a mypy plugin that
  understands models and querysets; the concept prescribes it.

## Decision
- **Python 3.12** in `.python-version`, `requires-python = ">=3.12"`. Pinning the floor locally keeps
  3.13-only features out (concept §10).
- **uv** for everything: `uv add`, `uv run`, committed `uv.lock`, `uv sync --frozen` in CI.
- **Django `>=5.2,<5.3`** (LTS) with **psycopg 3** (binary) for PostgreSQL.
- **django-environ** reads environment variables; `settings/base.py` holds what is common,
  `settings/dev.py` reads `DJANGO_SECRET_KEY`, `DATABASE_URL` (and later `OLLAMA_*`) from the
  environment or `backend/.env`, and `settings/test.py` reads nothing from the environment and uses
  in-memory SQLite.
- **pytest + pytest-django**; tests live in `<app>/tests/`, files named `test_*.py`.
- **ruff** for linting (rules `E, W, F, I, B, UP, SIM, DJ, PT`) and formatting, line length 110.
- **mypy + `django-stubs[compatible-mypy]` 5.2.x**: the `compatible-mypy` extra pins a mypy range
  the stubs are tested with. Public functions must be typed (`disallow_untyped_defs`); tests and
  migrations are exempt.

## Reasoning
- Django 5.2 is the current LTS with extended support until April 2028; 6.2 LTS follows in
  April 2027 ([Django downloads](https://www.djangoproject.com/download/),
  [endoflife.date/django](https://endoflife.date/django)).
- A `settings/` package with `base`, `development`/`dev` and `test` modules plus django-environ for
  typed environment values and `DATABASE_URL` parsing is the most frequently recommended pattern
  ([Django Stars: configuring settings](https://djangostars.com/blog/configuring-django-settings-best-practices/),
  [env.dev: Django environment variables](https://env.dev/guides/django-env-variables),
  [django-environ](https://pypy-django.github.io/backend/package/django-environ/)).
- uv + ruff + mypy + django-stubs is the common modern Django setup; django-stubs recommends
  installing the `compatible-mypy` extra so mypy and the plugin stay in step
  ([Set up a Django project with uv](https://pydevtools.com/handbook/tutorial/set-up-a-django-project-with-uv/),
  [Configure mypy and django-stubs in a uv project](https://pydevtools.com/handbook/how-to/how-to-configure-mypy-and-django-stubs-in-a-uv-project/),
  [Configure Ruff for Django](https://pydevtools.com/handbook/how-to/how-to-configure-ruff-for-django/)).
- Versions were checked on PyPI on 2026-10-03: Django 5.2.17, django-stubs 5.2.9 (mypy < 1.20),
  pytest 9.1, pytest-django 4.14, ruff 0.16, django-environ 0.14, psycopg 3.3.

## Consequences
- Upgrading to Django 6.2 LTS (after April 2027) means bumping Django and django-stubs together.
- The development server needs `DJANGO_SECRET_KEY` and `DATABASE_URL`; `backend/.env.example`
  shows the expected values. Tests need nothing.

## Amendment (2026-10-04, WP-062): Django 6.1
The project owner asked for a recent Django 6.x. The project now runs on **Django `>=6.1.1,<6.2`**
with **django-stubs 6.1.x**; everything else above stands. 6.1 is the newest feature release (6.1.1
on PyPI, 2026-10-04). Under Django's support policy the latest two feature releases receive
security fixes, so 6.1 is covered until the release after 6.2 LTS (about the end of 2027); moving on
to 6.2 LTS after its release in April 2027 keeps the original intent of running an LTS.

The upgrade needed no code changes: the settings already set `DEFAULT_AUTO_FIELD` (6.0 changed its
default), the project uses none of the APIs changed in 6.0 and 6.1 (custom expressions, email
internals, `first()` after a cleared ordering, combined querysets with default ordering), no
migration is generated and the suite passes on SQLite and PostgreSQL 18 (release notes:
[6.0](https://github.com/django/django/blob/main/docs/releases/6.0.txt),
[6.1](https://github.com/django/django/blob/main/docs/releases/6.1.txt)).
