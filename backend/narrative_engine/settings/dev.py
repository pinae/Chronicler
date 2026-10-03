"""Local development: values come from the environment or from backend/.env."""

from .base import *  # noqa: F403
from .base import BASE_DIR, env

environ_file = BASE_DIR / ".env"
if environ_file.exists():
    env.read_env(environ_file)

DEBUG = True
SECRET_KEY = env("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

DATABASES = {"default": env.db("DATABASE_URL")}
