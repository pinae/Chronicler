"""Settings shared by every environment. Secrets and databases live in dev.py / test.py."""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "chronicle",
    "schemas",
    "matching",
    "reader",
    "llm",
    "evaluation",
    "gm_ui",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "narrative_engine.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "narrative_engine.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# The external Ollama server (concept §8.1). Server and models have no defaults:
# without them, nothing may call a language model.
OLLAMA_BASE_URL = env.str("OLLAMA_BASE_URL", default=None)
OLLAMA_READER_MODEL = env.str("OLLAMA_READER_MODEL", default=None)
OLLAMA_INGEST_MODEL = env.str("OLLAMA_INGEST_MODEL", default=None)
OLLAMA_NUM_CTX = env.int("OLLAMA_NUM_CTX", default=16384)
OLLAMA_KEEP_ALIVE = env.str("OLLAMA_KEEP_ALIVE", default="30m")
OLLAMA_TIMEOUT_S = env.int("OLLAMA_TIMEOUT_S", default=120)

# Matcher (concept §7).
MATCHER_REPEATABLE_FILL_CAP = 3  # fills of a repeatable step that add weight
MATCHER_WEIGHT_FLOOR = -6.0  # live hypotheses below this weight are pruned
MATCHER_MAX_LIVE_PER_SCHEMA = 50  # beyond this, the lowest-weighted live hypotheses are pruned

# Implementations of the injected interfaces (narrative_engine/di.py).
INJECTED = {
    "ReaderModel": "reader.ollama.OllamaChoiceReader",
    "ContextBuilder": "reader.context.RecentAndSupportingBeats",
    "Ingester": "chronicle.ingest.fixture.FixtureIngester",
}

# Reader model context (concept §9.3): recent beats plus beats supporting the strongest hypotheses.
READER_CONTEXT_RECENT_BEATS = 30
READER_CONTEXT_TOP_HYPOTHESES = 5
READER_MAX_CANDIDATES = 20  # labels per readout question; the native API returns at most 20 top_logprobs

# Hand-written stories for tests and replays (concept §9.1).
FIXTURE_STORIES_DIR = BASE_DIR / "fixtures" / "stories"
EVALUATION_RUNS_DIR = BASE_DIR / "evaluation" / "runs"
