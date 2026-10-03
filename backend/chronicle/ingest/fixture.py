"""An ingester that replays the hand-authored beats of a fixture story (for tests and replays)."""

from pathlib import Path

from django.conf import settings

from chronicle.ingest.interfaces import IngestedBeat, IngestedTheory, IngestResult, NewEntity
from chronicle.models import Chronicle, Utterance
from chronicle.story_fixtures import BeatSpec, StoryFixture, mentioned_slugs, read_story


class FixtureIngester:
    """Finds the story through the chronicle's meta["fixture"], so it needs no arguments."""

    def __init__(self) -> None:
        self._stories: dict[tuple[Path, str], StoryFixture] = {}

    def ingest(self, chronicle: Chronicle, utterance: Utterance) -> IngestResult:
        story = self.story_of(chronicle)
        specs = [beat for beat in story.beats if beat.utterance_order == utterance.order]
        existing = set(chronicle.entities.values_list("slug", flat=True))
        return IngestResult(
            beats=tuple(ingested_beat(spec) for spec in specs),
            theories=tuple(
                IngestedTheory(schema=theory.schema, binding=theory.binding)
                for theory in story.theories
                if theory.utterance_order == utterance.order
            ),
            new_entities=tuple(new_entities(story, specs, existing)),
        )

    def story_of(self, chronicle: Chronicle) -> StoryFixture:
        slug = chronicle.meta.get("fixture")
        if not slug:
            raise ValueError(f"chronicle {chronicle.pk} was not built from a fixture story")
        key = (Path(settings.FIXTURE_STORIES_DIR), slug)
        if key not in self._stories:
            self._stories[key] = read_story(slug, stories_dir=key[0])
        return self._stories[key]


def ingested_beat(spec: BeatSpec) -> IngestedBeat:
    return IngestedBeat(
        pred=spec.pred,
        args=spec.args,
        present=tuple(spec.characters),
        players=None if spec.players is None else tuple(spec.players),
        source_kind=spec.source_kind,
        text=spec.text,
        tags=tuple(spec.tags),
        confidence=spec.confidence,
    )


def new_entities(story: StoryFixture, specs: list[BeatSpec], existing: set[str]) -> list[NewEntity]:
    entities = {entity.slug: entity for entity in story.entities}
    mentioned = [slug for spec in specs for slug in [*mentioned_slugs(spec.args), *spec.characters]]
    first_mentions = [slug for slug in dict.fromkeys(mentioned) if slug not in existing]
    return [
        NewEntity(
            slug=slug,
            kind=entities[slug].kind,
            name=entities[slug].name,
            aliases=tuple(entities[slug].aliases),
        )
        for slug in first_mentions
    ]
