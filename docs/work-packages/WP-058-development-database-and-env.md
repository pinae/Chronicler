# WP-058: Development database and settings from .env

**Milestone:** M0 (follow-up) · **Serves:** all

## Goal
A developer can run the whole system locally: PostgreSQL comes up with one command, and every
setting, including the Ollama ones, can be given in `backend/.env`.

## Acceptance criteria
- `docker compose up -d` in the repository root starts a PostgreSQL that the values in
  `backend/.env.example` connect to; its data survives a restart.
- The dev settings read every value from `backend/.env`, including those the shared settings read
  (the `OLLAMA_*` settings); environment variables still take precedence.
- The migrations run against that PostgreSQL, and a replay works there.
- An ADR records the choices; the README and the usage docs say how to start the database and how
  to point the engine at an Ollama server.

## Dependencies
WP-001, WP-003.

## Out of scope
Running Django itself in a container; production deployment.

## Status
done

## Summary
`docker-compose.yml` runs `postgres:18` on 127.0.0.1:5432 with the credentials of
`backend/.env.example` and a persistent volume (ADR-008); migrations, replays, `evaluate` and the
API were tried against it. Two bugs surfaced: the dev settings read `backend/.env` only after the
shared settings had read `OLLAMA_*`, so those values were ignored (now read first, environment
still wins, `DJANGO_ENV_FILE` for another file); and PostgreSQL's JSONB sorted the keys of schema
roles and bindings, which reordered displays, prompts and which open role a readout asks about
(roles are now stored as ordered pairs, bindings put back in role order on load). The whole suite
passes on PostgreSQL, and CI runs it there too (`settings.test_postgres`).
