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


def test_generate_sends_every_field_of_the_request_as_is_without_streaming():
    received = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/generate"
        received.update(json.loads(request.content))
        return httpx.Response(200, json={"model": "reader", "response": "A", "done": True})

    transport_answering(handler).generate(
        {"model": "reader", "prompt": "Pick A or B.", "think": False, "truncate": False}
    )

    assert received == {
        "model": "reader",
        "prompt": "Pick A or B.",
        "think": False,
        "truncate": False,
        "stream": False,
    }


def test_show_returns_what_the_server_knows_about_a_model():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/show"
        assert json.loads(request.content) == {"model": "reader"}
        return httpx.Response(200, json={"capabilities": ["completion", "thinking"]})

    assert transport_answering(handler).show("reader") == {"capabilities": ["completion", "thinking"]}


def test_an_unknown_model_raises_ollama_error_with_the_server_message():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "model 'reader' not found"})

    with pytest.raises(OllamaError, match="model 'reader' not found"):
        transport_answering(handler).show("reader")
