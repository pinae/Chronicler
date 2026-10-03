"""Test settings: in-memory SQLite and nothing read from the environment."""

from .base import *  # noqa: F403

SECRET_KEY = "test-only-secret-key"

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

# Hashing speed is irrelevant to what the tests check, so use the cheapest hasher.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
