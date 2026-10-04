from io import StringIO

import pytest
import yaml
from django.core.management import CommandError, call_command

from chronicle.importers.session import SessionTurn, TranscriptFormatError, parse_session

SESSION_SAMPLE = """\
[00:00:05] GM: Lady Mira holds court in the great hall of Wend.
She trusts her steward Aldric with everything.
[00:00:21] Anna: I bet the steward is up to something.

[00:00:30] Ben: I keep an eye on Aldric.
[00:00:42] GM: You see him watching Mira as she leaves the cellar.
Anna: Told you.
"""

MIRAS_COURT = (
    "Lady Mira holds court in the great hall of Wend. She trusts her steward Aldric with everything."
)


def test_each_turn_becomes_one_utterance_with_its_continuation_lines():
    session = parse_session(SESSION_SAMPLE, gm_names={"GM"})

    assert session.turns == [
        SessionTurn(
            speaker=None,
            text=MIRAS_COURT,
            line=1,
        ),
        SessionTurn(speaker="Anna", text="I bet the steward is up to something.", line=3),
        SessionTurn(speaker="Ben", text="I keep an eye on Aldric.", line=5),
        SessionTurn(speaker=None, text="You see him watching Mira as she leaves the cellar.", line=6),
        SessionTurn(speaker="Anna", text="Told you.", line=7),
    ]


def test_players_are_the_speakers_who_are_not_the_gm_in_order_of_appearance():
    session = parse_session(SESSION_SAMPLE, gm_names={"GM"})

    assert session.players == ["Anna", "Ben"]


def test_the_gm_may_go_by_other_names():
    session = parse_session("DM: The door creaks.\nAnna: I open it.\n", gm_names={"DM", "Narrator"})

    assert [turn.speaker for turn in session.turns] == [None, "Anna"]


def test_text_before_the_first_speaker_is_rejected():
    with pytest.raises(TranscriptFormatError, match="line 1: expected 'Speaker: text'"):
        parse_session("The session begins.\nGM: Welcome.\n", gm_names={"GM"})


def import_session(*arguments):
    output = StringIO()
    call_command("import_session", *arguments, stdout=output)
    return output.getvalue()


def test_the_command_writes_a_session_transcript_and_a_readme_skeleton(tmp_path):
    recording = tmp_path / "session.txt"
    recording.write_text(SESSION_SAMPLE)

    output = import_session(
        str(recording), "wend", "--title", "The Court of Wend", "--stories-dir", str(tmp_path)
    )

    transcript = yaml.safe_load((tmp_path / "wend" / "transcript.yaml").read_text())
    assert (transcript["title"], transcript["kind"], transcript["players"]) == (
        "The Court of Wend",
        "session",
        ["Anna", "Ben"],
    )
    assert transcript["utterances"][:2] == [
        {
            "order": 1,
            "speaker": "gm",
            "text": MIRAS_COURT,
            "source": {"line": 1},
        },
        {
            "order": 2,
            "speaker": "Anna",
            "text": "I bet the steward is up to something.",
            "source": {"line": 3},
        },
    ]
    assert "- **Kind:** session" in (tmp_path / "wend" / "README.md").read_text()
    assert "5 turns by the GM and 2 players (Anna, Ben)" in output


def test_the_command_takes_gm_names_from_the_options(tmp_path):
    recording = tmp_path / "session.txt"
    recording.write_text("DM: The door creaks.\nAnna: I open it.\n")

    import_session(str(recording), "door", "--title", "Door", "--gm", "DM", "--stories-dir", str(tmp_path))

    transcript = yaml.safe_load((tmp_path / "door" / "transcript.yaml").read_text())
    assert transcript["players"] == ["Anna"]
    assert transcript["utterances"][0]["speaker"] == "gm"


def test_the_command_reports_a_malformed_transcript(tmp_path):
    recording = tmp_path / "session.txt"
    recording.write_text("The session begins.\n")

    with pytest.raises(CommandError, match="line 1: expected 'Speaker: text'"):
        import_session(str(recording), "broken", "--title", "Broken", "--stories-dir", str(tmp_path))
