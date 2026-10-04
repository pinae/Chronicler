import math
import os

import pytest
from django.core.exceptions import ImproperlyConfigured

from llm.models import LLMCall
from reader.interfaces import Candidate, ContextBeat, Question, ReaderContext
from reader.ollama import OllamaChoiceReader, ReaderError

CONTEXT = ReaderContext(
    t=2, beats=(ContextBeat(t=1, text="Mira trusts Aldric."), ContextBeat(t=2, text="Mira has the key."))
)
QUESTION = Question(
    t=2,
    text="Next: Aldric learns that Mira hides ___.",
    candidates=(
        Candidate(label="A", text="The key", binding_delta={"S": 4}),
        Candidate(label="B", text="The letter", binding_delta={"S": 5}),
        Candidate(label="C", text="nothing like this yet", binding_delta=None),
    ),
)


def first_token(*alternatives):
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


class FakeServer:
    def __init__(self, response):
        self.response = response
        self.requests = []

    def server_version(self):
        return "0.12.3"

    def generate(self, request):
        self.requests.append(request)
        return self.response


def reader_answering(response, settings):
    settings.OLLAMA_READER_MODEL = "reader-model"
    server = FakeServer(response)
    return OllamaChoiceReader(transport=server), server


@pytest.mark.django_db
def test_prompt_lists_the_context_the_question_and_lettered_options(settings):
    reader, server = reader_answering(first_token(("A", 0.9)), settings)

    reader.readout(CONTEXT, QUESTION)

    [request] = server.requests
    prompt = request["prompt"]
    assert prompt.index("t=1: Mira trusts Aldric.") < prompt.index("t=2: Mira has the key.")
    assert "Next: Aldric learns that Mira hides ___." in prompt
    assert "A) The key\nB) The letter\nC) nothing like this yet" in prompt
    assert prompt.rstrip().endswith("Answer with the letter only.")


@pytest.mark.django_db
def test_request_asks_for_one_token_with_enough_logprobs_and_no_constrained_decoding(settings):
    reader, server = reader_answering(first_token(("A", 0.9)), settings)

    reader.readout(CONTEXT, QUESTION)

    [request] = server.requests
    assert request["model"] == "reader-model"
    assert request["logprobs"] is True
    assert request["top_logprobs"] >= len(QUESTION.candidates)
    assert request["options"]["num_predict"] == 1
    assert "format" not in request


@pytest.mark.django_db
def test_request_reads_the_models_own_distribution_over_the_answer(settings):
    """A thinking model would spend its one token on its reasoning; a repeat penalty would lower the
    labels, which all appear in the prompt; temperature 1 leaves the logits unscaled."""
    reader, server = reader_answering(first_token(("A", 0.9)), settings)

    reader.readout(CONTEXT, QUESTION)

    [request] = server.requests
    assert request["think"] is False
    assert request["options"]["temperature"] == 1.0
    assert request["options"]["repeat_penalty"] == 1.0
    assert request["options"]["presence_penalty"] == 0.0
    assert request["options"]["frequency_penalty"] == 0.0


@pytest.mark.django_db
def test_a_prompt_too_long_for_the_context_is_an_error_not_silently_cut(settings):
    reader, server = reader_answering(first_token(("A", 0.9)), settings)
    settings.OLLAMA_NUM_CTX = 8192

    reader.readout(CONTEXT, QUESTION)

    [request] = server.requests
    assert request["truncate"] is False
    assert request["options"]["num_ctx"] == 8192


@pytest.mark.django_db
def test_a_model_that_thinks_anyway_is_an_error_that_says_so(settings):
    thinking = {**first_token(("The", 0.5), ("A", 0.1)), "response": "", "thinking": "The"}
    reader, _ = reader_answering(thinking, settings)

    with pytest.raises(ReaderError, match="thinking"):
        reader.readout(CONTEXT, QUESTION)


@pytest.mark.django_db
def test_distribution_is_renormalized_over_the_labels_and_reports_the_mass_outside(settings):
    reader, _ = reader_answering(first_token(("A", 0.6), ("B", 0.2), ("The", 0.1), ("C", 0.05)), settings)

    readout = reader.readout(CONTEXT, QUESTION)

    assert readout.probabilities == pytest.approx({"A": 0.6 / 0.85, "B": 0.2 / 0.85, "C": 0.05 / 0.85})
    assert readout.outside_mass == pytest.approx(0.15)


@pytest.mark.django_db
def test_spelling_variants_of_a_label_are_added_up(settings):
    reader, _ = reader_answering(first_token(("A", 0.5), (" A", 0.2), ("B)", 0.2), ("c", 0.1)), settings)

    readout = reader.readout(CONTEXT, QUESTION)

    assert readout.probabilities == pytest.approx({"A": 0.7 / 0.9, "B": 0.2 / 0.9, "C": 0.0})


@pytest.mark.django_db
def test_readout_is_logged_with_the_included_beats_and_served_from_the_log_next_time(settings):
    reader, server = reader_answering(first_token(("A", 0.9)), settings)

    first = reader.readout(CONTEXT, QUESTION)
    second = reader.readout(CONTEXT, QUESTION)

    assert len(server.requests) == 1
    assert first.llm_call_id == second.llm_call_id
    call = LLMCall.objects.get(pk=first.llm_call_id)
    assert call.metadata["included_beat_ts"] == [1, 2]
    assert [candidate["label"] for candidate in call.metadata["candidates"]] == ["A", "B", "C"]


@pytest.mark.django_db
def test_assumption_is_stated_in_the_prompt(settings):
    reader, server = reader_answering(first_token(("A", 0.9)), settings)

    reader.readout(CONTEXT.assuming("Aldric is betraying Mira."), QUESTION)

    assert "Assume: Aldric is betraying Mira." in server.requests[0]["prompt"]


@pytest.mark.django_db
def test_response_without_logprobs_is_an_error_that_points_to_the_smoke_check(settings):
    reader, _ = reader_answering({"response": "A", "eval_count": 1}, settings)

    with pytest.raises(ReaderError, match="logprobs.*smoke"):
        reader.readout(CONTEXT, QUESTION)


class WholeTextServer(FakeServer):
    """Offers the rest of the scored line as one token with probability 0.5."""

    def __init__(self, line):
        super().__init__({})
        self.line = line

    def generate(self, request):
        self.requests.append(request)
        scored = request["prompt"].split("\nt=3:")[-1]
        remaining = self.line[len(scored) :]
        return first_token((remaining, 0.5))


@pytest.mark.django_db
def test_a_beat_is_scored_as_the_next_line_of_the_story_under_the_assumption(settings):
    settings.OLLAMA_READER_MODEL = "reader-model"
    server = WholeTextServer(" Aldric steals the key.")
    reader = OllamaChoiceReader(transport=server)

    log_likelihood = reader.beat_log_likelihood(
        CONTEXT.assuming("Aldric is betraying Mira."), ContextBeat(t=3, text="Aldric steals the key.")
    )

    assert log_likelihood == pytest.approx(math.log(0.5))
    [request] = server.requests
    prompt = request["prompt"]
    assert request["raw"] is True
    assert prompt.index("t=1: Mira trusts Aldric.") < prompt.index("t=2: Mira has the key.")
    assert "Assume: Aldric is betraying Mira." in prompt
    assert prompt.endswith("The next event:\nt=3:")


def test_reader_without_a_configured_model_explains_what_is_missing(settings):
    settings.OLLAMA_READER_MODEL = None

    with pytest.raises(ImproperlyConfigured, match="OLLAMA_READER_MODEL"):
        OllamaChoiceReader(transport=FakeServer({}))


def test_reader_without_a_server_explains_what_is_missing(settings):
    settings.OLLAMA_READER_MODEL = "reader-model"
    settings.OLLAMA_BASE_URL = None

    with pytest.raises(ImproperlyConfigured, match="OLLAMA_BASE_URL"):
        OllamaChoiceReader()


@pytest.mark.llm
@pytest.mark.django_db
def test_distribution_over_four_labels_from_the_real_server(settings):
    """Integration (`pytest --llm`): needs OLLAMA_BASE_URL and OLLAMA_READER_MODEL."""
    from llm.transport import HttpOllamaTransport

    settings.OLLAMA_READER_MODEL = os.environ["OLLAMA_READER_MODEL"]
    reader = OllamaChoiceReader(
        transport=HttpOllamaTransport(os.environ["OLLAMA_BASE_URL"], timeout_seconds=120)
    )
    question = Question(
        t=0,
        text="Next: ___ betrays the queen.",
        candidates=tuple(
            Candidate(
                label=label, text=text, binding_delta=None if text.startswith("nothing") else {"T": index}
            )
            for index, (label, text) in enumerate(
                [
                    ("A", "the steward"),
                    ("B", "the captain"),
                    ("C", "the maid"),
                    ("D", "nothing like this yet"),
                ]
            )
        ),
    )

    readout = reader.readout(ReaderContext(t=0, beats=()), question)

    assert sum(readout.probabilities.values()) == pytest.approx(1.0, abs=1e-6)
    assert readout.probabilities["D"] > 0


@pytest.mark.llm
@pytest.mark.django_db
def test_a_beat_that_fits_an_assumption_is_more_likely_under_it_on_the_real_server(settings):
    """Integration (`pytest --llm`): identical contexts give a log Bayes factor of 0, and a theft is
    more likely when the reader assumes a thief than when it assumes a loyal servant."""
    from llm.transport import HttpOllamaTransport
    from reader.bayes import bayes_factor

    settings.OLLAMA_READER_MODEL = os.environ["OLLAMA_READER_MODEL"]
    reader = OllamaChoiceReader(
        transport=HttpOllamaTransport(os.environ["OLLAMA_BASE_URL"], timeout_seconds=120)
    )
    theft = ContextBeat(t=3, text="Aldric steals the key.")
    thief, loyal = "Aldric is a thief.", "Aldric is utterly loyal to Mira."

    assert bayes_factor(reader, theft, CONTEXT, thief, thief) == pytest.approx(0.0, abs=1e-9)
    assert bayes_factor(reader, theft, CONTEXT, thief, loyal) > 0
