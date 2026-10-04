from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from llm.cache import CachedOllama, request_hash
from llm.models import LLMCall
from llm.transport import OllamaError

BACKEND_DIR = Path(__file__).resolve().parents[2]
REQUEST = {"model": "reader", "prompt": "Pick A or B.", "options": {"temperature": 0, "num_predict": 1}}


class CountingServer:
    def __init__(self, fail: bool = False) -> None:
        self.requests: list[Mapping[str, Any]] = []
        self.fail = fail

    def server_version(self) -> str:
        return "0.12.3"

    def generate(self, request: Mapping[str, Any]) -> dict[str, Any]:
        self.requests.append(request)
        if self.fail:
            raise OllamaError("model not found")
        return {"response": "A", "eval_count": 1}


def test_request_hash_ignores_key_order():
    reordered = {"options": {"num_predict": 1, "temperature": 0}, "prompt": "Pick A or B.", "model": "reader"}

    assert request_hash("generate", REQUEST) == request_hash("generate", reordered)
    assert len(request_hash("generate", REQUEST)) == 64


@pytest.mark.django_db
def test_first_request_calls_the_server_and_is_logged():
    server = CountingServer()

    call = CachedOllama(server).generate(REQUEST)

    assert server.requests == [REQUEST]
    stored = LLMCall.objects.get(pk=call.pk)
    assert (stored.model, stored.endpoint, stored.request, stored.response, stored.server_version) == (
        "reader",
        "generate",
        REQUEST,
        {"response": "A", "eval_count": 1},
        "0.12.3",
    )


@pytest.mark.django_db
def test_identical_request_is_served_from_the_log_without_calling_the_server():
    first_server, second_server = CountingServer(), CountingServer()
    first = CachedOllama(first_server).generate(REQUEST)

    second = CachedOllama(second_server).generate(dict(REQUEST))

    assert second.pk == first.pk
    assert second_server.requests == []


@pytest.mark.django_db
def test_changed_parameter_makes_a_new_call():
    server = CountingServer()
    cached = CachedOllama(server)
    cached.generate(REQUEST)

    cached.generate({**REQUEST, "options": {"temperature": 1, "num_predict": 1}})

    assert len(server.requests) == 2
    assert LLMCall.objects.count() == 2


@pytest.mark.django_db
def test_sampling_draws_are_cached_separately_without_sending_the_draw_index():
    server = CountingServer()
    cached = CachedOllama(server)

    calls = [cached.generate(REQUEST, draw=draw) for draw in [0, 1, 0]]

    assert [call.pk for call in calls][0] == calls[2].pk != calls[1].pk
    assert server.requests == [REQUEST, REQUEST]


@pytest.mark.django_db
def test_failed_request_is_not_logged():
    with pytest.raises(OllamaError):
        CachedOllama(CountingServer(fail=True)).generate(REQUEST)

    assert LLMCall.objects.count() == 0


@pytest.mark.django_db
def test_server_version_is_asked_once_per_client():
    class VersionCountingServer(CountingServer):
        version_requests = 0

        def server_version(self) -> str:
            self.version_requests += 1
            return "0.12.3"

    server = VersionCountingServer()
    cached = CachedOllama(server)

    cached.generate(REQUEST)
    cached.generate({**REQUEST, "prompt": "Pick C or D."})

    assert server.version_requests == 1


def test_only_the_llm_app_talks_to_the_server():
    offenders = [
        path.relative_to(BACKEND_DIR)
        for path in BACKEND_DIR.rglob("*.py")
        if ".venv" not in path.parts
        and path.relative_to(BACKEND_DIR).parts[0] != "llm"
        and any(
            line.strip().startswith(("import ollama", "from ollama", "import httpx", "from httpx"))
            for line in path.read_text(encoding="utf-8").splitlines()
        )
    ]

    assert offenders == []
