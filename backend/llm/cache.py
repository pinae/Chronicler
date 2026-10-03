"""Logging and caching of every Ollama request (concept §8.4)."""

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from django.db import IntegrityError, transaction

from llm.models import LLMCall
from llm.transport import OllamaTransport

GENERATE = "generate"


def request_hash(endpoint: str, request: Mapping[str, Any], draw: int | None = None) -> str:
    """SHA-256 of the endpoint and the canonical JSON of the request (model included). A sampling
    draw index is part of the hash, so draws are cached separately."""
    hashed: dict[str, Any] = {"endpoint": endpoint, "request": request}
    if draw is not None:
        hashed["draw"] = draw
    canonical = json.dumps(hashed, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class CachedOllama:
    """Answers each request from the call log when it can and asks the server only when it must."""

    def __init__(self, transport: OllamaTransport) -> None:
        self.transport = transport
        self._server_version: str | None = None

    def generate(self, request: Mapping[str, Any], draw: int | None = None) -> LLMCall:
        key = request_hash(GENERATE, request, draw)
        logged = LLMCall.objects.filter(request_hash=key).first()
        if logged is not None:
            return logged
        response = self.transport.generate(request)
        return self.log(key, request, response)

    def log(self, key: str, request: Mapping[str, Any], response: dict[str, Any]) -> LLMCall:
        try:
            with transaction.atomic():
                return LLMCall.objects.create(
                    request_hash=key,
                    model=request["model"],
                    endpoint=GENERATE,
                    request=dict(request),
                    response=response,
                    server_version=self.server_version(),
                )
        except IntegrityError:  # logged by a concurrent identical request in the meantime
            return LLMCall.objects.get(request_hash=key)

    def server_version(self) -> str:
        if self._server_version is None:
            self._server_version = self.transport.server_version()
        return self._server_version
