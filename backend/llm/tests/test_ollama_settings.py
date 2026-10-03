import json
import os
import subprocess
import sys
from pathlib import Path

from django.conf import settings

BACKEND_DIR = Path(__file__).resolve().parents[2]

OLLAMA_ENVIRONMENT = {
    "OLLAMA_BASE_URL": "http://gpu-box:11434",
    "OLLAMA_READER_MODEL": "reader-model",
    "OLLAMA_INGEST_MODEL": "ingest-model",
}


def load_settings_module(module: str, extra_environment: dict[str, str]) -> dict[str, object]:
    """Import a settings module in a fresh interpreter, so its environment is fully controlled."""
    script = (
        "import importlib, json\n"
        f"module = importlib.import_module({module!r})\n"
        "names = [n for n in dir(module) if n.startswith('OLLAMA_')]\n"
        "print(json.dumps({n: getattr(module, n) for n in names}))\n"
    )
    environment = {key: value for key, value in os.environ.items() if not key.startswith("OLLAMA_")}
    environment.update(extra_environment)
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=BACKEND_DIR,
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(completed.stdout)


def test_base_settings_read_ollama_configuration_from_environment():
    values = load_settings_module("narrative_engine.settings.base", OLLAMA_ENVIRONMENT)

    assert values["OLLAMA_BASE_URL"] == "http://gpu-box:11434"
    assert values["OLLAMA_READER_MODEL"] == "reader-model"
    assert values["OLLAMA_INGEST_MODEL"] == "ingest-model"


def test_base_settings_default_context_keep_alive_and_timeout():
    values = load_settings_module("narrative_engine.settings.base", {})

    assert values["OLLAMA_NUM_CTX"] == 16384
    assert values["OLLAMA_KEEP_ALIVE"] == "30m"
    assert values["OLLAMA_TIMEOUT_S"] == 120


def test_test_settings_carry_no_ollama_server_or_models():
    assert settings.OLLAMA_BASE_URL is None
    assert settings.OLLAMA_READER_MODEL is None
    assert settings.OLLAMA_INGEST_MODEL is None


def test_test_settings_ignore_ollama_values_in_the_environment():
    values = load_settings_module("narrative_engine.settings.test", OLLAMA_ENVIRONMENT)

    assert values["OLLAMA_BASE_URL"] is None
    assert values["OLLAMA_READER_MODEL"] is None
    assert values["OLLAMA_INGEST_MODEL"] is None
