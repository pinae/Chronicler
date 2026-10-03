import textwrap

import pytest

from chronicle.ingest.fixture import FixtureIngester
from chronicle.ingest.interfaces import IngestedBeat, IngestedTheory
from chronicle.models import Chronicle, Entity, Utterance
from narrative_engine import di

pytestmark = pytest.mark.django_db


def chronicle_of(slug, kind="session"):
    return Chronicle.objects.create(kind=kind, title=slug, meta={"fixture": slug})


def utterance(chronicle, order):
    return Utterance.objects.create(chronicle=chronicle, order=order, text="…")


def test_fixture_ingester_yields_the_fixture_beats_of_the_utterance_in_order():
    chronicle = chronicle_of("minimal")

    result = FixtureIngester().ingest(chronicle, utterance(chronicle, 1))

    assert [beat.pred for beat in result.beats] == ["is_at", "trusts", "gives"]
    assert result.beats[2] == IngestedBeat(
        pred="gives",
        args={"who": "@mira", "what": "@key", "to": "@aldric"},
        present=("mira", "aldric"),
        players=None,
        source_kind="action",
        text="Mira gives Aldric the cellar key.",
    )


def test_utterance_without_beats_yields_none():
    chronicle = chronicle_of("minimal")

    assert FixtureIngester().ingest(chronicle, utterance(chronicle, 2)).beats == ()


def test_entities_mentioned_for_the_first_time_are_reported_as_new_in_order_of_mention():
    chronicle = chronicle_of("minimal")

    result = FixtureIngester().ingest(chronicle, utterance(chronicle, 1))

    assert [entity.slug for entity in result.new_entities] == ["aldric", "hall", "mira", "key"]


def test_entities_the_chronicle_already_has_are_not_new():
    chronicle = chronicle_of("minimal")
    Entity.objects.create(
        chronicle=chronicle, slug="aldric", kind="character", canonical_name="Aldric", introduced_at_t=1
    )

    result = FixtureIngester().ingest(chronicle, utterance(chronicle, 1))

    assert "aldric" not in [entity.slug for entity in result.new_entities]


def test_theories_voiced_in_the_utterance_are_reported():
    chronicle = chronicle_of("steward")

    result = FixtureIngester().ingest(chronicle, utterance(chronicle, 3))

    assert result.theories == (IngestedTheory(schema="betrayal", binding={"T": "aldric"}),)


@pytest.mark.parametrize(
    ("kind", "speaker"),
    [("literature", "narrator"), ("media", "herald")],
)
def test_prose_and_articles_are_ingested_like_table_talk(tmp_path, settings, kind, speaker):
    story = tmp_path / "other_kinds"
    story.mkdir()
    (story / "transcript.yaml").write_text(
        textwrap.dedent(
            f"""
            title: Other kinds
            kind: {kind}
            utterances:
              - {{order: 1, speaker: {speaker}, text: "The minister resigned."}}
            """
        )
    )
    (story / "entities.yaml").write_text(
        "herald: {kind: source, name: The Herald}\nminister: {kind: character, name: The minister}\n"
    )
    (story / "beats.yaml").write_text(
        textwrap.dedent(
            """
            - utterance: 1
              beats:
                - pred: says
                  kind: claim
                  args: {who: "@herald", what: {pred: is, args: {who: "@minister", trait: gone}}}
            """
        )
    )
    settings.FIXTURE_STORIES_DIR = tmp_path
    chronicle = chronicle_of("other_kinds", kind=kind)

    [beat] = FixtureIngester().ingest(chronicle, utterance(chronicle, 1)).beats

    assert (beat.pred, beat.source_kind) == ("says", "claim")


def test_chronicle_that_was_not_built_from_a_fixture_cannot_be_fixture_ingested():
    chronicle = Chronicle.objects.create(kind="session", title="Live table")

    with pytest.raises(ValueError, match="fixture"):
        FixtureIngester().ingest(chronicle, utterance(chronicle, 1))


def test_test_settings_bind_the_ingester_to_the_fixture_ingester():
    assert isinstance(di.make("Ingester"), FixtureIngester)
