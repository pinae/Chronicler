"""The production reader model: a multiple-choice prompt to Ollama, read from first-token logprobs
(concept §8.3). No constrained decoding: masking would renormalize the distribution and hide how
much probability the model put outside the candidates, which is itself a signal."""

from collections.abc import Mapping, Sequence
from typing import Any

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from llm.cache import CachedOllama
from llm.next_token import label_masses, next_token_request
from llm.transport import HttpOllamaTransport, OllamaTransport
from reader.interfaces import ContextBeat, Question, ReaderContext, Readout

MAX_TOP_LOGPROBS = 20  # the native API's maximum (see docs/llm-smoke.md)


class ReaderError(Exception):
    pass


class OllamaChoiceReader:
    def __init__(self, transport: OllamaTransport | None = None) -> None:
        if not settings.OLLAMA_READER_MODEL:
            raise ImproperlyConfigured("OLLAMA_READER_MODEL is not set; the reader model needs a model name")
        self.model = settings.OLLAMA_READER_MODEL
        self.client = CachedOllama(transport or transport_from_settings())

    def readout(self, context: ReaderContext, question: Question) -> Readout:
        request = {
            **next_token_request(
                self.model,
                choice_prompt(context, question),
                top_logprobs=min(MAX_TOP_LOGPROBS, max(len(question.candidates), 10)),
                num_ctx=settings.OLLAMA_NUM_CTX,
            ),
            "keep_alive": settings.OLLAMA_KEEP_ALIVE,
        }
        metadata = {
            "included_beat_ts": context.included_beat_ts,
            "question": question.text,
            "candidates": [
                {"label": c.label, "text": c.text, "binding_delta": c.binding_delta}
                for c in question.candidates
            ],
        }
        call = self.client.generate(request, metadata=metadata)
        probabilities, outside_mass = label_distribution(
            call.response, [c.label for c in question.candidates]
        )
        return Readout(probabilities=probabilities, outside_mass=outside_mass, llm_call_id=call.pk)

    def beat_log_likelihood(self, context: ReaderContext, beat: ContextBeat) -> float:
        raise NotImplementedError("Bayes factors need the estimator chosen in WP-044")


def transport_from_settings() -> OllamaTransport:
    if not settings.OLLAMA_BASE_URL:
        raise ImproperlyConfigured("OLLAMA_BASE_URL is not set; the reader model needs the Ollama server")
    return HttpOllamaTransport(settings.OLLAMA_BASE_URL, settings.OLLAMA_TIMEOUT_S)


def choice_prompt(context: ReaderContext, question: Question) -> str:
    story = "\n".join(f"t={beat.t}: {beat.text}" for beat in context.beats) or "Nothing has happened yet."
    assumption = f"\nAssume: {context.assumption}\n" if context.assumption else ""
    options = "\n".join(f"{candidate.label}) {candidate.text}" for candidate in question.candidates)
    return (
        "You are reading a story as it unfolds. This is what you know so far:\n"
        f"{story}\n{assumption}\n"
        "Which option best completes the next event of the story?\n"
        f"{question.text}\n{options}\n"
        "Answer with the letter only."
    )


def label_distribution(response: Mapping[str, Any], labels: Sequence[str]) -> tuple[dict[str, float], float]:
    """Probabilities per label from the first generated token's alternatives, renormalized over the
    labels, and the probability mass that fell on anything else."""
    if response.get("thinking"):
        raise ReaderError(
            "the model was thinking instead of answering, although the request said think: false; "
            "check the model with the smoke check (llm.smoke)"
        )
    mass = label_masses(response, labels)
    if mass is None:
        raise ReaderError("the server returned no logprobs; check the model with the smoke check (llm.smoke)")
    total = sum(mass.values())
    if total == 0:
        return mass, 1.0
    return {label: p / total for label, p in mass.items()}, max(0.0, 1.0 - total)
