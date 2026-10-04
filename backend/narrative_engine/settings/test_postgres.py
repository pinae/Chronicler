"""The test settings on PostgreSQL, the database of development and production (ADR-008).

The default suite runs on SQLite, fast and without a server; CI runs it on PostgreSQL too, because
the two differ (e.g. JSONB does not keep the order of object keys). Locally:
`docker compose up -d`, then `uv run pytest --ds=narrative_engine.settings.test_postgres`."""

import environ

from .test import *  # noqa: F403

# An IP address, not a host name: pytest-socket blocks name lookups in tests.
DATABASES = {
    "default": environ.Env().db(
        "TEST_DATABASE_URL", default="postgres://narrative:narrative@127.0.0.1:5432/narrative_engine"
    )
}
