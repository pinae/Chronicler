import json
import math
from collections.abc import Mapping
from typing import Any

import pytest

from llm.smoke import ModelCapabilities, check_model, format_report, main, models_to_check
from llm.transport import OllamaError, OllamaUnreachable


class FakeOllamaServer:
    """Answers the way a server with the given capabilities and model would."""

    def __init__(
        self,
        version: str = "0.12.3",
        logprobs: bool = True,
        top_logprobs_limit: int = 20,
        json_schema: bool = True,
        prompt_logprobs: bool = False,
        thinking: bool = False,
        temperature_scales_logprobs: bool = False,
        show: dict[str, Any] | None = None,
    ) -> None:
        self.version = version
        self.logprobs = logprobs
        self.top_logprobs_limit = top_logprobs_limit
        self.json_schema = json_schema
        self.prompt_logprobs = prompt_logprobs
        self.thinking = thinking
        self.temperature_scales_logprobs = temperature_scales_logprobs
        self.show_answer = (
            show
            if show is not None
            else {
                "capabilities": ["completion", "thinking"] if thinking else ["completion"],
                "details": {"quantization_level": "Q4_K_M"},
                "model_info": {"general.architecture": "gemma4", "gemma4.context_length": 131072},
            }
        )
        self.requests: list[Mapping[str, Any]] = []

    def server_version(self) -> str:
        return self.version

    def show(self, model: str) -> dict[str, Any]:
        return self.show_answer

    def generate(self, request: Mapping[str, Any]) -> dict[str, Any]:
        self.requests.append(request)
        if request.get("format") is not None:
            return self.structured_answer()
        if self.thinking and request.get("think") is not False:
            return self.thought(request)
        return self.letter(request)

    def structured_answer(self) -> dict[str, Any]:
        if not self.json_schema:
            raise OllamaError("format is not supported")
        return {"response": json.dumps({"answer": "yes"}), "eval_count": 5}

    def letter(self, request: Mapping[str, Any]) -> dict[str, Any]:
        temperature = request.get("options", {}).get("temperature", 0.8)
        sharpness = 1 / temperature if self.temperature_scales_logprobs and temperature > 0 else 1.0
        return self.one_token("A", request, [("A", -0.1 * sharpness), ("B", -2.5 * sharpness)], response="A")

    def thought(self, request: Mapping[str, Any]) -> dict[str, Any]:
        return self.one_token("Let", request, [("Let", -0.2), ("The", -1.9), ("A", -6.0)], response="")

    def one_token(self, token, request, alternatives, response):
        answer: dict[str, Any] = {"response": response, "eval_count": 1}
        if not response:
            answer["thinking"] = token
        if not (self.logprobs and request.get("logprobs")):
            return answer
        count = min(request.get("top_logprobs", 0), self.top_logprobs_limit)
        padding = [(f"t{i}", -9.0) for i in range(count)]
        top = [{"token": t, "logprob": lp} for t, lp in [*alternatives, *padding][:count]]
        entry = {"token": token, "logprob": alternatives[0][1], "top_logprobs": top}
        prompt_entries = [entry] * 12 if self.prompt_logprobs else []
        answer["logprobs"] = [*prompt_entries, entry]
        return answer


# The fake model answers "A" with logprob -0.1 and "B" with -2.5.
LETTERS_MASS = math.exp(-0.1) + math.exp(-2.5)


class UnreachableServer:
    def server_version(self) -> str:
        raise OllamaUnreachable("connection refused")

    def show(self, model: str) -> dict[str, Any]:
        raise OllamaUnreachable("connection refused")

    def generate(self, request: Mapping[str, Any]) -> dict[str, Any]:
        raise OllamaUnreachable("connection refused")


def test_capable_server_reports_every_capability():
    capabilities = check_model(FakeOllamaServer(), "reader")

    assert capabilities == ModelCapabilities(
        model="reader",
        thinking=False,
        context_length=131072,
        quantization="Q4_K_M",
        logprobs=True,
        top_logprobs_max=20,
        answer_mass=LETTERS_MASS,
        answer_mass_by_default=LETTERS_MASS,
        temperature_dependent=False,
        json_schema=True,
        prompt_logprobs=False,
    )


def test_minimal_server_reports_missing_capabilities():
    server = FakeOllamaServer(logprobs=False, json_schema=False, show={})

    capabilities = check_model(server, "reader")

    assert capabilities == ModelCapabilities(
        model="reader",
        thinking=False,
        context_length=None,
        quantization=None,
        logprobs=False,
        top_logprobs_max=0,
        answer_mass=None,
        answer_mass_by_default=None,
        temperature_dependent=None,
        json_schema=False,
        prompt_logprobs=False,
    )


def test_top_logprobs_maximum_is_what_the_server_returns():
    capabilities = check_model(FakeOllamaServer(top_logprobs_limit=5), "reader")

    assert capabilities.top_logprobs_max == 5


def test_logprobs_for_more_tokens_than_generated_means_prompt_logprobs():
    capabilities = check_model(FakeOllamaServer(prompt_logprobs=True), "reader")

    assert capabilities.prompt_logprobs is True


def test_a_thinking_model_puts_its_first_token_on_its_reasoning_unless_told_not_to_think():
    capabilities = check_model(FakeOllamaServer(thinking=True), "reader")

    assert capabilities.thinking is True
    assert capabilities.answer_mass == pytest.approx(LETTERS_MASS)
    assert capabilities.answer_mass_by_default == pytest.approx(math.exp(-6.0))


def test_logprobs_that_change_with_the_temperature_are_reported():
    capabilities = check_model(FakeOllamaServer(temperature_scales_logprobs=True), "reader")

    assert capabilities.temperature_dependent is True


def test_report_prints_server_version_and_each_capability_readably():
    capabilities = ModelCapabilities(
        model="reader",
        thinking=True,
        context_length=131072,
        quantization="Q4_K_M",
        logprobs=True,
        top_logprobs_max=20,
        answer_mass=0.973,
        answer_mass_by_default=0.002,
        temperature_dependent=False,
        json_schema=False,
        prompt_logprobs=False,
    )

    report = format_report("0.12.3", [capabilities], num_ctx=16384)

    assert report.splitlines() == [
        "server version: 0.12.3",
        "model: reader",
        "  thinks unless told not to: yes",
        "  context length: 131072 (requests ask for 16384)",
        "  quantization: Q4_K_M",
        "  logprobs: yes",
        "  top_logprobs max: 20",
        "  answer-letter mass, thinking off: 97.3%",
        "  answer-letter mass, model defaults: 0.2%",
        "  logprobs depend on temperature: no",
        "  json-schema: no",
        "  prompt-logprobs: no",
    ]


def test_unknown_values_are_reported_as_unknown():
    capabilities = ModelCapabilities(
        model="reader",
        thinking=False,
        context_length=None,
        quantization=None,
        logprobs=False,
        top_logprobs_max=0,
        answer_mass=None,
        answer_mass_by_default=None,
        temperature_dependent=None,
        json_schema=False,
        prompt_logprobs=False,
    )

    report = format_report("0.12.3", [capabilities], num_ctx=16384)

    assert "  context length: unknown (requests ask for 16384)" in report
    assert "  answer-letter mass, thinking off: unknown" in report
    assert "  logprobs depend on temperature: unknown" in report


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
