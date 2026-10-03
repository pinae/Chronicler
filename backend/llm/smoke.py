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

from llm.transport import (
    HttpOllamaTransport,
    JsonObject,
    OllamaError,
    OllamaTransport,
    OllamaUnreachable,
)

# The native API documents 0–20 alternatives per token; ask for the maximum and count what comes back.
REQUESTED_TOP_LOGPROBS = 20

CHOICE_PROMPT = "Answer with a single letter. Is water wet? A) yes B) no"
STRUCTURED_PROMPT = 'Reply with a JSON object whose field "answer" is "yes".'
ANSWER_SCHEMA = {"type": "object", "properties": {"answer": {"type": "string"}}, "required": ["answer"]}

type TransportFactory = Callable[[str, float], OllamaTransport]


@dataclass(frozen=True)
class ModelCapabilities:
    model: str
    logprobs: bool
    top_logprobs_max: int
    json_schema: bool
    prompt_logprobs: bool


def check_model(transport: OllamaTransport, model: str) -> ModelCapabilities:
    choice = generate_choice_with_logprobs(transport, model)
    token_logprobs = choice.get("logprobs") or []
    return ModelCapabilities(
        model=model,
        logprobs=bool(token_logprobs),
        top_logprobs_max=len(token_logprobs[0].get("top_logprobs") or []) if token_logprobs else 0,
        json_schema=supports_json_schema(transport, model),
        prompt_logprobs=has_logprobs_for_prompt_tokens(choice),
    )


def has_logprobs_for_prompt_tokens(response: JsonObject) -> bool:
    """More logprob entries than generated tokens means the prompt was scored too."""
    token_logprobs = response.get("logprobs") or []
    generated_tokens = response.get("eval_count", len(token_logprobs))
    return len(token_logprobs) > generated_tokens


def generate_choice_with_logprobs(transport: OllamaTransport, model: str) -> JsonObject:
    try:
        return transport.generate(
            {
                "model": model,
                "prompt": CHOICE_PROMPT,
                "logprobs": True,
                "top_logprobs": REQUESTED_TOP_LOGPROBS,
                "options": {"num_predict": 1, "temperature": 0},
            }
        )
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


def format_report(server_version: str, models: list[ModelCapabilities]) -> str:
    lines = [f"server version: {server_version}"]
    for capabilities in models:
        lines += [
            f"model: {capabilities.model}",
            f"  logprobs: {yes_or_no(capabilities.logprobs)}",
            f"  top_logprobs max: {capabilities.top_logprobs_max}",
            f"  json-schema: {yes_or_no(capabilities.json_schema)}",
            f"  prompt-logprobs: {yes_or_no(capabilities.prompt_logprobs)}",
        ]
    return "\n".join(lines)


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
        report = format_report(transport.server_version(), [check_model(transport, m) for m in models])
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
