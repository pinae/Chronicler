"""The only module that talks to the Ollama server. Requests and responses are plain JSON data,
so they can be logged and cached (concept §8.4) and replaced by fakes in tests."""

from collections.abc import Mapping
from typing import Any, Protocol

import httpx

type JsonObject = dict[str, Any]


class OllamaError(Exception):
    """The server could not fulfil a request."""


class OllamaUnreachable(OllamaError):
    """No connection to the server."""


class OllamaTransport(Protocol):
    def server_version(self) -> str: ...

    def generate(self, request: Mapping[str, Any]) -> JsonObject: ...


class InspectingTransport(OllamaTransport, Protocol):
    """Also asks what the server knows about a model (the smoke check)."""

    def show(self, model: str) -> JsonObject: ...


class HttpOllamaTransport:
    """The native Ollama API over HTTP. Requests are posted as they are, so every field the server
    understands can be used, including those the official Python client does not know (`truncate`).
    `http_transport` lets tests replace the network with an in-memory `httpx.MockTransport`."""

    def __init__(
        self, base_url: str, timeout_seconds: float, http_transport: httpx.BaseTransport | None = None
    ) -> None:
        self._http = httpx.Client(base_url=base_url, timeout=timeout_seconds, transport=http_transport)

    def server_version(self) -> str:
        return str(self._call("GET", "/api/version")["version"])

    def generate(self, request: Mapping[str, Any]) -> JsonObject:
        return self._call("POST", "/api/generate", {**request, "stream": False})

    def show(self, model: str) -> JsonObject:
        return self._call("POST", "/api/show", {"model": model})

    def _call(self, method: str, path: str, body: Mapping[str, Any] | None = None) -> JsonObject:
        try:
            response = self._http.request(method, path, json=body)
        except httpx.ConnectError as error:
            raise OllamaUnreachable(str(error)) from error
        except httpx.HTTPError as error:
            raise OllamaError(str(error)) from error
        if response.is_error:
            raise OllamaError(server_message(response))
        answer: JsonObject = response.json()
        return answer


def server_message(response: httpx.Response) -> str:
    try:
        return str(response.json()["error"])
    except (ValueError, KeyError, TypeError):
        return f"{response.status_code} {response.reason_phrase}"
