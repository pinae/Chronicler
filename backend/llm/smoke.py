"""Smoke check of the deployed Ollama server (concept §8.2).

    uv run python -m llm.smoke

Reports, per configured model, whether the features the reader model and the ingester rely on
are available. Commit the output to docs/llm-smoke.md.
"""

import json
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass

from llm.next_token import label_masses, next_token_request
from llm.transport import (
    HttpOllamaTransport,
    InspectingTransport,
    JsonObject,
    OllamaError,
    OllamaTransport,
    OllamaUnreachable,
)

# The native API documents 0–20 alternatives per token; ask for the maximum and count what comes back.
REQUESTED_TOP_LOGPROBS = 20

CHOICE_PROMPT = "Answer with a single letter. Is water wet? A) yes B) no"
ANSWER_LETTERS = ("A", "B")
STRUCTURED_PROMPT = 'Reply with a JSON object whose field "answer" is "yes".'
ANSWER_SCHEMA = {"type": "object", "properties": {"answer": {"type": "string"}}, "required": ["answer"]}
# Logprobs scaled by the temperature would come out sharper at this temperature than at 1.
SHARPENING_TEMPERATURE = 0.5

type TransportFactory = Callable[[str, float], InspectingTransport]


@dataclass(frozen=True)
class ModelCapabilities:
    model: str
    thinking: bool
    context_length: int | None
    quantization: str | None
    logprobs: bool
    top_logprobs_max: int
    # How probable it is that the first token is an answer letter: as readouts ask (thinking off,
    # neutral sampling), and with the model's defaults (what readouts asked before WP-063).
    answer_mass: float | None
    answer_mass_by_default: float | None
    temperature_dependent: bool | None
    json_schema: bool
    prompt_logprobs: bool


def check_model(transport: InspectingTransport, model: str) -> ModelCapabilities:
    info = model_info(transport, model)
    readout_request = next_token_request(model, CHOICE_PROMPT, REQUESTED_TOP_LOGPROBS)
    choice = generate_or_nothing(transport, readout_request)
    sharpened = generate_or_nothing(transport, with_temperature(readout_request, SHARPENING_TEMPERATURE))
    by_default = generate_or_nothing(transport, model_defaults_request(model))
    token_logprobs = choice.get("logprobs") or []
    return ModelCapabilities(
        model=model,
        thinking="thinking" in info.get("capabilities", []),
        context_length=context_length(info),
        quantization=info.get("details", {}).get("quantization_level"),
        logprobs=bool(token_logprobs),
        top_logprobs_max=len(token_logprobs[0].get("top_logprobs") or []) if token_logprobs else 0,
        answer_mass=answer_mass(choice),
        answer_mass_by_default=answer_mass(by_default),
        temperature_dependent=temperature_dependent(choice, sharpened),
        json_schema=supports_json_schema(transport, model),
        prompt_logprobs=has_logprobs_for_prompt_tokens(choice),
    )


def model_info(transport: InspectingTransport, model: str) -> JsonObject:
    try:
        return transport.show(model)
    except OllamaUnreachable:
        raise
    except OllamaError:
        return {}


def context_length(info: JsonObject) -> int | None:
    lengths = [value for key, value in info.get("model_info", {}).items() if key.endswith(".context_length")]
    return int(lengths[0]) if lengths else None


def model_defaults_request(model: str) -> JsonObject:
    """One token with logprobs and nothing else said: the model thinks if it can, samples as it is
    configured to."""
    return {
        "model": model,
        "prompt": CHOICE_PROMPT,
        "logprobs": True,
        "top_logprobs": REQUESTED_TOP_LOGPROBS,
        "options": {"num_predict": 1},
    }


def with_temperature(request: JsonObject, temperature: float) -> JsonObject:
    return {**request, "options": {**request["options"], "temperature": temperature}}


def answer_mass(response: JsonObject) -> float | None:
    masses = label_masses(response, ANSWER_LETTERS)
    return None if masses is None else sum(masses.values())


def temperature_dependent(at_one: JsonObject, sharpened: JsonObject) -> bool | None:
    """Do the first token's logprobs change with the temperature? Then readouts must use 1."""
    first, second = at_one.get("logprobs"), sharpened.get("logprobs")
    if not first or not second:
        return None
    return abs(first[0]["logprob"] - second[0]["logprob"]) > 1e-3


def has_logprobs_for_prompt_tokens(response: JsonObject) -> bool:
    """More logprob entries than generated tokens means the prompt was scored too."""
    token_logprobs = response.get("logprobs") or []
    generated_tokens = response.get("eval_count", len(token_logprobs))
    return len(token_logprobs) > generated_tokens


def generate_or_nothing(transport: OllamaTransport, request: JsonObject) -> JsonObject:
    try:
        return transport.generate(request)
    except OllamaUnreachable:
        raise
    except OllamaError:
        return {}


def supports_json_schema(transport: OllamaTransport, model: str) -> bool:
    try:
        response = transport.generate(
            {
                "model": model,
                "prompt": STRUCTURED_PROMPT,
                "format": ANSWER_SCHEMA,
                "options": {"num_predict": 32, "temperature": 0},
            }
        )
    except OllamaUnreachable:
        raise
    except OllamaError:
        return False
    try:
        answer = json.loads(response.get("response", ""))
    except json.JSONDecodeError:
        return False
    return isinstance(answer, dict) and "answer" in answer


def models_to_check(reader_model: str | None, ingest_model: str | None) -> list[str]:
    configured = [model for model in (reader_model, ingest_model) if model]
    return list(dict.fromkeys(configured))


def format_report(server_version: str, models: list[ModelCapabilities], num_ctx: int) -> str:
    lines = [f"server version: {server_version}"]
    for capabilities in models:
        lines += [
            f"model: {capabilities.model}",
            f"  thinks unless told not to: {yes_or_no(capabilities.thinking)}",
            f"  context length: {capabilities.context_length or 'unknown'} (requests ask for {num_ctx})",
            f"  quantization: {capabilities.quantization or 'unknown'}",
            f"  logprobs: {yes_or_no(capabilities.logprobs)}",
            f"  top_logprobs max: {capabilities.top_logprobs_max}",
            f"  answer-letter mass, thinking off: {percent(capabilities.answer_mass)}",
            f"  answer-letter mass, model defaults: {percent(capabilities.answer_mass_by_default)}",
            f"  logprobs depend on temperature: {yes_no_or_unknown(capabilities.temperature_dependent)}",
            f"  json-schema: {yes_or_no(capabilities.json_schema)}",
            f"  prompt-logprobs: {yes_or_no(capabilities.prompt_logprobs)}",
        ]
    return "\n".join(lines)


def percent(share: float | None) -> str:
    return "unknown" if share is None else f"{share:.1%}"


def yes_no_or_unknown(flag: bool | None) -> str:
    return "unknown" if flag is None else yes_or_no(flag)


def yes_or_no(flag: bool) -> str:
    return "yes" if flag else "no"


def main(transport_factory: TransportFactory = HttpOllamaTransport) -> int:
    from django.conf import settings

    base_url = settings.OLLAMA_BASE_URL
    if not base_url:
        print("OLLAMA_BASE_URL is not set; point it to the Ollama server, e.g. http://gpu-box:11434")
        return 2
    models = models_to_check(settings.OLLAMA_READER_MODEL, settings.OLLAMA_INGEST_MODEL)
    if not models:
        print("Neither OLLAMA_READER_MODEL nor OLLAMA_INGEST_MODEL is set; nothing to check")
        return 2

    transport = transport_factory(base_url, settings.OLLAMA_TIMEOUT_S)
    try:
        report = format_report(
            transport.server_version(),
            [check_model(transport, model) for model in models],
            num_ctx=settings.OLLAMA_NUM_CTX,
        )
    except OllamaUnreachable as error:
        print(f"cannot reach the Ollama server at {base_url}: {error}")
        return 1
    print(report)
    return 0


if __name__ == "__main__":
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "narrative_engine.settings.dev")
    django.setup()
    sys.exit(main())
