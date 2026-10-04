"""Local development: values come from the environment or from backend/.env (another file with
DJANGO_ENV_FILE). Environment variables take precedence over the file."""

import os
from pathlib import Path

import environ

ENV_FILE = Path(os.environ.get("DJANGO_ENV_FILE", Path(__file__).resolve().parents[2] / ".env"))
if ENV_FILE.exists():
    environ.Env.read_env(ENV_FILE)

# Imported after reading the file, because the shared settings read the environment too (OLLAMA_*).
from .base import *  # noqa: E402, F403
from .base import env  # noqa: E402

DEBUG = True
SECRET_KEY = env("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

DATABASES = {"default": env.db("DATABASE_URL")}
