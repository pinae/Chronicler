"""The log-likelihood of a text as the continuation of a prompt, scored token by token through
Ollama's top logprobs (ADR-009). Ollama reports probabilities only for generated tokens, so the
text is forced: each step asks for one token after the prompt and the text scored so far, and takes
the probability of the alternative that continues the text."""

import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from llm.cache import CachedOllama
from llm.next_token import NEUTRAL_SAMPLING

MAX_TOP_LOGPROBS = 20
NEXT_WORD = re.compile(r"\s*\S+")


@dataclass(frozen=True)
class ForcedScore:
    log_likelihood: float
    steps: int
    # Steps whose token was not among the alternatives: charged an upper bound of its probability,
    # and the text skipped by one word, since the model's tokenization of it is unknown.
    unmatched: int


def score_continuation(
    client: CachedOllama, model: str, prompt: str, continuation: str, num_ctx: int
) -> ForcedScore:
    log_likelihood, steps, unmatched = 0.0, 0, 0
    scored = ""
    while scored != continuation:
        remaining = continuation[len(scored) :]
        alternatives = next_token_alternatives(client, model, prompt + scored, num_ctx)
        token = longest_continuing(alternatives, remaining)
        if token is None:
            log_likelihood += unlisted_bound(alternatives)
            scored += next_word(remaining)
            unmatched += 1
        else:
            log_likelihood += alternatives[token]
            scored += token
        steps += 1
    return ForcedScore(log_likelihood=log_likelihood, steps=steps, unmatched=unmatched)


def next_token_alternatives(client: CachedOllama, model: str, prompt: str, num_ctx: int) -> dict[str, float]:
    """Raw: no chat template, so the model continues the text itself and has no turn to think in."""
    request = {
        "model": model,
        "prompt": prompt,
        "raw": True,
        "truncate": False,
        "logprobs": True,
        "top_logprobs": MAX_TOP_LOGPROBS,
        "options": {"num_predict": 1, **NEUTRAL_SAMPLING, "num_ctx": num_ctx},
    }
    response = client.generate(request).response
    return top_alternatives(response)


def top_alternatives(response: Mapping[str, Any]) -> dict[str, float]:
    token_logprobs: Sequence[Mapping[str, Any]] = response.get("logprobs") or []
    if not token_logprobs:
        raise ValueError("the server returned no logprobs; check the model with the smoke check (llm.smoke)")
    alternatives: dict[str, float] = {}
    for alternative in token_logprobs[0].get("top_logprobs") or []:
        alternatives.setdefault(alternative["token"], alternative["logprob"])
    return alternatives


def longest_continuing(alternatives: Mapping[str, float], remaining: str) -> str | None:
    continuing = [token for token in alternatives if token and remaining.startswith(token)]
    return max(continuing, key=len, default=None)


def unlisted_bound(alternatives: Mapping[str, float]) -> float:
    """A token outside the alternatives is no more probable than the least probable alternative, nor
    than all the probability the alternatives leave."""
    least_listed = min(alternatives.values())
    left_over = max(1e-12, 1.0 - sum(math.exp(logprob) for logprob in alternatives.values()))
    return min(least_listed, math.log(left_over))


def next_word(text: str) -> str:
    match = NEXT_WORD.match(text)
    return match.group(0) if match else text
