import json
from collections.abc import Mapping
from typing import Any

import pytest

from llm.smoke import ModelCapabilities, check_model, format_report, main, models_to_check
from llm.transport import OllamaError, OllamaUnreachable


class FakeOllamaServer:
    """Answers generate requests the way a server with the given capabilities would."""

    def __init__(
        self,
        version: str = "0.12.3",
        logprobs: bool = True,
        top_logprobs_limit: int = 20,
        json_schema: bool = True,
        prompt_logprobs: bool = False,
    ) -> None:
        self.version = version
        self.logprobs = logprobs
        self.top_logprobs_limit = top_logprobs_limit
        self.json_schema = json_schema
        self.prompt_logprobs = prompt_logprobs
        self.requests: list[Mapping[str, Any]] = []

    def server_version(self) -> str:
        return self.version

    def generate(self, request: Mapping[str, Any]) -> dict[str, Any]:
        self.requests.append(request)
        if request.get("format") is not None:
            return self.structured_answer()
        return self.one_token_answer(request)

    def structured_answer(self) -> dict[str, Any]:
        if not self.json_schema:
            raise OllamaError("format is not supported")
        return {"response": json.dumps({"answer": "yes"}), "eval_count": 5}

    def one_token_answer(self, request: Mapping[str, Any]) -> dict[str, Any]:
        answer: dict[str, Any] = {"response": "A", "eval_count": 1}
        if not (self.logprobs and request.get("logprobs")):
            return answer
        alternatives = min(request.get("top_logprobs", 0), self.top_logprobs_limit)
        entry = {
            "token": "A",
            "logprob": -0.1,
            "top_logprobs": [{"token": f"t{i}", "logprob": -1.0} for i in range(alternatives)],
        }
        prompt_entries = [entry] * 12 if self.prompt_logprobs else []
        answer["logprobs"] = [*prompt_entries, entry]
        return answer


class UnreachableServer:
    def server_version(self) -> str:
        raise OllamaUnreachable("connection refused")

    def generate(self, request: Mapping[str, Any]) -> dict[str, Any]:
        raise OllamaUnreachable("connection refused")


def test_capable_server_reports_every_capability():
    capabilities = check_model(FakeOllamaServer(), "reader")

    assert capabilities == ModelCapabilities(
        model="reader", logprobs=True, top_logprobs_max=20, json_schema=True, prompt_logprobs=False
    )


def test_minimal_server_reports_missing_capabilities():
    server = FakeOllamaServer(logprobs=False, json_schema=False)

    capabilities = check_model(server, "reader")

    assert capabilities == ModelCapabilities(
        model="reader", logprobs=False, top_logprobs_max=0, json_schema=False, prompt_logprobs=False
    )


def test_top_logprobs_maximum_is_what_the_server_returns():
    capabilities = check_model(FakeOllamaServer(top_logprobs_limit=5), "reader")

    assert capabilities.top_logprobs_max == 5


def test_logprobs_for_more_tokens_than_generated_means_prompt_logprobs():
    capabilities = check_model(FakeOllamaServer(prompt_logprobs=True), "reader")

    assert capabilities.prompt_logprobs is True


def test_report_prints_server_version_and_each_capability_as_yes_or_no():
    capabilities = ModelCapabilities(
        model="reader", logprobs=True, top_logprobs_max=20, json_schema=False, prompt_logprobs=False
    )

    report = format_report("0.12.3", [capabilities])

    assert report.splitlines() == [
        "server version: 0.12.3",
        "model: reader",
        "  logprobs: yes",
        "  top_logprobs max: 20",
        "  json-schema: no",
        "  prompt-logprobs: no",
    ]


def test_reader_and_ingest_model_are_checked_once_each():
    assert models_to_check("reader", "ingest") == ["reader", "ingest"]
    assert models_to_check("shared", "shared") == ["shared"]
    assert models_to_check("reader", None) == ["reader"]


def test_main_explains_missing_server_configuration(settings, capsys):
    settings.OLLAMA_BASE_URL = None

    exit_code = main(transport_factory=lambda base_url, timeout: FakeOllamaServer())

    assert exit_code == 2
    assert "OLLAMA_BASE_URL is not set" in capsys.readouterr().out


def test_main_explains_missing_models(settings, capsys):
    settings.OLLAMA_BASE_URL = "http://gpu-box:11434"
    settings.OLLAMA_READER_MODEL = None
    settings.OLLAMA_INGEST_MODEL = None

    exit_code = main(transport_factory=lambda base_url, timeout: FakeOllamaServer())

    assert exit_code == 2
    assert "OLLAMA_READER_MODEL" in capsys.readouterr().out


def test_main_prints_the_report_for_the_configured_models(settings, capsys):
    settings.OLLAMA_BASE_URL = "http://gpu-box:11434"
    settings.OLLAMA_READER_MODEL = "reader"
    settings.OLLAMA_INGEST_MODEL = "ingest"

    exit_code = main(transport_factory=lambda base_url, timeout: FakeOllamaServer())

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "server version: 0.12.3" in output
    assert "model: reader" in output
    assert "model: ingest" in output


def test_main_reports_an_unreachable_server(settings, capsys):
    settings.OLLAMA_BASE_URL = "http://gpu-box:11434"
    settings.OLLAMA_READER_MODEL = "reader"

    exit_code = main(transport_factory=lambda base_url, timeout: UnreachableServer())

    assert exit_code == 1
    assert "cannot reach the Ollama server at http://gpu-box:11434" in capsys.readouterr().out


@pytest.mark.llm
def test_smoke_check_runs_against_the_configured_server(capsys):
    """Integration: `uv run pytest --llm` with OLLAMA_BASE_URL and OLLAMA_READER_MODEL set."""
    import os

    from llm.transport import HttpOllamaTransport

    transport = HttpOllamaTransport(os.environ["OLLAMA_BASE_URL"], timeout_seconds=120)
    capabilities = check_model(transport, os.environ["OLLAMA_READER_MODEL"])

    assert capabilities.model == os.environ["OLLAMA_READER_MODEL"]
