import shutil
from dataclasses import replace
from io import StringIO

import pytest
import yaml
from django.core.management import CommandError, call_command

from chronicle.ingest.interfaces import IngestedBeat, IngestResult, NewEntity
from chronicle.models import Chronicle
from chronicle.story_fixtures import StoryFixtureError, read_story

pytestmark = pytest.mark.django_db

LANTERN = {
    "title": "The Lantern",
    "kind": "literature",
    "utterances": [
        {"order": 1, "speaker": "narrator", "text": "Wena trusted the harbour master."},
        {"order": 2, "speaker": "narrator", "text": "She adored the sea."},
    ],
}
WENA = NewEntity(slug="wena", kind="character", name="Wena", aliases=("the keeper",))
MASTER = NewEntity(slug="master", kind="character", name="The harbour master")


class ScriptedIngester:
    """Answers each utterance (by order) with the result in `script`."""

    script: dict[int, IngestResult] = {}

    def ingest(self, chronicle, utterance):
        return self.script.get(utterance.order, IngestResult())


@pytest.fixture
def lantern(tmp_path, settings):
    """A story with nothing but a transcript, drafted by the scripted ingester."""
    (tmp_path / "lantern").mkdir()
    (tmp_path / "lantern" / "transcript.yaml").write_text(yaml.safe_dump(LANTERN))
    settings.INJECTED = {**settings.INJECTED, "Ingester": f"{__name__}.ScriptedIngester"}
    return tmp_path


def draft(story, stories_dir, *options):
    output = StringIO()
    call_command("draft_beats", story, "--stories-dir", str(stories_dir), *options, stdout=output)
    return output.getvalue()


def drafted(stories_dir, story="lantern"):
    beats = yaml.safe_load((stories_dir / story / "beats.yaml").read_text())
    entities = yaml.safe_load((stories_dir / story / "entities.yaml").read_text())
    return beats, entities


def test_drafting_with_the_fixture_ingester_reproduces_a_story(tmp_path, settings):
    shutil.copytree(settings.FIXTURE_STORIES_DIR / "steward", tmp_path / "steward")
    settings.FIXTURE_STORIES_DIR = tmp_path
    original = read_story("steward", tmp_path)

    draft("steward", tmp_path, "--force")

    redrafted = read_story("steward", tmp_path)
    assert [replace(beat, declared_t=None) for beat in redrafted.beats] == [
        replace(beat, declared_t=None) for beat in original.beats
    ]
    assert sorted(redrafted.entities, key=lambda e: e.slug) == sorted(original.entities, key=lambda e: e.slug)
    assert redrafted.theories == original.theories


def test_drafted_beats_and_entities_are_written_with_their_confidence(lantern):
    ScriptedIngester.script = {
        1: IngestResult(
            beats=(
                IngestedBeat(
                    pred="trusts",
                    args={"who": "@wena", "whom": "@master"},
                    present=("wena",),
                    text="Wena trusts the harbour master.",
                    confidence=0.8,
                ),
            ),
            new_entities=(WENA, MASTER),
        )
    }

    output = draft("lantern", lantern)

    beats, entities = drafted(lantern)
    assert beats == [
        {
            "utterance": 1,
            "beats": [
                {
                    "pred": "trusts",
                    "args": {"who": "@wena", "whom": "@master"},
                    "present": ["wena"],
                    "text": "Wena trusts the harbour master.",
                    "confidence": 0.8,
                }
            ],
        }
    ]
    assert entities == {
        "wena": {"kind": "character", "name": "Wena", "aliases": ["the keeper"]},
        "master": {"kind": "character", "name": "The harbour master"},
    }
    assert "Drafted 1 beat and 2 entities from 2 utterances; 0 marked for review" in output


def test_a_beat_with_a_predicate_outside_the_vocabulary_is_marked_for_review(lantern):
    ScriptedIngester.script = {
        2: IngestResult(beats=(IngestedBeat(pred="adores", args={"who": "@wena"}),), new_entities=(WENA,))
    }

    output = draft("lantern", lantern)

    [entry] = drafted(lantern)[0]
    assert entry["beats"][0]["review"] == (
        "unknown predicate 'adores': map it onto the vocabulary, or remove this mark to keep it quarantined"
    )
    assert "1 marked for review" in output


def test_problems_the_ingester_reports_are_marked_for_review_on_their_utterance(lantern):
    ScriptedIngester.script = {1: IngestResult(problems=("dropped a beat: 'who' was missing",))}

    draft("lantern", lantern)

    assert drafted(lantern)[0] == [{"utterance": 1, "review": ["dropped a beat: 'who' was missing"]}]


def test_an_utterance_whose_beats_cannot_be_appended_is_marked_for_review_without_beats(lantern):
    ScriptedIngester.script = {
        1: IngestResult(beats=(IngestedBeat(pred="trusts", args={"who": "@nobody", "whom": "@nobody"}),)),
        2: IngestResult(
            beats=(IngestedBeat(pred="is", args={"who": "@wena", "trait": "calm"}),), new_entities=(WENA,)
        ),
    }

    draft("lantern", lantern)

    beats, entities = drafted(lantern)
    assert beats[0] == {"utterance": 1, "review": ["utterance 1: unknown entity 'nobody'"]}
    assert beats[1]["beats"][0]["pred"] == "is"
    assert list(entities) == ["wena"]


def test_a_draft_marked_for_review_cannot_be_loaded_as_a_story(lantern):
    ScriptedIngester.script = {
        1: IngestResult(
            beats=(IngestedBeat(pred="adores", args={"who": "@wena"}),),
            new_entities=(WENA,),
        )
    }
    draft("lantern", lantern)

    with pytest.raises(StoryFixtureError, match="utterance 1, beat 1: still marked for review"):
        read_story("lantern", lantern)


def test_drafting_does_not_overwrite_reviewed_beats(lantern):
    (lantern / "lantern" / "beats.yaml").write_text("[]")

    with pytest.raises(CommandError, match="lantern already has a beats.yaml; pass --force to replace it"):
        draft("lantern", lantern)


def test_drafting_keeps_nothing_in_the_database(lantern):
    ScriptedIngester.script = {1: IngestResult(new_entities=(WENA,))}

    draft("lantern", lantern)

    assert Chronicle.objects.count() == 0


def test_entities_declared_before_drafting_are_known_to_the_ingester_and_kept(lantern):
    (lantern / "lantern" / "entities.yaml").write_text(
        yaml.safe_dump({"wena": {"kind": "character", "name": "Wena"}})
    )
    ScriptedIngester.script = {
        1: IngestResult(
            beats=(IngestedBeat(pred="trusts", args={"who": "@wena", "whom": "@master"}),),
            new_entities=(MASTER,),
        )
    }

    draft("lantern", lantern)

    beats, entities = drafted(lantern)
    assert beats[0]["beats"][0]["args"] == {"who": "@wena", "whom": "@master"}
    assert entities == {
        "wena": {"kind": "character", "name": "Wena"},
        "master": {"kind": "character", "name": "The harbour master"},
    }


class OutletIngester:
    """States what the speaking outlet claims, as the ingester does for media utterances."""

    def ingest(self, chronicle, utterance):
        outlet = utterance.speaker_entity
        claim = {
            "who": f"@{outlet.slug}",
            "what": {"pred": "is", "args": {"who": f"@{outlet.slug}", "trait": "first"}},
        }
        return IngestResult(beats=(IngestedBeat(pred="says", args=claim, source_kind="claim"),))


def test_a_media_outlet_declared_as_an_entity_speaks_its_passages(tmp_path, settings):
    (tmp_path / "fire").mkdir()
    (tmp_path / "fire" / "transcript.yaml").write_text(
        yaml.safe_dump(
            {
                "title": "Fire",
                "kind": "media",
                "utterances": [{"order": 1, "speaker": "courier", "text": "We were first."}],
            }
        )
    )
    (tmp_path / "fire" / "entities.yaml").write_text(
        yaml.safe_dump({"courier": {"kind": "source", "name": "The Courier"}})
    )
    settings.INJECTED = {**settings.INJECTED, "Ingester": f"{__name__}.OutletIngester"}

    draft("fire", tmp_path)

    [entry] = drafted(tmp_path, "fire")[0]
    assert entry["beats"][0]["args"]["who"] == "@courier"
    assert entry["beats"][0]["kind"] == "claim"
