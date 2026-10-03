"""The only module that talks to the Ollama server. Requests and responses are plain JSON data,
so they can be logged and cached (concept §8.4) and replaced by fakes in tests."""

from collections.abc import Mapping
from typing import Any, Protocol

import httpx
import ollama

type JsonObject = dict[str, Any]


class OllamaError(Exception):
    """The server could not fulfil a request."""


class OllamaUnreachable(OllamaError):
    """No connection to the server."""


class OllamaTransport(Protocol):
    def server_version(self) -> str: ...

    def generate(self, request: Mapping[str, Any]) -> JsonObject: ...


class HttpOllamaTransport:
    """Native Ollama API (`/api/generate`) via the official client; `http_transport` lets tests
    replace the network with an in-memory `httpx.MockTransport`."""

    def __init__(
        self, base_url: str, timeout_seconds: float, http_transport: httpx.BaseTransport | None = None
    ) -> None:
        self._http = httpx.Client(base_url=base_url, timeout=timeout_seconds, transport=http_transport)
        self._ollama = ollama.Client(host=base_url, timeout=timeout_seconds, transport=http_transport)

    def server_version(self) -> str:
        try:
            response = self._http.get("/api/version")
            response.raise_for_status()
        except httpx.ConnectError as error:
            raise OllamaUnreachable(str(error)) from error
        except httpx.HTTPError as error:
            raise OllamaError(str(error)) from error
        return str(response.json()["version"])

    def generate(self, request: Mapping[str, Any]) -> JsonObject:
        try:
            response = self._ollama.generate(**request)
        except ConnectionError as error:
            raise OllamaUnreachable(str(error)) from error
        except (ollama.ResponseError, httpx.HTTPError) as error:
            raise OllamaError(str(error)) from error
        return response.model_dump(exclude_none=True)
