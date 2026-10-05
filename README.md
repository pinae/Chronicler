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

Running the development server needs PostgreSQL. `docker-compose.yml` in the repository root
starts one whose credentials match `backend/.env.example` (ADR-008):

```bash
docker compose up -d         # in the repository root; data stays in a Docker volume
cd backend
cp .env.example .env         # then set DJANGO_SECRET_KEY, and the OLLAMA_* lines for a language model
uv run python manage.py migrate
uv run python manage.py runserver
```

`docker compose down` stops the database (`down -v` also deletes its data). Every setting can be
given in `backend/.env` or, taking precedence, in the environment. The tests run on SQLite and need
no database server; to run them on PostgreSQL as CI does: `uv run pytest --ds=narrative_engine.settings.test_postgres`.

## Trying it out

**Start with the guided tour, [`docs/usage/guided-tour.md`](docs/usage/guided-tour.md):** *Macbeth*
as a roleplaying session and Kleist's *The Broken Jug* as a pen-and-paper adventure, step by step,
with what you should see on every screen and why. It tells you whether the engine reads two
well-known plots the way you do.

Everything below works without a language model (`--reader uniform` is the know-nothing
baseline). Each step links the usage doc that describes it in detail. Start the database first
(see above).

```bash
cd backend
uv run python manage.py migrate
uv run python manage.py load_schemas                          # docs/usage/schema-library.md
uv run python manage.py replay steward --reader uniform --per-player   # docs/usage/replay.md
uv run python manage.py replay ferryman --reader uniform
uv run python manage.py evaluate steward                      # docs/usage/evaluate.md
uv run python manage.py report steward ferryman --output /tmp/rq1.md   # docs/usage/report.md
cd .. && corepack enable && yarn install && yarn workspace chronicler-frontend build && cd backend
uv run python manage.py runserver                             # then open http://localhost:8000
```

In the browser: the **story map** with a river of readings per audience (`docs/usage/story-map.md`)
and who knew which beat from when (`knowledge-map.md`),
the chronicle list (`docs/usage/browse-chronicles.md`), a chronicle's beats as
each audience saw them (`chronicle.md`), the lattice of hypotheses at any beat (`lattice.md`), what
the audience expects next (`expectations.md`), who knows what (`knowledge.md`) and trying a beat
before narrating it (`try-a-beat.md`). The Django admin is at `/admin/` (`admin.md`).

With a language model: check it with `uv run python -m llm.smoke` (`ollama-smoke-check.md`), replay
with `--reader configured`, and look at the raw token probabilities behind every expectation with
`manage.py inspect_readouts` (`inspect-readouts.md`).

More commands, all documented in `docs/usage/`: importing books, sessions and news coverage
(`import-prose.md`, `import-session.md`, `import-media.md`), drafting their beats with the language
model (`draft-beats.md`), writing stories toward a twist and comparing writers (`generate.md`,
`compare.md`), fact labels and outlet comparison (`fact-labels.md`, `compare-outlets.md`), and the
usage study (`usage-study.md`, `consent.md`). Packages still waiting for input are marked
`blocked` in `docs/work-packages/`.

## Frontend

Requirements: Node 24 LTS (`.node-version`; 22.22.2 or newer works too) and Yarn 4 through
Corepack (ADR-010). The frontend and the browser tests are Yarn workspaces with one `yarn.lock` in
the repository root.

```bash
corepack enable              # once; Node 25 and newer: npm install -g corepack first
yarn install                 # in the repository root: installs frontend/ and e2e/
cd frontend
yarn dev                     # http://localhost:5173, forwards /api to Django on port 8000
yarn test                    # component tests
yarn lint && yarn format:check && yarn typecheck
yarn build                   # frontend/dist, served by Django under / (ADR-007)
yarn generate:api-types      # after changing the API
```

## Browser tests

```bash
cd e2e
yarn playwright install chromium   # skip if the browser is pre-installed
yarn playwright test               # builds the frontend and starts Django with the e2e settings
```

In a container with a pre-installed Chromium of another build, point Playwright to it:
`CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium yarn playwright test`.
