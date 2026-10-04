"""The dev settings take their values from backend/.env (or DJANGO_ENV_FILE).

Regression (2026-10-04, found before the first test against a real Ollama server): the file was
read after base.py had already read the OLLAMA_* settings, so they were silently ignored."""

import os
import subprocess
import sys

from django.conf import settings

ENV_FILE_VALUES = [
    "DJANGO_SECRET_KEY=from-the-file",
    "DATABASE_URL=postgres://narrative:narrative@localhost:5432/narrative_engine",
    "OLLAMA_BASE_URL=http://victor:11434",
    "OLLAMA_READER_MODEL=gemma3:12b",
]


def dev_settings(env_file, **environment):
    """The values the dev settings end up with, in a fresh interpreter."""
    clean = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("OLLAMA_", "DJANGO_", "DATABASE"))
    }
    script = (
        "from django.conf import settings; "
        "print(settings.SECRET_KEY, settings.OLLAMA_BASE_URL, settings.OLLAMA_READER_MODEL, "
        "settings.DATABASES['default']['NAME'])"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        env={
            **clean,
            "DJANGO_SETTINGS_MODULE": "narrative_engine.settings.dev",
            "DJANGO_ENV_FILE": str(env_file),
            **environment,
        },
        cwd=settings.BASE_DIR,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.split()


def test_every_setting_can_come_from_the_env_file_including_ollama(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("\n".join(ENV_FILE_VALUES) + "\n")

    assert dev_settings(env_file) == [
        "from-the-file",
        "http://victor:11434",
        "gemma3:12b",
        "narrative_engine",
    ]


def test_the_environment_takes_precedence_over_the_env_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("\n".join(ENV_FILE_VALUES) + "\n")

    values = dev_settings(env_file, OLLAMA_READER_MODEL="gemma3:27b")

    assert values[2] == "gemma3:27b"
