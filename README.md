# Chronicler — narrative interpretation engine

A research instrument that keeps a formal, time-indexed record of a narrated world (the
*Chronicle*), matches it against narrative patterns (*Schemas*) and asks a language model what an
audience currently expects. See [`docs/narrative-engine-concept.md`](docs/narrative-engine-concept.md).

## Repository layout

| Path | Contents |
|---|---|
| `backend/` | Django project (`uv`): apps, tests, fixtures |
| `docs/work-packages/` | the planned work, one file per package |
| `docs/decisions/` | architecture decision records |
| `docs/usage/` | user documentation, one file per feature |

## Backend

Requirements: [uv](https://docs.astral.sh/uv/) (it installs Python 3.12 if needed).

```bash
cd backend
uv sync                      # create .venv from uv.lock
uv run pytest                # tests (no database server or network needed)
uv run ruff check .          # lint
uv run ruff format --check . # formatting
uv run mypy .                # type check
```

Running the development server needs PostgreSQL and two environment variables:

```bash
cp .env.example .env         # then edit DJANGO_SECRET_KEY and DATABASE_URL
uv run python manage.py migrate
uv run python manage.py runserver
```
