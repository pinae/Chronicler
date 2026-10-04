import math

import pytest

from llm.cache import CachedOllama
from reader.forced_scoring import score_continuation

pytestmark = pytest.mark.django_db

PROMPT = "The story so far:\nt=1: Mira trusts Aldric.\nWhat happens next:\nt=2:"
CONTINUATION = " Aldric steals the seal."


class TokenizingServer:
    """A model that continues PROMPT with CONTINUATION, token by token, with the given probability
    for each true token and a few distractors."""

    def __init__(self, tokens, probabilities, distractors=None, top=20):
        self.tokens = tokens
        self.probabilities = probabilities
        self.distractors = distractors or {}
        self.top = top
        self.requests = []

    def server_version(self):
        return "0.22.1"

    def generate(self, request):
        self.requests.append(request)
        forced = request["prompt"][len(PROMPT) :]
        step = self.step_after(forced)
        alternatives = [(self.tokens[step], self.probabilities[step]), *self.distractors.get(step, [])]
        alternatives += [(f"<{i}>", 0.001) for i in range(self.top)]
        alternatives = sorted(alternatives, key=lambda alternative: -alternative[1])[: self.top]
        return {
            "response": alternatives[0][0],
            "eval_count": 1,
            "logprobs": [
                {
                    "token": alternatives[0][0],
                    "logprob": math.log(alternatives[0][1]),
                    "top_logprobs": [{"token": token, "logprob": math.log(p)} for token, p in alternatives],
                }
            ],
        }

    def step_after(self, forced):
        text = ""
        for step, token in enumerate(self.tokens):
            if text == forced:
                return step
            text += token
        raise AssertionError(f"unexpected forced text {forced!r}")


TOKENS = [" Ald", "ric", " steals", " the", " seal", "."]


def score(server, model="reader"):
    return score_continuation(CachedOllama(server), model, PROMPT, CONTINUATION, num_ctx=8192)


def test_the_log_likelihood_of_a_continuation_is_the_sum_of_its_tokens_log_probabilities():
    probabilities = [0.5, 0.9, 0.2, 0.8, 0.6, 0.7]
    server = TokenizingServer(TOKENS, probabilities)

    result = score(server)

    assert result.log_likelihood == pytest.approx(sum(math.log(p) for p in probabilities))
    assert (result.steps, result.unmatched) == (6, 0)


def test_each_step_asks_for_one_raw_token_after_the_prompt_and_the_text_scored_so_far():
    server = TokenizingServer(TOKENS, [0.5] * 6)

    score(server)

    prompts = [request["prompt"] for request in server.requests]
    assert prompts[:3] == [PROMPT, PROMPT + " Ald", PROMPT + " Aldric"]
    request = server.requests[0]
    assert request["raw"] is True
    assert request["truncate"] is False
    assert request["logprobs"] is True
    assert request["top_logprobs"] == 20
    assert request["options"]["num_predict"] == 1
    assert request["options"]["temperature"] == 1.0
    assert request["options"]["repeat_penalty"] == 1.0
    assert request["options"]["num_ctx"] == 8192


def test_the_longest_alternative_that_continues_the_text_is_taken():
    server = TokenizingServer(TOKENS, [0.5] * 6, distractors={0: [(" A", 0.3), (" Al", 0.1)]})

    result = score(server)

    assert result.log_likelihood == pytest.approx(6 * math.log(0.5))


def test_a_token_outside_the_alternatives_is_charged_an_upper_bound_and_the_word_skipped():
    probabilities = [0.5, 0.9, 0.0001, 0.8, 0.6, 0.7]  # " steals" is not among the top 20
    distractors = {2: [(f" w{i}", 0.04) for i in range(20)]}
    server = TokenizingServer(TOKENS, probabilities, distractors=distractors)

    result = score(server)

    twentieth = 0.04
    expected = (
        math.log(0.5) + math.log(0.9) + math.log(twentieth) + math.log(0.8) + math.log(0.6) + math.log(0.7)
    )
    assert result.log_likelihood == pytest.approx(expected)
    assert (result.steps, result.unmatched) == (6, 1)


def test_a_repeated_scoring_is_answered_from_the_call_log():
    server = TokenizingServer(TOKENS, [0.5] * 6)

    first = score(server)
    second = score(server)

    assert len(server.requests) == 6
    assert first == second
