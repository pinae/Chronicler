"""Test settings: in-memory SQLite and nothing read from the environment."""

from .base import *  # noqa: F403

SECRET_KEY = "test-only-secret-key"

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

# Hashing speed is irrelevant to what the tests check, so use the cheapest hasher.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Tests never talk to a language model, even when the developer's shell points to one.
# Integration tests marked `llm` read the server from the environment themselves.
OLLAMA_BASE_URL = None
OLLAMA_READER_MODEL = None
OLLAMA_INGEST_MODEL = None
OLLAMA_WRITER_MODEL = None

INJECTED = {
    "ReaderModel": "reader.table.TableReader",
    "ContextBuilder": "reader.context.RecentAndSupportingBeats",
    "Ingester": "chronicle.ingest.fixture.FixtureIngester",
}

# Tests never run collectstatic; without a root WhiteNoise has nothing to scan.
STATIC_ROOT = None
