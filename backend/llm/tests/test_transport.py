import json

import httpx
import pytest

from llm.transport import HttpOllamaTransport, OllamaError, OllamaUnreachable


def transport_answering(handler) -> HttpOllamaTransport:
    return HttpOllamaTransport(
        "http://gpu-box:11434", timeout_seconds=5, http_transport=httpx.MockTransport(handler)
    )


def test_server_version_comes_from_the_version_endpoint():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/version"
        return httpx.Response(200, json={"version": "0.12.3"})

    assert transport_answering(handler).server_version() == "0.12.3"


def test_generate_posts_the_request_and_returns_the_response_as_plain_data():
    received = {}

    def handler(request: httpx.Request) -> httpx.Response:
        received.update(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "model": "reader",
                "response": "A",
                "done": True,
                "logprobs": [
                    {"token": "A", "logprob": -0.1, "top_logprobs": [{"token": "A", "logprob": -0.1}]}
                ],
            },
        )

    response = transport_answering(handler).generate(
        {"model": "reader", "prompt": "Pick A or B.", "logprobs": True, "top_logprobs": 1}
    )

    assert received["prompt"] == "Pick A or B."
    assert received["top_logprobs"] == 1
    assert response["response"] == "A"
    assert response["logprobs"][0]["top_logprobs"] == [{"token": "A", "logprob": -0.1}]


def test_rejected_request_raises_ollama_error_with_the_server_message():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": "invalid format"})

    with pytest.raises(OllamaError, match="invalid format"):
        transport_answering(handler).generate({"model": "reader", "prompt": "Hi"})


def test_unreachable_server_raises_ollama_unreachable():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    with pytest.raises(OllamaUnreachable):
        transport_answering(handler).server_version()
    with pytest.raises(OllamaUnreachable):
        transport_answering(handler).generate({"model": "reader", "prompt": "Hi"})
