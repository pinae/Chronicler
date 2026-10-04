from io import StringIO

import pytest
import yaml
from django.core.management import CommandError, call_command

from chronicle.importers.prose import ProseParagraph, parse_prose

GUTENBERG_SAMPLE = """\
The Project Gutenberg eBook of The Lantern Keeper

This ebook is for the use of anyone anywhere in the United States and
most other parts of the world at no cost and with almost no restrictions
whatsoever.

Title: The Lantern Keeper

Author: Nobody in Particular

Release date: January 1, 2026 [eBook #99999]

*** START OF THE PROJECT GUTENBERG EBOOK THE LANTERN KEEPER ***




                           THE LANTERN KEEPER

                                CONTENTS

 CHAPTER I. The Lamp

 CHAPTER II. The Storm


CHAPTER I.
The Lamp

Wena kept the lantern on the cliff,
as her mother had before her.

    She trusted the harbour master
    with the spare key.

[Illustration]

* * *

CHAPTER II.
The Storm

When the storm came, the lamp went dark.

*** END OF THE PROJECT GUTENBERG EBOOK THE LANTERN KEEPER ***

Updated editions will replace the previous one.
"""


def test_paragraphs_become_narrator_utterances_numbered_by_chapter():
    transcript = parse_prose(GUTENBERG_SAMPLE)

    assert transcript.paragraphs == [
        ProseParagraph(chapter=1, text="Wena kept the lantern on the cliff, as her mother had before her."),
        ProseParagraph(chapter=1, text="She trusted the harbour master with the spare key."),
        ProseParagraph(chapter=2, text="When the storm came, the lamp went dark."),
    ]


def test_the_title_and_ebook_number_come_from_the_gutenberg_header():
    transcript = parse_prose(GUTENBERG_SAMPLE)

    assert (transcript.title, transcript.gutenberg_ebook) == ("The Lantern Keeper", 99999)


def test_a_plain_text_without_chapters_is_one_chapter():
    transcript = parse_prose("The lamp was lit.\n\nThen it went out.\n")

    assert [(p.chapter, p.text) for p in transcript.paragraphs] == [
        (1, "The lamp was lit."),
        (1, "Then it went out."),
    ]
    assert (transcript.title, transcript.gutenberg_ebook) == (None, None)


def test_chapter_headings_may_use_arabic_numerals_and_mixed_case():
    transcript = parse_prose("Chapter 1\n\nFirst.\n\nChapter 2: Onwards\n\nSecond.\n")

    assert [(p.chapter, p.text) for p in transcript.paragraphs] == [(1, "First."), (2, "Second.")]


def import_prose(*arguments):
    output = StringIO()
    call_command("import_prose", *arguments, stdout=output)
    return output.getvalue()


def test_the_command_writes_a_transcript_and_a_readme_skeleton(tmp_path):
    book = tmp_path / "lantern.txt"
    book.write_text(GUTENBERG_SAMPLE)

    output = import_prose(str(book), "lantern", "--stories-dir", str(tmp_path))

    story_dir = tmp_path / "lantern"
    transcript = yaml.safe_load((story_dir / "transcript.yaml").read_text())
    assert (transcript["title"], transcript["kind"]) == ("The Lantern Keeper", "literature")
    assert transcript["utterances"][0] == {
        "order": 1,
        "speaker": "narrator",
        "text": "Wena kept the lantern on the cliff, as her mother had before her.",
        "source": {"chapter": 1},
    }
    readme = (story_dir / "README.md").read_text()
    assert "- **Kind:** literature" in readme
    assert "Project Gutenberg eBook #99999" in readme
    assert "- **License:** TODO" in readme
    assert "3 paragraphs in 2 chapters" in output


def test_the_command_takes_the_title_from_the_options_when_the_text_has_none(tmp_path):
    book = tmp_path / "plain.txt"
    book.write_text("The lamp was lit.\n")

    import_prose(str(book), "plain", "--stories-dir", str(tmp_path), "--title", "A Lamp")

    assert yaml.safe_load((tmp_path / "plain" / "transcript.yaml").read_text())["title"] == "A Lamp"


def test_the_command_does_not_overwrite_an_existing_story(tmp_path):
    book = tmp_path / "lantern.txt"
    book.write_text(GUTENBERG_SAMPLE)
    (tmp_path / "lantern").mkdir()
    (tmp_path / "lantern" / "transcript.yaml").write_text("keep me")

    with pytest.raises(
        CommandError, match="lantern already has a transcript.yaml; pass --force to replace it"
    ):
        import_prose(str(book), "lantern", "--stories-dir", str(tmp_path))

    import_prose(str(book), "lantern", "--stories-dir", str(tmp_path), "--force")
    assert "keep me" not in (tmp_path / "lantern" / "transcript.yaml").read_text()
