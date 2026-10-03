"""The `llm` marker: integration tests that call Ollama run only on request (`pytest --llm`)."""

import pytest

pytest_plugins = ["pytester"]

INTEGRATION_TEST = """
import pytest

@pytest.mark.llm
def test_calls_the_server():
    pass

def test_plain_unit_test():
    pass
"""


@pytest.fixture
def project_with_integration_test(pytester):
    pytester.makeconftest('pytest_plugins = ["llm.pytest_plugin"]')
    pytester.makepyfile(test_example=INTEGRATION_TEST)
    return pytester


def run(pytester, *arguments):
    return pytester.runpytest_inprocess("-p", "no:django", "-p", "no:cacheprovider", *arguments)


def test_integration_tests_are_deselected_by_default(project_with_integration_test):
    result = run(project_with_integration_test)

    result.assert_outcomes(passed=1, deselected=1)


def test_llm_option_runs_integration_tests_when_server_is_configured(
    project_with_integration_test, monkeypatch
):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://gpu-box:11434")

    result = run(project_with_integration_test, "--llm")

    result.assert_outcomes(passed=2)


def test_llm_option_skips_integration_tests_without_a_server(project_with_integration_test, monkeypatch):
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)

    result = run(project_with_integration_test, "--llm", "-rs")

    result.assert_outcomes(passed=1, skipped=1)
    result.stdout.fnmatch_lines(["*OLLAMA_BASE_URL is not set*"])


def test_integration_tests_may_open_network_connections(pytester, monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://gpu-box:11434")
    pytester.makeconftest('pytest_plugins = ["llm.pytest_plugin"]')
    pytester.makepyfile(
        test_network="""
import socket
import pytest

@pytest.mark.llm
def test_creates_a_socket():
    socket.socket().close()
"""
    )

    result = run(pytester, "--llm", "--disable-socket")

    result.assert_outcomes(passed=1)
