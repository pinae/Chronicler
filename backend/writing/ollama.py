"""Story writers backed by Ollama (concept §9.4, R2).

`OllamaStoryWriter` sees the engine's structure: the strongest readings of the lattice, what the
audience expects and the target twist, and drafts the beat its paragraph is meant to convey.
`OllamaProseWriter` sees the story so far and nothing else; comparing the two (WP-051) asks whether
the structure helps."""

from collections.abc import Mapping, Sequence
from typing import Any

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from chronicle.ingest.interfaces import IngestedBeat
from chronicle.ingest.ollama import beat_problem, predicate_lines, transport_from_settings
from evaluation.ground_truth import TrueHypothesis
from llm.cache import CachedOllama
from llm.json_answers import JsonAnswers
from llm.transport import OllamaTransport
from matching.engine import COMPLETE, LIVE
from matching.lattice import LatticeHypothesis
from matching.models import Expectation
from schemas.vocabulary import default_vocabulary
from writing.interfaces import Continuation, StoryEntity, WritingRequest

PARAGRAPHS_IN_PROMPT = 20
READINGS_IN_PROMPT = 5
TEMPERATURE = 0.7  # a writer, unlike a reader, should not always pick the likeliest word

PROSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"prose": {"type": "string"}},
    "required": ["prose"],
}
PROSE_AND_BEAT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "prose": {"type": "string"},
        "beat": {
            "type": "object",
            "properties": {
                "pred": {"type": "string"},
                "args": {"type": "object"},
                "present": {"type": "array", "items": {"type": "string"}},
                "text": {"type": "string"},
            },
            "required": ["pred", "args", "text"],
        },
    },
    "required": ["prose", "beat"],
}


def writer_model() -> str:
    if not settings.OLLAMA_WRITER_MODEL:
        raise ImproperlyConfigured("OLLAMA_WRITER_MODEL is not set; the story writer needs a model name")
    model: str = settings.OLLAMA_WRITER_MODEL
    return model


class OllamaProseWriter:
    """Continues the story from the prose alone."""

    schema = PROSE_SCHEMA

    def __init__(self, transport: OllamaTransport | None = None) -> None:
        self.model = writer_model()
        self.answers = JsonAnswers(CachedOllama(transport or transport_from_settings()), self.schema)

    def continue_story(self, request: WritingRequest) -> Continuation:
        answer = self.ask(self.prompt(request))
        return Continuation(prose=str(answer.get("prose", "")).strip())

    def prompt(self, request: WritingRequest) -> str:
        return "\n".join(
            [
                "You are writing a story, one short paragraph at a time.",
                "",
                *story_so_far(request.prefix),
                "",
                "Write the next paragraph: one to three sentences that move the story on.",
                'Reply with JSON: {"prose": the paragraph}.',
            ]
        )

    def ask(self, prompt: str) -> dict[str, Any]:
        return self.answers.ask(
            {
                "model": self.model,
                "prompt": prompt,
                "options": {"temperature": TEMPERATURE, "num_ctx": settings.OLLAMA_NUM_CTX},
                "keep_alive": settings.OLLAMA_KEEP_ALIVE,
            }
        )


class OllamaStoryWriter(OllamaProseWriter):
    """Continues the story toward the target, with the engine's structure in the prompt."""

    schema = PROSE_AND_BEAT_SCHEMA

    def continue_story(self, request: WritingRequest) -> Continuation:
        answer = self.ask(self.prompt(request))
        return Continuation(
            prose=str(answer.get("prose", "")).strip(), intended=intended_beat(answer.get("beat"), request)
        )

    def prompt(self, request: WritingRequest) -> str:
        names = {entity.id: entity.name for entity in request.entities}
        return "\n".join(
            [
                "You are writing a story, one short paragraph at a time, toward a twist that the reader "
                "should see coming only in hindsight.",
                "",
                *story_so_far(request.prefix),
                "",
                "Where the story could be going (the strongest readings, and what has happened for each):",
                *(reading_line(hypothesis, names) for hypothesis in strongest_readings(request)),
                "",
                "What the audience expects next:",
                *(expectation_line(expectation) for expectation in request.expectations),
                "" if request.expectations else "(nothing asked yet)",
                f"Write toward: {target_text(request.target, request.entities)}. Plant clues for it "
                "without giving it away, and keep the other readings alive.",
                "",
                "Write the next paragraph (one to three sentences) and the one beat it conveys, with "
                "these predicates (role: allowed values; a role ending in ? is optional):",
                *(f"- {line}" for line in predicate_lines(default_vocabulary())),
                "",
                'Entities (write them as "@slug"):',
                *(f"- @{entity.slug}: {entity.name} ({entity.kind})" for entity in request.entities),
                "",
                'Reply with JSON: {"prose": the paragraph, "beat": {"pred", "args", "present": '
                '[slugs of characters who witness it], "text": a short sentence}}.',
            ]
        )


def story_so_far(prefix: Sequence[str]) -> list[str]:
    recent = prefix[-PARAGRAPHS_IN_PROMPT:]
    return (
        [f"The story so far (last {len(recent)} paragraphs):", *recent] if recent else ["(The story begins.)"]
    )


def strongest_readings(request: WritingRequest) -> list[LatticeHypothesis]:
    held = [h for h in request.lattice.hypotheses if h.status in (LIVE, COMPLETE) and h.fills]
    return sorted(held, key=lambda h: (-h.weight, h.created_at_t))[:READINGS_IN_PROMPT]


def reading_line(hypothesis: LatticeHypothesis, names: Mapping[int, str]) -> str:
    binding = ", ".join(
        f"{role} = {names.get(entity, '?') if entity is not None else '?'}"
        for role, entity in hypothesis.binding.items()
    )
    so_far = ", ".join(f"{fill.step_id} at t={fill.beat_t}" for fill in hypothesis.fills)
    return (
        f"- {schema_title(hypothesis.schema)}: {binding} (weight {hypothesis.weight:.1f}; so far: {so_far})"
    )


def expectation_line(expectation: Expectation) -> str:
    candidates = ", ".join(
        f"{candidate['text']} {candidate['p']:.0%}" for candidate in expectation.candidates
    )
    return f"- {expectation.question} {candidates}"


def target_text(target: TrueHypothesis, entities: Sequence[StoryEntity]) -> str:
    names = {entity.slug: entity.name for entity in entities}
    roles = ", ".join(f"{role} = {names.get(slug, slug)}" for role, slug in target.binding.items())
    return f"a {schema_title(target.schema)} with {roles}"


def schema_title(slug: str) -> str:
    return slug.replace("_", " ").capitalize()


def intended_beat(raw: object, request: WritingRequest) -> IngestedBeat | None:
    """The drafted beat, if it fits the vocabulary and names only entities the story knows."""
    if not isinstance(raw, Mapping):
        return None
    pred, args = str(raw.get("pred", "")), raw.get("args") or {}
    present = tuple(str(slug).lstrip("@") for slug in raw.get("present") or [])
    slugs = {entity.slug for entity in request.entities}
    if beat_problem(pred, args, present, "narration", slugs, default_vocabulary(), request.lattice.t + 1):
        return None
    return IngestedBeat(pred=pred, args=dict(args), present=present, text=str(raw.get("text", "")))
