"""Asking a model for a JSON object: constrained by a JSON schema where the server supports
structured outputs, otherwise asked for in the prompt and parsed leniently."""

import json
from collections.abc import Mapping
from typing import Any

from llm.cache import CachedOllama
from llm.transport import OllamaError, OllamaUnreachable


class JsonAnswers:
    def __init__(self, client: CachedOllama, schema: Mapping[str, Any]) -> None:
        self.client = client
        self.schema = dict(schema)
        self.structured_output = True

    def ask(self, request: Mapping[str, Any]) -> dict[str, Any]:
        """The model's JSON object; an empty one if the answer holds none."""
        if self.structured_output:
            try:
                return json_object(self.client.generate({**request, "format": self.schema}).response)
            except OllamaUnreachable:
                raise
            except OllamaError:
                self.structured_output = False  # the server cannot constrain output: the prompt asks
        return json_object(self.client.generate(dict(request)).response)


def json_object(response: Mapping[str, Any]) -> dict[str, Any]:
    """The outermost {...} of the model's answer text, if it parses as an object."""
    text = str(response.get("response", ""))
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end < start:
        return {}
    try:
        answer = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return {}
    return answer if isinstance(answer, dict) else {}
