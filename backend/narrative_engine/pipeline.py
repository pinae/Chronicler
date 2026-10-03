"""The pipeline (concept §3): utterance → ingest → append → scope and entity view → matcher → readouts.

One `Pipeline` serves one chronicle. Each audience gets its own lattice: None is the unfiltered lattice
over every beat (the GM's), a player gets the lattice of what they have seen. With a reader, every
beat is followed by readouts for every audience.
"""

from collections.abc import Mapping, Sequence

from django.db import transaction

from chronicle.beat_log import BeatDraft
from chronicle.ingest.interfaces import IngestedBeat, IngestedTheory, Ingester, IngestResult, NewEntity
from chronicle.models import Beat, Chronicle, Entity, Player, Utterance
from chronicle.story_fixtures import expand_args, mentioned_slugs
from matching.store import StoredMatcher
from reader.context import ContextBuilder
from reader.expectations import seed_expectations
from reader.interfaces import ReaderModel


class IngestError(ValueError):
    pass


class Pipeline:
    def __init__(
        self,
        chronicle: Chronicle,
        ingester: Ingester,
        reader: ReaderModel | None,
        context_builder: ContextBuilder,
        audiences: Sequence[Player | None] = (None,),
    ) -> None:
        self.chronicle = chronicle
        self.ingester = ingester
        self.reader = reader
        self.context_builder = context_builder
        self.matchers = {audience: StoredMatcher(chronicle, for_player=audience) for audience in audiences}

    def process(self, utterance: Utterance) -> list[Beat]:
        result = self.ingester.ingest(self.chronicle, utterance)
        with transaction.atomic():
            self.create_entities(result)
            entities = self.entities_by_slug()
            self.voice(result.theories, utterance, entities)
            return [self.process_beat(draft, utterance, entities) for draft in result.beats]

    def process_beat(self, draft: IngestedBeat, utterance: Utterance, entities: Mapping[str, Entity]) -> Beat:
        beat = self.chronicle.append(self.beat_draft(draft, utterance, entities))
        for matcher in self.matchers.values():
            matcher.step(beat)
        if self.reader is not None:
            for audience in self.matchers:
                seed_expectations(self.chronicle, beat.t, audience, self.reader, self.context_builder)
        return beat

    def create_entities(self, result: IngestResult) -> None:
        """New entities are introduced at the t of the first beat of this utterance that mentions them."""
        next_t = self.chronicle.beats.count() + 1
        first_mention: dict[str, int] = {}
        for offset, draft in enumerate(result.beats):
            for slug in [*mentioned_slugs(draft.args), *draft.present]:
                first_mention.setdefault(slug, next_t + offset)
        for entity in result.new_entities:
            create_entity(self.chronicle, entity, first_mention.get(entity.slug, next_t))

    def entities_by_slug(self) -> dict[str, Entity]:
        return {entity.slug: entity for entity in self.chronicle.entities.exclude(slug="")}

    def voice(
        self, theories: Sequence[IngestedTheory], utterance: Utterance, entities: Mapping[str, Entity]
    ) -> None:
        if not theories:
            return
        speaker = utterance.speaker_player
        if speaker is None:
            raise IngestError(f"utterance {utterance.order}: only players voice theories")
        t = self.chronicle.beats.count()
        for theory in theories:
            binding = {role: self.entity(entities, slug).pk for role, slug in theory.binding.items()}
            for audience, matcher in self.matchers.items():
                if audience is None or audience == speaker:
                    matcher.voice(theory.schema, binding, speaker, utterance, t)

    def beat_draft(
        self, draft: IngestedBeat, utterance: Utterance, entities: Mapping[str, Entity]
    ) -> BeatDraft:
        try:
            args = expand_args(draft.args, entities)
        except KeyError as error:
            raise IngestError(f"utterance {utterance.order}: unknown entity {error}") from None
        return BeatDraft(
            pred=draft.pred,
            args=args,
            source_utterance=utterance,
            source_kind=draft.source_kind,
            text=draft.text,
            tags=draft.tags,
            confidence=draft.confidence,
            characters_present=[self.entity(entities, slug).pk for slug in draft.present],
            players_present=[player.pk for player in self.players_named(draft.players)],
        )

    def players_named(self, names: Sequence[str] | None) -> list[Player]:
        players = self.chronicle.players.filter(implicit=False)
        if names is None:
            return list(players)
        return list(players.filter(name__in=names))

    def entity(self, entities: Mapping[str, Entity], slug: str) -> Entity:
        try:
            return entities[slug]
        except KeyError:
            raise IngestError(f"unknown entity '{slug}'") from None


def create_entity(chronicle: Chronicle, entity: NewEntity, introduced_at_t: int) -> Entity:
    return Entity.objects.create(
        chronicle=chronicle,
        slug=entity.slug,
        kind=entity.kind,
        canonical_name=entity.name,
        aliases=list(entity.aliases),
        introduced_at_t=introduced_at_t,
    )
