import textwrap

import pytest

from chronicle.story_fixtures import StoryFixtureError, read_story

TRANSCRIPT = """
    title: Theories
    kind: session
    players: [Anna]
    utterances:
      - {order: 1, speaker: gm, text: "Mira trusts Aldric."}
      - {order: 2, speaker: Anna, text: "I bet Aldric betrays her."}
      - {order: 3, speaker: gm, text: "Aldric harms Mira."}
"""
ENTITIES = """
    mira: {kind: character, name: Mira}
    aldric: {kind: character, name: Aldric}
"""


def write_story(directory, beats):
    directory.mkdir()
    (directory / "transcript.yaml").write_text(textwrap.dedent(TRANSCRIPT))
    (directory / "entities.yaml").write_text(textwrap.dedent(ENTITIES))
    (directory / "beats.yaml").write_text(textwrap.dedent(beats))
    return directory


def test_theories_are_read_with_the_t_they_were_voiced_at(tmp_path):
    story = write_story(
        tmp_path / "theories",
        """
        - utterance: 1
          beats:
            - {pred: trusts, args: {who: "@mira", whom: "@aldric"}}
        - utterance: 2
          theories:
            - {schema: betrayal, binding: {T: aldric, V: mira}}
        - utterance: 3
          beats:
            - {pred: harms, args: {who: "@aldric", whom: "@mira"}}
        """,
    )

    [theory] = read_story("theories", stories_dir=story.parent).theories

    assert (theory.utterance_order, theory.schema, theory.binding, theory.voiced_at_t) == (
        2,
        "betrayal",
        {"T": "aldric", "V": "mira"},
        1,
    )


def test_theory_must_be_voiced_by_a_player(tmp_path):
    story = write_story(
        tmp_path / "gm_theory",
        """
        - utterance: 1
          beats:
            - {pred: trusts, args: {who: "@mira", whom: "@aldric"}}
          theories:
            - {schema: betrayal, binding: {T: aldric}}
        """,
    )

    with pytest.raises(StoryFixtureError, match=r"utterance 1.*theory.*player"):
        read_story("gm_theory", stories_dir=story.parent)


def test_theory_about_an_unknown_entity_is_rejected(tmp_path):
    story = write_story(
        tmp_path / "unknown",
        """
        - utterance: 1
          beats:
            - {pred: trusts, args: {who: "@mira", whom: "@aldric"}}
        - utterance: 2
          theories:
            - {schema: betrayal, binding: {T: ronan}}
        """,
    )

    with pytest.raises(StoryFixtureError, match=r"utterance 2.*unknown entity 'ronan'"):
        read_story("unknown", stories_dir=story.parent)
