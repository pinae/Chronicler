"""Drafting a story's beats and entities with the configured ingester, for human review (R1).

The transcript runs through the pipeline (ingest, entities, append) inside a transaction that is
rolled back, so later utterances are ingested against the entities and beats drafted so far, and
nothing is kept. What the ingester proposed is returned in the fixture format (beats.yaml,
entities.yaml), with `review` marks where a human has to decide."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from django.db import transaction

from chronicle.beat_log import AppendError
from chronicle.ingest.interfaces import IngestedBeat, Ingester, IngestResult, NewEntity
from chronicle.models import Chronicle, Entity, Player, Utterance
from chronicle.story_fixtures import EntitySpec, Transcript, UtteranceSpec, read_entities, read_transcript
from narrative_engine.pipeline import IngestError, Pipeline, create_entity
from reader.context import RecentAndSupportingBeats
from schemas.vocabulary import BeatArgsError, default_vocabulary

NARRATION = "narration"


@dataclass
class StoryDraft:
    utterance_count: int
    beats: list[dict[str, Any]] = field(default_factory=list)  # beats.yaml
    entities: dict[str, dict[str, Any]] = field(default_factory=dict)  # entities.yaml

    @property
    def beat_count(self) -> int:
        return sum(len(entry.get("beats", [])) for entry in self.beats)

    @property
    def review_count(self) -> int:
        """Utterances and beats a human has to look at."""
        return sum(
            ("review" in entry) + sum("review" in beat for beat in entry.get("beats", []))
            for entry in self.beats
        )


class RecordingIngester:
    """Passes each utterance to the real ingester and keeps what it proposed."""

    def __init__(self, ingester: Ingester) -> None:
        self.ingester = ingester
        self.last_result = IngestResult()

    def ingest(self, chronicle: Chronicle, utterance: Utterance) -> IngestResult:
        self.last_result = self.ingester.ingest(chronicle, utterance)
        return self.last_result


def draft_story(slug: str, stories_dir: Path, ingester: Ingester) -> StoryDraft:
    """Entities the story already declares (e.g. the outlet of a media story) are known from the
    start and kept."""
    transcript = read_transcript(slug, stories_dir)
    declared = read_entities(slug, stories_dir)
    with transaction.atomic():
        draft = draft_transcript(slug, transcript, declared, ingester)
        transaction.set_rollback(True)
    return draft


def draft_transcript(
    slug: str, transcript: Transcript, declared: Sequence[EntitySpec], ingester: Ingester
) -> StoryDraft:
    chronicle = Chronicle.objects.create(kind=transcript.kind, title=transcript.title, meta={"fixture": slug})
    players = {name: Player.objects.create(chronicle=chronicle, name=name) for name in transcript.players}
    entities = {entity.slug: create_entity(chronicle, new_entity(entity), 1) for entity in declared}
    recorder = RecordingIngester(ingester)
    pipeline = Pipeline(
        chronicle, recorder, reader=None, context_builder=RecentAndSupportingBeats(), audiences=()
    )
    draft = StoryDraft(utterance_count=len(transcript.utterances))
    draft.entities = {entity.slug: entity_entry(new_entity(entity)) for entity in declared}
    for spec in transcript.utterances:
        utterance = create_utterance(chronicle, spec, players, entities)
        try:
            pipeline.process(utterance)
        except (IngestError, AppendError, BeatArgsError) as error:
            draft.beats.append({"utterance": spec.order, "review": [str(error)]})
            continue
        add_result(draft, spec.order, recorder.last_result)
    return draft


def create_utterance(
    chronicle: Chronicle, spec: UtteranceSpec, players: Mapping[str, Player], entities: Mapping[str, Entity]
) -> Utterance:
    """A speaker is a player, a declared entity (a media outlet) or, like the GM and the narrator,
    no one in particular."""
    return Utterance.objects.create(
        chronicle=chronicle,
        order=spec.order,
        speaker_player=players.get(spec.speaker),
        speaker_entity=entities.get(spec.speaker),
        text=spec.text,
        source=spec.source,
    )


def new_entity(spec: EntitySpec) -> NewEntity:
    return NewEntity(slug=spec.slug, kind=spec.kind, name=spec.name, aliases=tuple(spec.aliases))


def add_result(draft: StoryDraft, order: int, result: IngestResult) -> None:
    for entity in result.new_entities:
        draft.entities[entity.slug] = entity_entry(entity)
    entry: dict[str, Any] = {"utterance": order}
    if result.beats:
        entry["beats"] = [beat_entry(beat) for beat in result.beats]
    if result.theories:
        entry["theories"] = [
            {"schema": theory.schema, "binding": dict(theory.binding)} for theory in result.theories
        ]
    if result.problems:
        entry["review"] = list(result.problems)
    if len(entry) > 1:
        draft.beats.append(entry)


def beat_entry(beat: IngestedBeat) -> dict[str, Any]:
    entry: dict[str, Any] = {"pred": beat.pred, "args": dict(beat.args)}
    if beat.present:
        entry["present"] = list(beat.present)
    if beat.players is not None:
        entry["players"] = list(beat.players)
    if beat.source_kind != NARRATION:
        entry["kind"] = beat.source_kind
    if beat.text:
        entry["text"] = beat.text
    if beat.tags:
        entry["tags"] = list(beat.tags)
    entry["confidence"] = beat.confidence
    if beat.pred not in default_vocabulary():
        entry["review"] = (
            f"unknown predicate '{beat.pred}': map it onto the vocabulary, "
            "or remove this mark to keep it quarantined"
        )
    return entry


def entity_entry(entity: NewEntity) -> dict[str, Any]:
    entry: dict[str, Any] = {"kind": entity.kind, "name": entity.name}
    if entity.aliases:
        entry["aliases"] = list(entity.aliases)
    return entry
