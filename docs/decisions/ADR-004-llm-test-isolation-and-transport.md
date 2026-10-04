# ADR-004: Keeping tests away from the language model

**Status:** accepted (2026-10-03) · **Work package:** WP-003 · **Amended:** 2026-10-04 (WP-063), the
transport posts to the native API itself, see *Amendment* below.

## Context
Concept §8.5: no test in the default run may reach the network; integration tests that call the
Ollama server are marked `llm`, deselected by default, run with `pytest --llm`, and skip when
`OLLAMA_BASE_URL` is unset. All model calls go through the `llm` app using the official `ollama`
package and its native API. We need (1) a guarantee, not a convention, that tests stay offline,
(2) the opt-in mechanism, and (3) a seam where tests replace the server.

## Options considered
- **Offline guarantee:** the `pytest-socket` plugin (`--disable-socket`; per-test opt-in with the
  `enable_socket` marker) vs. a hand-written fixture that patches `socket.socket` (same idea, our
  code to maintain) vs. relying on mocks (nothing fails when a mock is forgotten).
- **Opt-in:** `addopts = "-m 'not llm'"` as in the concept vs. a small plugin that deselects `llm`
  tests unless `--llm` is given. With `-m` in `addopts`, `--llm` would have to rewrite the marker
  expression, and a developer's own `-m` would silently replace it.
- **Seam for fakes:** mock the `ollama` client objects vs. our own `OllamaTransport` protocol that
  takes and returns plain JSON-shaped dicts.

## Decision
- `pytest-socket` with `addopts = "--strict-markers --disable-socket --allow-unix-socket"`. Unix
  sockets stay allowed because asyncio creates a socket pair internally.
- `llm/pytest_plugin.py` (loaded from `backend/conftest.py`) registers the `llm` marker and the
  `--llm` option. Without `--llm`, `llm` tests are deselected. With it, they get `enable_socket`,
  and are skipped with the reason "OLLAMA_BASE_URL is not set" when the variable is missing.
- Test settings set `OLLAMA_BASE_URL` and both model names to `None`, even when the shell defines
  them; integration tests read the server from the environment themselves.
- `llm/transport.py` defines `OllamaTransport` (`server_version()`, `generate(request) -> dict`).
  `HttpOllamaTransport` wraps the official client; its unit tests run against
  `httpx.MockTransport`, so they need no sockets. Everything above the transport sees plain data,
  which is also what the call log (WP-023) stores.

## Reasoning
- pytest-socket is the established, maintained way to make network access fail loudly in tests
  (0.8.1, released August 2026); its README documents `--disable-socket`, `--allow-unix-socket` and
  the `enable_socket` marker ([pytest-socket](https://github.com/miketheman/pytest-socket)).
- The official client passes extra keyword arguments to `httpx.Client`, so an in-memory
  `httpx.MockTransport` exercises the real request and response code
  ([ollama-python](https://github.com/ollama/ollama-python),
  [HTTPX mock transports](https://www.python-httpx.org/advanced/transports/)).
- A dict-in, dict-out seam keeps fakes trivial and matches how requests are hashed and cached
  (concept §8.4).

## Consequences
- A test that tries to open a network connection fails with `SocketBlockedError`.
- The smoke check and later readers/ingesters receive a transport, so tests drive them with fakes.
- The `top_logprobs` maximum of the native API is 20 per the client's documentation; the smoke check
  reports what the deployed server actually returns.

## Amendment (2026-10-04, WP-063): the transport posts to the native API itself
`HttpOllamaTransport` no longer wraps the official `ollama` client; it posts the request dict as it
is to `/api/generate` (with `stream: false`), `/api/show` and `/api/version` over `httpx`, and the
`ollama` package is no longer a dependency. Readouts must send `truncate: false` (fail instead of
silently cutting an over-long prompt), and the official client (0.6.3, the latest on PyPI on
2026-10-04) has no such parameter; its `generate()` rejects unknown keywords. The server accepts
the field ([`api/types.go`](https://github.com/ollama/ollama/blob/main/api/types.go): `Truncate`,
`Shift`, `Think`, `Logprobs`, `TopLogprobs` on `GenerateRequest`). Posting the dict also keeps the
logged request identical to what the server received. Everything else above stands: the seam is
still `OllamaTransport`, unit tests still run against `httpx.MockTransport`, and only the `llm`
app talks to the server (now checked for `httpx` as well as `ollama` imports).
