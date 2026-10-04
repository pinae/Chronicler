"""Production ingest: an utterance becomes canonical beats via Ollama (concept §3, §8.3).

The model answers in JSON with beats in the compact `@slug` notation. Predicates are deliberately not
restricted to the vocabulary: an unknown verb is quarantined on append, which is how coverage shows
what the vocabulary cannot express (RQ1), instead of forcing a poor fit. Invalid drafts get one
repair round; whatever is still invalid is dropped and reported.
"""

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.text import slugify

from chronicle.beat_args import referenced_beat_ts
from chronicle.ingest.interfaces import IngestedBeat, IngestResult, NewEntity
from chronicle.models import Chronicle, EntityKind, SourceKind, Utterance
from chronicle.story_fixtures import expand_args
from llm.cache import CachedOllama
from llm.json_answers import JsonAnswers
from llm.transport import HttpOllamaTransport, OllamaTransport
from schemas.vocabulary import InvalidBeatArgs, UnknownPredicate, ValueKind, Vocabulary, default_vocabulary

RECENT_BEATS_IN_PROMPT = 10
KIND_ORDER = list(ValueKind)

ANSWER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "slug": {"type": "string"},
                    "kind": {"type": "string", "enum": list(EntityKind.values)},
                    "name": {"type": "string"},
                    "aliases": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["slug", "kind", "name"],
            },
        },
        "beats": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "pred": {"type": "string"},
                    "args": {"type": "object"},
                    "present": {"type": "array", "items": {"type": "string"}},
                    "kind": {"type": "string", "enum": list(SourceKind.values)},
                    "text": {"type": "string"},
                    "confidence": {"type": "number"},
                },
                "required": ["pred", "args", "text"],
            },
        },
    },
    "required": ["entities", "beats"],
}


@dataclass(frozen=True)
class KnownEntity:
    slug: str
    kind: str
    name: str
    aliases: tuple[str, ...]

    @property
    def names(self) -> set[str]:
        return {name.casefold() for name in (self.name, *self.aliases)}


class OllamaIngester:
    def __init__(self, transport: OllamaTransport | None = None) -> None:
        if not settings.OLLAMA_INGEST_MODEL:
            raise ImproperlyConfigured("OLLAMA_INGEST_MODEL is not set; ingest needs a model name")
        self.model = settings.OLLAMA_INGEST_MODEL
        self.answers = JsonAnswers(CachedOllama(transport or transport_from_settings()), ANSWER_SCHEMA)
        self.vocabulary = default_vocabulary()

    def ingest(self, chronicle: Chronicle, utterance: Utterance) -> IngestResult:
        known = known_entities(chronicle)
        next_t = chronicle.beats.count() + 1
        prompt = ingest_prompt(chronicle, utterance, known, self.vocabulary)
        answer = self.ask(prompt)
        proposal = Proposal.from_answer(answer, known, self.vocabulary, next_t)
        if proposal.problems:
            answer = self.ask(repair_prompt(prompt, answer, proposal.problems))
            proposal = Proposal.from_answer(answer, known, self.vocabulary, next_t)
        return IngestResult(
            beats=tuple(proposal.valid_beats),
            new_entities=tuple(proposal.new_entities),
            problems=tuple(proposal.problems),
        )

    def ask(self, prompt: str) -> dict[str, Any]:
        return self.answers.ask(
            {
                "model": self.model,
                "prompt": prompt,
                "options": {"temperature": 0, "num_ctx": settings.OLLAMA_NUM_CTX},
                "keep_alive": settings.OLLAMA_KEEP_ALIVE,
            }
        )


def transport_from_settings() -> OllamaTransport:
    if not settings.OLLAMA_BASE_URL:
        raise ImproperlyConfigured("OLLAMA_BASE_URL is not set; ingest needs the Ollama server")
    return HttpOllamaTransport(settings.OLLAMA_BASE_URL, settings.OLLAMA_TIMEOUT_S)


def known_entities(chronicle: Chronicle) -> list[KnownEntity]:
    return [
        KnownEntity(
            slug=entity.slug, kind=entity.kind, name=entity.canonical_name, aliases=tuple(entity.aliases)
        )
        for entity in chronicle.entities.exclude(slug="").order_by("slug")
    ]


# Prompts


def ingest_prompt(
    chronicle: Chronicle, utterance: Utterance, known: Sequence[KnownEntity], vocabulary: Vocabulary
) -> str:
    recent = chronicle.beats.order_by("-t")[:RECENT_BEATS_IN_PROMPT]
    recent_lines = [f"t={beat.t}: {beat.text}" for beat in sorted(recent, key=lambda beat: beat.t)]
    return "\n".join(
        [
            "You turn what is said in a story into formal beats: facts about the story world.",
            "",
            "Predicates (role: allowed values; a role ending in ? is optional):",
            *(f"- {line}" for line in predicate_lines(vocabulary)),
            "",
            'Values: "@slug" for a known or new entity, "#t" for the beat at time t, '
            '{"pred": ..., "args": {...}} for a nested statement (claims, beliefs), '
            "anything else is a literal.",
            "Map verbs onto these predicates (lends, hands over -> gives). "
            "If none fits, use a short verb of your own.",
            "",
            "Known entities:",
            *(entity_line(entity) for entity in known),
            "" if known else "(none yet)",
            "Recent beats:",
            *(recent_lines or ["(none yet)"]),
            "",
            f"Speaker: {speaker_of(utterance)}",
            f"Utterance: {utterance.text}",
            "",
            'Reply with JSON: {"entities": [new entities as {"slug", "kind", "name", "aliases"}], '
            '"beats": [{"pred", "args", "present": [slugs of characters who witness it], '
            '"kind": "narration|action|claim", "text": a short sentence, "confidence": 0..1}]}.',
            "If the utterance states nothing that happens in the story, reply with no beats.",
        ]
    )


def predicate_lines(vocabulary: Vocabulary) -> list[str]:
    lines = []
    for name in vocabulary.predicate_names:
        roles = vocabulary.predicate(name).roles.values()
        described = [
            f"{role.name}{'?' if role.optional else ''}: {'|'.join(k for k in KIND_ORDER if k in role.kinds)}"
            for role in roles
        ]
        lines.append(f"{name}({', '.join(described)})")
    return lines


def entity_line(entity: KnownEntity) -> str:
    aliases = "; also " + ", ".join(f'"{alias}"' for alias in entity.aliases) if entity.aliases else ""
    return f"@{entity.slug}: {entity.name} ({entity.kind}{aliases})"


def speaker_of(utterance: Utterance) -> str:
    if utterance.speaker_player is not None:
        return f"player {utterance.speaker_player.name}"
    if utterance.speaker_entity is not None:
        return utterance.speaker_entity.canonical_name
    return "game master or narrator"


def repair_prompt(prompt: str, answer: Mapping[str, Any], problems: Sequence[str]) -> str:
    return "\n".join(
        [
            prompt,
            "",
            "Your previous answer was:",
            json.dumps(answer, ensure_ascii=False),
            "It has these problems:",
            *(f"- {problem}" for problem in problems),
            "Reply with the corrected JSON.",
        ]
    )


# Checking what the model proposed


@dataclass
class Proposal:
    new_entities: list[NewEntity] = field(default_factory=list)
    valid_beats: list[IngestedBeat] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)

    @classmethod
    def from_answer(
        cls, answer: Mapping[str, Any], known: Sequence[KnownEntity], vocabulary: Vocabulary, next_t: int
    ) -> "Proposal":
        proposal = cls()
        renames = proposal.resolve_entities(answer.get("entities") or [], known)
        slugs = {entity.slug for entity in known} | {entity.slug for entity in proposal.new_entities}
        for number, raw in enumerate(answer.get("beats") or [], start=1):
            proposal.check_beat(number, raw, renames, slugs, vocabulary, next_t)
        return proposal

    def resolve_entities(
        self, proposed: Iterable[Mapping[str, Any]], known: Sequence[KnownEntity]
    ) -> dict[str, str]:
        """New entities that match a known name or alias are the known entity; taken slugs are renamed."""
        renames: dict[str, str] = {}
        taken = {entity.slug for entity in known}
        for raw in proposed:
            proposed_slug = str(raw.get("slug") or "")
            names = {str(name).casefold() for name in [raw.get("name", ""), *raw.get("aliases", [])] if name}
            match = next((entity for entity in known if entity.names & names), None)
            if match is not None:
                renames[proposed_slug] = match.slug
                continue
            if raw.get("kind") not in EntityKind.values:
                self.problems.append(f"entity '{proposed_slug}': unknown kind '{raw.get('kind')}'")
                continue
            slug = unique_slug(slugify(proposed_slug or raw.get("name", "")) or "entity", taken)
            taken.add(slug)
            renames[proposed_slug] = slug
            self.new_entities.append(
                NewEntity(
                    slug=slug, kind=raw["kind"], name=str(raw["name"]), aliases=tuple(raw.get("aliases", []))
                )
            )
        return renames

    def check_beat(
        self,
        number: int,
        raw: Mapping[str, Any],
        renames: Mapping[str, str],
        slugs: set[str],
        vocabulary: Vocabulary,
        next_t: int,
    ) -> None:
        pred = str(raw.get("pred", ""))
        args = rename_slugs(raw.get("args") or {}, renames)
        present = tuple(
            renames.get(slug, slug) for slug in (str(s).lstrip("@") for s in raw.get("present") or [])
        )
        problem = beat_problem(pred, args, present, raw.get("kind", "narration"), slugs, vocabulary, next_t)
        if problem:
            self.problems.append(f"beat {number} ({pred}): {problem}")
            return
        self.valid_beats.append(
            IngestedBeat(
                pred=pred,
                args=args,
                present=present,
                source_kind=raw.get("kind", "narration"),
                text=str(raw.get("text", "")),
                confidence=float(raw.get("confidence", 1.0)),
            )
        )


@dataclass(frozen=True)
class StandIn:
    """Takes an entity's place when checking a draft before the entity exists."""

    id: int


def unique_slug(slug: str, taken: set[str]) -> str:
    candidate, number = slug, 2
    while candidate in taken:
        candidate, number = f"{slug}-{number}", number + 1
    return candidate


def rename_slugs(args: Mapping[str, Any], renames: Mapping[str, str]) -> dict[str, Any]:
    def renamed(value: Any) -> Any:
        if isinstance(value, str) and value.startswith("@"):
            return "@" + renames.get(value[1:], value[1:])
        if isinstance(value, Mapping) and "pred" in value:
            return {"pred": value["pred"], "args": rename_slugs(value.get("args") or {}, renames)}
        return value

    return {role: renamed(value) for role, value in args.items()}


def beat_problem(
    pred: str,
    args: Mapping[str, Any],
    present: Sequence[str],
    source_kind: str,
    slugs: set[str],
    vocabulary: Vocabulary,
    next_t: int,
) -> str | None:
    if source_kind not in SourceKind.values:
        return f"unknown kind '{source_kind}'"
    stand_ins = {slug: StandIn(id=index) for index, slug in enumerate(sorted(slugs), start=1)}
    unknown = sorted(slug for slug in present if slug not in stand_ins)
    try:
        expanded = expand_args(args, stand_ins)
    except KeyError as error:
        unknown.append(str(error).strip("'"))
    if unknown:
        return f"unknown entity '{unknown[0]}'"
    try:
        vocabulary.validate_args(pred, expanded)
    except UnknownPredicate:
        pass  # kept: append quarantines it, coverage reports it
    except InvalidBeatArgs as error:
        return str(error)
    later = sorted(t for t in referenced_beat_ts(expanded) if t >= next_t)
    if later:
        return f"refers to beat t={later[0]}, which has not happened yet"
    return None
