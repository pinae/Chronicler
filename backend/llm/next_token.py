"""Requests that read the model's probability distribution over its next token, as the reader
model's readouts and the smoke check do."""

import math
from collections.abc import Mapping, Sequence
from typing import Any

# The model's own distribution: temperature 1 leaves the logits unscaled, and without penalties the
# answer labels, which all appear in the prompt, are not pushed down.
NEUTRAL_SAMPLING = {
    "temperature": 1.0,
    "repeat_penalty": 1.0,
    "presence_penalty": 0.0,
    "frequency_penalty": 0.0,
}


def next_token_request(
    model: str, prompt: str, top_logprobs: int, num_ctx: int | None = None
) -> dict[str, Any]:
    """One generated token with its alternatives. A thinking model must not think first (its one
    token would be the start of its reasoning), and a prompt too long for the context must fail
    instead of losing its beginning."""
    options: dict[str, Any] = {"num_predict": 1, **NEUTRAL_SAMPLING}
    if num_ctx is not None:
        options["num_ctx"] = num_ctx
    return {
        "model": model,
        "prompt": prompt,
        "think": False,
        "truncate": False,
        "logprobs": True,
        "top_logprobs": top_logprobs,
        "options": options,
    }


LABEL_DECORATIONS = " )].:"


def label_masses(response: Mapping[str, Any], labels: Sequence[str]) -> dict[str, float] | None:
    """The probability of each label as the first generated token, adding up spelling variants
    such as " A" and "A)". None if the response holds no logprobs."""
    token_logprobs = response.get("logprobs")
    if not token_logprobs:
        return None
    masses = dict.fromkeys(labels, 0.0)
    for alternative in token_logprobs[0].get("top_logprobs") or []:
        # Case-sensitive on purpose: a lowercase "a" is as likely the article as the label.
        label = alternative["token"].strip(LABEL_DECORATIONS)
        if label in masses:
            masses[label] += math.exp(alternative["logprob"])
    return masses
