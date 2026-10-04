# ADR-008: Development database with Docker Compose, tests on SQLite and PostgreSQL

**Status:** accepted · **Date:** 2026-10-04

## Context
The dev settings need PostgreSQL (`DATABASE_URL`), but the repository gave no way to run one, so
the assembled system could not be tried. Tests ran only on in-memory SQLite. Constraints: one
command to start, data that survives restarts, nothing exposed beyond the developer's machine, and
Django itself should keep running on the host with `uv` (fast reloads, debugger, the same commands
as in the docs).

## Options considered
1. **Docker Compose with only PostgreSQL**: one command; the official image; Django stays on the
   host. Needs Docker.
2. **Compose with PostgreSQL and Django**: the whole stack in containers, but every command in the
   docs gets a `docker compose exec` prefix, and reloads and debugging get harder.
3. **A locally installed PostgreSQL**: no Docker, but the setup differs per operating system and
   version.
4. **SQLite for development too**: no server at all, but development would run on a database that
   production does not use.

## Decision
- `docker-compose.yml` in the repository root runs `postgres:18` only, with the credentials of
  `backend/.env.example`, published on `127.0.0.1` only, data in a named volume mounted at
  `/var/lib/postgresql`, and a `pg_isready` health check.
- The file is named `docker-compose.yml` as the user asked; Compose still reads that name, though
  `compose.yaml` is now the canonical one.
- The default test suite stays on SQLite (fast, no server). CI also runs it on PostgreSQL 18
  (`narrative_engine.settings.test_postgres`), and so can a developer with the Compose database.

## Reasoning
- Django 5.2 supports PostgreSQL 14 and newer
  ([Django docs: databases](https://django.readthedocs.io/en/5.2.x/ref/databases.html)); 18 is the
  current major release of the [official image](https://hub.docker.com/_/postgres/).
- From 18 on, the image keeps `PGDATA` in `/var/lib/postgresql/18/docker` and declares the volume at
  `/var/lib/postgresql`; mounting the old `/var/lib/postgresql/data` path makes the container fail
  ([official image](https://hub.docker.com/_/postgres/),
  [experience report](https://aronschueler.de/blog/2025/10/30/fixing-postgres-18-docker-compose-startup/)).
  The per-major directory lets a later `pg_upgrade --link` place 19 next to 18 in the same volume.
- `pg_isready` is the usual health check and lets other services or scripts wait for a ready
  database ([Docker Compose healthchecks](https://www.dash0.com/faq/docker-compose-wait-for-container-before-starting-another)).
- Compose prefers `compose.yaml` but supports `docker-compose.yml` for backwards compatibility
  ([Docker docs](https://docs.docker.com/compose/intro/compose-application-model/)).
- Running the suite on PostgreSQL found real differences on the first try: JSONB does not keep the
  order of object keys, which reordered schema roles and bindings (fixed with WP-058). SQLite alone
  would have kept hiding them.

## Consequences
- Trying the system is `docker compose up -d`, then the commands of the README.
- Developers need Docker for the dev database; tests still need nothing.
- The CI has one more job; a PostgreSQL-only failure shows up there.
- A later move to PostgreSQL 19 needs a `pg_upgrade` (or a dump and restore) of the volume.
