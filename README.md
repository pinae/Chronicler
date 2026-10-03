# Chronicler — narrative interpretation engine

A research instrument that keeps a formal, time-indexed record of a narrated world (the
*Chronicle*), matches it against narrative patterns (*Schemas*) and asks a language model what an
audience currently expects. See [`docs/narrative-engine-concept.md`](docs/narrative-engine-concept.md).

## Repository layout

| Path | Contents |
|---|---|
| `backend/` | Django project (`uv`): apps, tests, fixtures |
| `frontend/` | React app (Vite, TypeScript): the GM/writer screens |
| `e2e/` | browser tests (Playwright), one per scenario in `docs/usage/` |
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

Git hooks run the same checks before each commit:

```bash
uv run pre-commit install    # once per clone
```

CI (`.github/workflows/ci.yml`) runs these checks on every push and pull request.

Running the development server needs PostgreSQL and two environment variables:

```bash
cp .env.example .env         # then edit DJANGO_SECRET_KEY and DATABASE_URL
uv run python manage.py migrate
uv run python manage.py runserver
```

## Frontend

Requirements: Node 22.13 or newer.

```bash
cd frontend
npm ci
npm run dev                  # http://localhost:5173, forwards /api to Django on port 8000
npm test                     # component tests
npm run lint && npm run format:check && npm run typecheck
npm run build                # frontend/dist, served by Django under / (ADR-007)
npm run generate:api-types   # after changing the API
```

## Browser tests

```bash
cd e2e
npm ci
npx playwright install chromium   # skip if the browser is pre-installed
npx playwright test               # builds the frontend and starts Django with the e2e settings
```
