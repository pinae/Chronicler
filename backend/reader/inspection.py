"""What the reader model actually answered (WP-063): for each stored readout the question, the
model's first token, its raw alternatives and the answer distribution read from them."""

import math
from collections.abc import Iterator, Mapping
from typing import Any

from chronicle.models import Chronicle, Player
from matching.models import Expectation, Hypothesis

THINKING_HINT = "its first token is no answer. Replay to ask again."


def readouts(chronicle: Chronicle, t: int, audience: Player | None) -> list[Expectation]:
    return list(
        Expectation.objects.filter(hypothesis__chronicle=chronicle, computed_at_t=t, for_player=audience)
        .select_related("hypothesis__schema", "llm_call")
        .order_by("hypothesis_id", "pk")
    )


def describe_readouts(chronicle: Chronicle, t: int, audience: Player | None) -> Iterator[str]:
    audience_name = audience.name if audience else "the table"
    found = readouts(chronicle, t, audience)
    if not found:
        yield f"No readouts at t={t} for {audience_name}."
        return
    story = chronicle.meta.get("fixture", chronicle.title)
    yield f"Readouts at t={t} for {audience_name} ({story}, chronicle {chronicle.pk})"
    names = dict(chronicle.entities.values_list("pk", "canonical_name"))
    for expectation in found:
        yield ""
        yield reading_text(expectation.hypothesis, names)
        yield f"  {expectation.question}"
        yield from model_lines(expectation)
        yield f"  answers: {answers_text(expectation)}"


def reading_text(hypothesis: Hypothesis, names: Mapping[int, str]) -> str:
    roles = ", ".join(
        f"{role} = {names.get(hypothesis.binding.get(role), '?')}" for role in hypothesis.schema.role_names
    )
    return f"{hypothesis.schema.name}: {roles}"


def model_lines(expectation: Expectation) -> Iterator[str]:
    call = expectation.llm_call
    if call is None:
        yield "  no language model was asked (uniform reader)"
        return
    response = call.response
    prompt_tokens = response.get("prompt_eval_count", "?")
    first_token = response.get("response", "")
    yield f'  model {call.model} · prompt {prompt_tokens} tokens · first token "{first_token}"'
    if response.get("thinking"):
        yield f'  the model was thinking ("{response["thinking"][:40]}"): {THINKING_HINT}'
    yield f"  first-token alternatives: {alternatives_text(response)}"


def alternatives_text(response: Mapping[str, Any]) -> str:
    token_logprobs = response.get("logprobs") or []
    if not token_logprobs:
        return "none (the server returned no logprobs)"
    alternatives = sorted(
        token_logprobs[0].get("top_logprobs") or [], key=lambda alternative: -alternative["logprob"]
    )
    return " · ".join(f'"{a["token"]}" {math.exp(a["logprob"]):.1%}' for a in alternatives)


def answers_text(expectation: Expectation) -> str:
    answers = [f"{c['label']}) {c['text']} {c['p']:.1%}" for c in expectation.candidates]
    return " · ".join([*answers, f"outside the letters {expectation.outside_mass:.1%}"])
