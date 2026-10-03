import textwrap

import pytest

from chronicle.models import Entity
from chronicle.story_fixtures import STORIES_DIR, StoryFixtureError, load_story

pytestmark = pytest.mark.django_db


def write_story(directory, **files):
    directory.mkdir()
    for name, content in files.items():
        (directory / name).write_text(textwrap.dedent(content))
    return directory


SESSION_TRANSCRIPT = """
    title: Test table
    kind: session
    players: [Anna, Ben]
    utterances:
      - {order: 1, speaker: gm, text: "Mira trusts Aldric."}
"""

TWO_CHARACTERS = """
    mira: {kind: character, name: Mira}
    aldric: {kind: character, name: Aldric, aliases: [the steward]}
"""


def test_minimal_story_loads_into_a_session_chronicle():
    chronicle = load_story("minimal")

    assert chronicle.kind == "session"
    assert sorted(player.name for player in chronicle.players.all()) == ["Anna", "Ben"]
    assert [beat.t for beat in chronicle.beats.all()] == [1, 2, 3, 4, 5]
    assert chronicle.utterances.count() == 3


def test_minimal_story_entities_keep_slugs_and_aliases():
    chronicle = load_story("minimal")

    aldric = chronicle.entities.get(slug="aldric")
    assert (aldric.canonical_name, aldric.kind, aldric.aliases) == ("Aldric", "character", ["the steward"])


def test_entities_are_introduced_at_their_first_mention():
    chronicle = load_story("minimal")

    assert chronicle.entities.get(slug="hall").introduced_at_t == 1
    assert chronicle.entities.get(slug="key").introduced_at_t == 3


def test_entity_references_become_entity_ids_and_beat_references_stay_ts():
    chronicle = load_story("minimal")
    mira, aldric, key = (chronicle.entities.get(slug=slug) for slug in ["mira", "aldric", "key"])

    gives = chronicle.beats.get(t=3)

    assert gives.pred == "gives"
    assert gives.args == {"who": {"entity": mira.id}, "what": {"entity": key.id}, "to": {"entity": aldric.id}}


def test_scope_follows_the_declared_presence():
    chronicle = load_story("minimal")
    anna, ben = chronicle.players.get(name="Anna"), chronicle.players.get(name="Ben")

    assert set(chronicle.visible_to(anna, 5).values_list("t", flat=True)) == {1, 2, 3}
    assert set(chronicle.visible_to(ben, 5).values_list("t", flat=True)) == {1, 2, 3, 4}
    assert sorted(e.slug for e in chronicle.beats.get(t=5).known_by_chars_at(5)) == ["aldric"]


def test_player_speaks_their_utterances():
    chronicle = load_story("minimal")

    assert str(chronicle.utterances.get(order=2).speaker_player) == "Anna"
    assert chronicle.utterances.get(order=1).speaker_player is None


def test_every_fixture_story_has_a_readme_with_provenance_license_and_kind():
    for story in [path for path in STORIES_DIR.iterdir() if path.is_dir()]:
        readme = (story / "README.md").read_text().lower()

        assert "provenance" in readme, story.name
        assert "license" in readme, story.name
        assert "kind" in readme, story.name


def test_unknown_entity_is_reported_with_file_and_beat(tmp_path):
    story = write_story(
        tmp_path / "broken",
        **{
            "transcript.yaml": SESSION_TRANSCRIPT,
            "entities.yaml": TWO_CHARACTERS,
            "beats.yaml": """
                - utterance: 1
                  beats:
                    - {pred: trusts, args: {who: "@mira", whom: "@aldric"}}
                    - {pred: trusts, args: {who: "@mira", whom: "@ronan"}}
            """,
        },
    )

    with pytest.raises(StoryFixtureError, match=r"beats\.yaml.*utterance 1, beat 2.*ronan"):
        load_story("broken", stories_dir=story.parent)


def test_entity_that_is_never_mentioned_is_reported(tmp_path):
    story = write_story(
        tmp_path / "unused",
        **{
            "transcript.yaml": SESSION_TRANSCRIPT,
            "entities.yaml": TWO_CHARACTERS + "    ronan: {kind: character, name: Ronan}\n",
            "beats.yaml": """
                - utterance: 1
                  beats:
                    - {pred: trusts, args: {who: "@mira", whom: "@aldric"}}
            """,
        },
    )

    with pytest.raises(StoryFixtureError, match=r"entities\.yaml.*ronan.*never"):
        load_story("unused", stories_dir=story.parent)


def test_declared_t_must_match_the_position_of_the_beat(tmp_path):
    story = write_story(
        tmp_path / "miscounted",
        **{
            "transcript.yaml": SESSION_TRANSCRIPT,
            "entities.yaml": TWO_CHARACTERS,
            "beats.yaml": """
                - utterance: 1
                  beats:
                    - {t: 1, pred: trusts, args: {who: "@mira", whom: "@aldric"}}
                    - {t: 3, pred: trusts, args: {who: "@aldric", whom: "@mira"}}
            """,
        },
    )

    with pytest.raises(StoryFixtureError, match=r"utterance 1, beat 2.*t=2"):
        load_story("miscounted", stories_dir=story.parent)


def test_literature_story_is_read_by_the_implicit_reader(tmp_path):
    story = write_story(
        tmp_path / "novel",
        **{
            "transcript.yaml": """
                title: A short novel
                kind: literature
                utterances:
                  - {order: 1, speaker: narrator, text: "Mira trusted Aldric.", source: {chapter: 1}}
            """,
            "entities.yaml": TWO_CHARACTERS,
            "beats.yaml": """
                - utterance: 1
                  beats:
                    - {pred: trusts, args: {who: "@mira", whom: "@aldric"}, text: Mira trusts Aldric.}
            """,
        },
    )

    chronicle = load_story("novel", stories_dir=story.parent)

    reader = chronicle.players.get()
    assert [beat.text for beat in chronicle.visible_to(reader, 1)] == ["Mira trusts Aldric."]
    assert chronicle.utterances.get().source == {"chapter": 1}


def test_media_utterances_are_spoken_by_their_outlet(tmp_path):
    story = write_story(
        tmp_path / "news",
        **{
            "transcript.yaml": """
                title: Minister resigns
                kind: media
                utterances:
                  - order: 1
                    speaker: herald
                    text: "The minister resigned, the Herald reports."
                    source: {outlet: The Herald, published_at: "2026-05-01"}
            """,
            "entities.yaml": """
                herald: {kind: source, name: The Herald}
                minister: {kind: character, name: The minister}
            """,
            "beats.yaml": """
                - utterance: 1
                  beats:
                    - pred: says
                      kind: claim
                      args:
                        who: "@herald"
                        what: {pred: breaks, args: {who: "@minister", whom: "@minister", what: office}}
            """,
        },
    )

    chronicle = load_story("news", stories_dir=story.parent)

    herald = chronicle.entities.get(slug="herald")
    minister = chronicle.entities.get(slug="minister")
    claim = chronicle.beats.get()
    assert chronicle.utterances.get().speaker_entity == herald
    assert claim.source_kind == "claim"
    assert claim.args["what"] == {
        "prop": {
            "pred": "breaks",
            "args": {
                "who": {"entity": minister.id},
                "whom": {"entity": minister.id},
                "what": {"literal": "office"},
            },
        }
    }


def test_entity_slugs_are_unique_within_a_chronicle(chronicle):
    Entity.objects.create(
        chronicle=chronicle, kind="character", canonical_name="Aldric", slug="aldric", introduced_at_t=1
    )

    with pytest.raises(Exception, match="UNIQUE|unique"):
        Entity.objects.create(
            chronicle=chronicle,
            kind="character",
            canonical_name="Aldric II",
            slug="aldric",
            introduced_at_t=1,
        )


def test_story_can_be_loaded_up_to_a_given_t():
    chronicle = load_story("minimal", until_t=3)

    assert [beat.t for beat in chronicle.beats.all()] == [1, 2, 3]
