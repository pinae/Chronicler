"""Hand-written stories under fixtures/stories/<slug>/ (concept §9.1).

The format is documented in fixtures/stories/README.md. `read_story` parses the files into plain
data; `load_story` builds a chronicle from it by appending every beat, exactly like ingest would.
"""

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import yaml
from django.conf import settings
from django.db import transaction

from chronicle.beat_log import BeatDraft
from chronicle.models import Chronicle, Entity, Player, Utterance

STORIES_DIR: Path = settings.BASE_DIR / "fixtures" / "stories"
SPEAKERS_WITHOUT_IDENTITY = {"gm", "narrator"}


class StoryFixtureError(Exception):
    pass


@dataclass(frozen=True)
class EntitySpec:
    slug: str
    kind: str
    name: str
    aliases: list[str]


@dataclass(frozen=True)
class UtteranceSpec:
    order: int
    speaker: str
    text: str
    source: dict[str, Any]


@dataclass(frozen=True)
class BeatSpec:
    location: str  # "utterance 3, beat 2", for error messages
    utterance_order: int
    pred: str
    args: dict[str, Any]  # compact notation: "@slug", "#t", nested {pred, args}, literals
    characters: list[str]
    players: list[str] | None  # None: every player at the table
    source_kind: str
    text: str
    tags: list[str]
    confidence: float
    declared_t: int | None


@dataclass(frozen=True)
class TheorySpec:
    """A theory a player voices ("I bet the steward is the traitor"), at the t of the last beat before it."""

    utterance_order: int
    schema: str
    binding: dict[str, str]  # role -> entity slug
    voiced_at_t: int


@dataclass(frozen=True)
class StoryFixture:
    slug: str
    title: str
    kind: str
    players: list[str]
    utterances: list[UtteranceSpec]
    entities: list[EntitySpec]
    beats: list[BeatSpec]
    theories: list[TheorySpec]


def read_story(slug: str, stories_dir: Path = STORIES_DIR) -> StoryFixture:
    directory = stories_dir / slug
    transcript = read_yaml(directory / "transcript.yaml")
    beat_entries = read_yaml(directory / "beats.yaml") or []
    story = StoryFixture(
        slug=slug,
        title=transcript["title"],
        kind=transcript["kind"],
        players=list(transcript.get("players", [])),
        utterances=[read_utterance(entry) for entry in transcript["utterances"]],
        entities=[read_entity(slug, entry) for slug, entry in read_yaml(directory / "entities.yaml").items()],
        beats=list(read_beats(beat_entries)),
        theories=list(read_theories(beat_entries)),
    )
    check_entity_mentions(story)
    check_theories(story)
    return story


def read_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError) as error:
        raise StoryFixtureError(f"{path.name}: {error}") from error


def read_utterance(entry: Mapping[str, Any]) -> UtteranceSpec:
    return UtteranceSpec(
        order=entry["order"],
        speaker=str(entry.get("speaker", "gm")),
        text=entry["text"],
        source=dict(entry.get("source", {})),
    )


def read_entity(slug: str, entry: Mapping[str, Any]) -> EntitySpec:
    return EntitySpec(
        slug=slug, kind=entry["kind"], name=entry["name"], aliases=list(entry.get("aliases", []))
    )


def read_beats(utterance_entries: list[Mapping[str, Any]]) -> Iterator[BeatSpec]:
    for utterance_entry in utterance_entries or []:
        order = utterance_entry["utterance"]
        for position, entry in enumerate(utterance_entry.get("beats", []), start=1):
            players = entry.get("players")
            yield BeatSpec(
                location=f"utterance {order}, beat {position}",
                utterance_order=order,
                pred=entry["pred"],
                args=dict(entry.get("args", {})),
                characters=list(entry.get("present", [])),
                players=None if players is None else list(players),
                source_kind=entry.get("kind", "narration"),
                text=entry.get("text", ""),
                tags=list(entry.get("tags", [])),
                confidence=entry.get("confidence", 1.0),
                declared_t=entry.get("t"),
            )


def read_theories(utterance_entries: list[Mapping[str, Any]]) -> Iterator[TheorySpec]:
    beats_so_far = 0
    for utterance_entry in utterance_entries:
        for entry in utterance_entry.get("theories", []):
            yield TheorySpec(
                utterance_order=utterance_entry["utterance"],
                schema=entry["schema"],
                binding=dict(entry["binding"]),
                voiced_at_t=beats_so_far,
            )
        beats_so_far += len(utterance_entry.get("beats", []))


def check_theories(story: StoryFixture) -> None:
    speakers = {utterance.order: utterance.speaker for utterance in story.utterances}
    declared = {entity.slug for entity in story.entities}
    for theory in story.theories:
        location = f"beats.yaml, utterance {theory.utterance_order}"
        if speakers.get(theory.utterance_order) not in story.players:
            raise StoryFixtureError(f"{location}: a theory must be voiced by a player")
        unknown = sorted(set(theory.binding.values()) - declared)
        if unknown:
            raise StoryFixtureError(f"{location}: theory names unknown entity '{unknown[0]}'")


def mentioned_slugs(compact_args: Mapping[str, Any]) -> Iterator[str]:
    for value in compact_args.values():
        if isinstance(value, str) and value.startswith("@"):
            yield value[1:]
        elif isinstance(value, Mapping) and "pred" in value:
            yield from mentioned_slugs(value.get("args", {}))
        elif isinstance(value, Mapping) and set(value) == {"entity"}:
            yield value["entity"]


def first_mentions(story: StoryFixture) -> dict[str, int]:
    """The t of the first beat that mentions each entity, in its arguments or as present."""
    mentions: dict[str, int] = {}
    for t, beat in enumerate(story.beats, start=1):
        for slug in [*mentioned_slugs(beat.args), *beat.characters]:
            mentions.setdefault(slug, t)
    return mentions


def check_entity_mentions(story: StoryFixture) -> None:
    declared = {entity.slug for entity in story.entities}
    for beat in story.beats:
        unknown = sorted({*mentioned_slugs(beat.args), *beat.characters} - declared)
        if unknown:
            raise StoryFixtureError(f"beats.yaml, {beat.location}: unknown entity '{unknown[0]}'")
    never_mentioned = sorted(declared - first_mentions(story).keys())
    if never_mentioned:
        raise StoryFixtureError(
            f"entities.yaml: entity '{never_mentioned[0]}' is never mentioned in beats.yaml"
        )


def load_story(slug: str, stories_dir: Path = STORIES_DIR, until_t: int | None = None) -> Chronicle:
    """Build a chronicle from a fixture story; with `until_t`, only the beats up to that t."""
    return build_chronicle(read_story(slug, stories_dir), until_t)


def build_chronicle(story: StoryFixture, until_t: int | None = None) -> Chronicle:
    with transaction.atomic():
        chronicle = Chronicle.objects.create(kind=story.kind, title=story.title, meta={"fixture": story.slug})
        players = {name: Player.objects.create(chronicle=chronicle, name=name) for name in story.players}
        entities = create_entities(chronicle, story)
        utterances = {
            spec.order: create_utterance(chronicle, spec, players, entities) for spec in story.utterances
        }
        for t, spec in enumerate(story.beats[:until_t], start=1):
            append_fixture_beat(chronicle, t, spec, utterances, players, entities)
        return chronicle


def create_entities(chronicle: Chronicle, story: StoryFixture) -> dict[str, Entity]:
    introduced_at = first_mentions(story)
    return {
        spec.slug: Entity.objects.create(
            chronicle=chronicle,
            slug=spec.slug,
            kind=spec.kind,
            canonical_name=spec.name,
            aliases=spec.aliases,
            introduced_at_t=introduced_at[spec.slug],
        )
        for spec in story.entities
    }


def create_utterance(
    chronicle: Chronicle, spec: UtteranceSpec, players: Mapping[str, Player], entities: Mapping[str, Entity]
) -> Utterance:
    speaker = spec.speaker
    if speaker not in SPEAKERS_WITHOUT_IDENTITY | players.keys() | entities.keys():
        raise StoryFixtureError(f"transcript.yaml, utterance {spec.order}: unknown speaker '{speaker}'")
    return Utterance.objects.create(
        chronicle=chronicle,
        order=spec.order,
        speaker_player=players.get(speaker),
        speaker_entity=entities.get(speaker),
        text=spec.text,
        source=spec.source,
    )


def append_fixture_beat(
    chronicle: Chronicle,
    t: int,
    spec: BeatSpec,
    utterances: Mapping[int, Utterance],
    players: Mapping[str, Player],
    entities: Mapping[str, Entity],
) -> None:
    if spec.declared_t is not None and spec.declared_t != t:
        raise StoryFixtureError(
            f"beats.yaml, {spec.location}: declared t={spec.declared_t}, but this beat is t={t}"
        )
    present_players = players.values() if spec.players is None else [players[name] for name in spec.players]
    draft = BeatDraft(
        pred=spec.pred,
        args=expand_args(spec.args, entities),
        source_utterance=utterances[spec.utterance_order],
        source_kind=spec.source_kind,
        text=spec.text,
        tags=spec.tags,
        confidence=spec.confidence,
        characters_present=[entities[slug].id for slug in spec.characters],
        players_present=[player.id for player in present_players],
    )
    try:
        chronicle.append(draft, t=t)
    except ValueError as error:  # invalid arguments, references or t
        raise StoryFixtureError(f"beats.yaml, {spec.location}: {error}") from error


class Identified(Protocol):
    @property
    def id(self) -> int: ...


def expand_args(compact_args: Mapping[str, Any], entities: Mapping[str, Identified]) -> dict[str, Any]:
    return {role: expand_value(value, entities) for role, value in compact_args.items()}


def expand_value(value: Any, entities: Mapping[str, Identified]) -> dict[str, Any]:
    if isinstance(value, str) and value.startswith("@"):
        return {"entity": entities[value[1:]].id}
    if isinstance(value, str) and value.startswith("#") and value[1:].isdigit():
        return {"beat": int(value[1:])}
    if isinstance(value, Mapping) and "pred" in value:
        return {"prop": {"pred": value["pred"], "args": expand_args(value.get("args", {}), entities)}}
    if isinstance(value, Mapping) and set(value) == {"entity"}:
        return {"entity": entities[value["entity"]].id}
    if isinstance(value, Mapping) and len(value) == 1 and set(value) <= {"literal", "beat"}:
        return dict(value)
    return {"literal": value}
