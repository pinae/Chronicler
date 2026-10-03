"""Settings for the end-to-end browser tests (e2e/): a throwaway SQLite file, the built frontend
served by Django, and the uniform reader instead of a language model."""

from .base import *  # noqa: F403
from .base import BASE_DIR, FRONTEND_DIST_DIR

DEBUG = False
SECRET_KEY = "e2e-only-secret-key"
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / ".e2e.sqlite3"}}

STATICFILES_DIRS = [FRONTEND_DIST_DIR]
WHITENOISE_USE_FINDERS = True  # serve the build without collectstatic

INJECTED = {
    "ReaderModel": "reader.uniform.UniformReader",
    "ContextBuilder": "reader.context.RecentAndSupportingBeats",
    "Ingester": "chronicle.ingest.fixture.FixtureIngester",
}

OLLAMA_BASE_URL = None
OLLAMA_READER_MODEL = None
OLLAMA_INGEST_MODEL = None

E2E_SEEDING_ALLOWED = True

# Files come from the finders (above), not from collectstatic.
STATIC_ROOT = None
