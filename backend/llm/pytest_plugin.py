"""Pytest plugin: tests marked `llm` call the real Ollama server and run only with `--llm`."""

import os

import pytest

LLM_MARKER = "llm"


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--llm",
        action="store_true",
        default=False,
        help="also run integration tests that call the Ollama server",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", f"{LLM_MARKER}: integration tests that call the Ollama server (deselected by default)"
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    integration_tests = [item for item in items if item.get_closest_marker(LLM_MARKER)]
    if not config.getoption("--llm"):
        deselect(config, items, integration_tests)
        return
    server_configured = bool(os.environ.get("OLLAMA_BASE_URL"))
    for item in integration_tests:
        item.add_marker(pytest.mark.enable_socket)
        if not server_configured:
            item.add_marker(pytest.mark.skip(reason="OLLAMA_BASE_URL is not set"))


def deselect(config: pytest.Config, items: list[pytest.Item], unwanted: list[pytest.Item]) -> None:
    if not unwanted:
        return
    config.hook.pytest_deselected(items=unwanted)
    items[:] = [item for item in items if item not in unwanted]
