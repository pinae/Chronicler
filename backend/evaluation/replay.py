"""Replaying a fixture story through the whole pipeline and exporting a run file (concept §9.3).

The run file holds the lattice and the expectations at every t. It is built after the run from the
stored, time-indexed data (`Lattice.at`), which is exactly what the replay guarantee promises.
Format: docs/run-file-format.md.
"""

import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from django.conf import settings

from chronicle.ingest.fixture import FixtureIngester
from chronicle.ingest.interfaces import NewEntity
from chronicle.models import Chronicle, Entity, Player, Utterance
from chronicle.story_fixtures import SPEAKERS_WITHOUT_IDENTITY, StoryFixture, UtteranceSpec, read_story
from matching.lattice import Lattice, LatticeHypothesis
from matching.models import Expectation
from matching.store import matcher_config_from_settings
from narrative_engine.pipeline import Pipeline, create_entity
from reader.context import ContextBuilder, RecentAndSupportingBeats
from reader.interfaces import ReaderModel
from schemas.library import load_library

RUN_FORMAT = "chronicler-run/1"
ALL_BEATS = "all"


def replay_story(
    slug: str,
    reader: ReaderModel | None,
    context_builder: ContextBuilder | None = None,
    until_t: int | None = None,
    stories_dir: Path | None = None,
    per_player: bool = False,
) -> Chronicle:
    """Run a fixture story through the pipeline, one utterance at a time, into a fresh chronicle.
    With `per_player`, every player of a session also gets a lattice (and readouts) of their own."""
    load_library()
    story = read_story(slug, stories_dir or settings.FIXTURE_STORIES_DIR)
    chronicle = Chronicle.objects.create(kind=story.kind, title=story.title, meta={"fixture": slug})
    players = [Player.objects.create(chronicle=chronicle, name=name) for name in story.players]
    audiences: list[Player | None] = [None, *(players if per_player else [])]
    pipeline = Pipeline(
        chronicle, FixtureIngester(), reader, context_builder or RecentAndSupportingBeats(), audiences
    )
    for spec in story.utterances:
        if until_t is not None and chronicle.beats.count() >= until_t:
            break
        pipeline.process(create_utterance(chronicle, story, spec))
    return chronicle


def create_utterance(chronicle: Chronicle, story: StoryFixture, spec: UtteranceSpec) -> Utterance:
    speaker_player = chronicle.players.filter(name=spec.speaker, implicit=False).first()
    speaker_entity = None
    if speaker_player is None and spec.speaker not in SPEAKERS_WITHOUT_IDENTITY:
        speaker_entity = speaker_entity_for(chronicle, story, spec.speaker)
    return Utterance.objects.create(
        chronicle=chronicle,
        order=spec.order,
        speaker_player=speaker_player,
        speaker_entity=speaker_entity,
        text=spec.text,
        source=spec.source,
    )


def speaker_entity_for(chronicle: Chronicle, story: StoryFixture, slug: str) -> Entity:
    """A media outlet speaks before any beat mentions it; it is introduced with the next beat."""
    existing = chronicle.entities.filter(slug=slug).first()
    if existing is not None:
        return existing
    spec = next(entity for entity in story.entities if entity.slug == slug)
    outlet = NewEntity(slug=spec.slug, kind=spec.kind, name=spec.name, aliases=tuple(spec.aliases))
    return create_entity(chronicle, outlet, chronicle.beats.count() + 1)


def build_run(
    chronicle: Chronicle,
    story: str,
    audiences: Sequence[Player | None] = (None,),
    reader: str | None = None,
    truth: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """The run file (docs/run-file-format.md). `truth` is what the reader made of the story's
    ground truth (evaluation/truth_readouts.py), if it was asked."""
    last_t = chronicle.beats.count()
    expectations = Expectation.objects.filter(hypothesis__chronicle=chronicle).select_related("step")
    llm_calls = {e.llm_call_id for e in expectations if e.llm_call_id is not None}
    if truth is not None:
        llm_calls |= {belief["llm_call"] for belief in truth["beliefs"] if belief["llm_call"] is not None}
    run = {
        "format": RUN_FORMAT,
        "story": story,
        "chronicle": chronicle.pk,
        "created_at": datetime.now(UTC).isoformat(),
        "reader": reader,
        "matcher": vars(matcher_config_from_settings()),
        "players": {str(player.pk): player.name for player in chronicle.players.all()},
        "entities": {
            str(entity.pk): {"slug": entity.slug, "name": entity.canonical_name, "kind": entity.kind}
            for entity in chronicle.entities.all()
        },
        "beats": [
            {
                "t": beat.t,
                "pred": beat.pred,
                "original_pred": beat.original_pred,
                "text": beat.text,
                "quarantined": beat.is_quarantined,
            }
            for beat in chronicle.beats.all()
        ],
        "timeline": [
            {
                "t": t,
                "lattice": {
                    audience_key(audience): [
                        lattice_entry(h) for h in Lattice.at(chronicle, t, audience).hypotheses
                    ]
                    for audience in audiences
                },
                "expectations": [expectation_entry(e) for e in expectations if e.computed_at_t == t],
            }
            for t in range(last_t + 1)
        ],
        "llm_calls": sorted(llm_calls),
    }
    if truth is not None:
        run["truth"] = dict(truth)
    return run


def audience_key(audience: Player | None) -> str:
    return ALL_BEATS if audience is None else audience.name


def lattice_entry(hypothesis: LatticeHypothesis) -> dict[str, Any]:
    return {
        "id": hypothesis.id,
        "schema": hypothesis.schema,
        "binding": dict(hypothesis.binding),
        "status": hypothesis.status,
        "weight": hypothesis.weight,
        "created_at_t": hypothesis.created_at_t,
        "status_changed_at_t": hypothesis.status_changed_at_t,
        "fills": [[fill.step_id, fill.beat_t] for fill in hypothesis.fills],
        "refines": hypothesis.refines_id,
        "merged_into": hypothesis.merged_into_id,
        "refuted_by_t": hypothesis.refuted_by_t,
        "voiced_by": hypothesis.voiced_by,
        "voiced_in": hypothesis.voiced_in,
        "voiced_at_t": hypothesis.voiced_at_t,
    }


def expectation_entry(expectation: Expectation) -> dict[str, Any]:
    return {
        "hypothesis": expectation.hypothesis_id,
        "step": expectation.step.step_id,
        "for_player": expectation.for_player_id,
        "question": expectation.question,
        "candidates": expectation.candidates,
        "outside_mass": expectation.outside_mass,
        "llm_call": expectation.llm_call_id,
    }


def write_run(run: dict[str, Any], directory: Path) -> Path:
    story_dir = directory / run["story"]
    story_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    path = story_dir / f"{timestamp}.json"
    path.write_text(json.dumps(run, indent=1, ensure_ascii=False))
    return path
