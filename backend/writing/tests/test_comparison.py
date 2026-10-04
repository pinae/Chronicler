import json
import re
from io import StringIO

import pytest
from django.core.management import call_command

from chronicle.ingest.interfaces import IngestedBeat, IngestResult
from evaluation.ground_truth import TrueHypothesis
from writing.comparison import PROSE_ONLY, WITH_STRUCTURE, compare_writers, export_for_raters
from writing.fixture import FixtureStoryWriter
from writing.interfaces import Continuation

pytestmark = pytest.mark.django_db

BRAM_BETRAYS_OSKAR = TrueHypothesis(schema="betrayal", binding={"T": "bram", "V": "oskar"})
STRUCTURED = [
    Continuation(
        prose="Bram watched Oskar hide the key again.",
        intended=IngestedBeat(
            pred="learns",
            args={"who": "@bram", "what": {"pred": "hides", "args": {"who": "@oskar", "what": "@key"}}},
            present=("bram",),
        ),
    ),
    Continuation(
        prose="Bram took the key from Oskar's boathouse.",
        intended=IngestedBeat(
            pred="steals", args={"who": "@bram", "what": "@key", "from": "@oskar"}, present=("bram",)
        ),
    ),
]
PROSE_ONLY_SCRIPT = [
    Continuation(prose="The harbour fell silent."),
    Continuation(prose="Rain fell on the boats."),
]


class EchoIngester:
    """Reads back the beats the structured writer intended; plain prose conveys nothing here."""

    def ingest(self, chronicle, utterance):
        intended = next((c.intended for c in STRUCTURED if c.prose == utterance.text), None)
        return IngestResult(beats=(intended,) if intended else ())


class StructuredWriter(FixtureStoryWriter):
    def __init__(self):
        super().__init__(STRUCTURED)


class ProseWriter(FixtureStoryWriter):
    def __init__(self):
        super().__init__(PROSE_ONLY_SCRIPT)


def compare():
    return compare_writers(
        "ferryman",
        BRAM_BETRAYS_OSKAR,
        2,
        writers={WITH_STRUCTURE: StructuredWriter(), PROSE_ONLY: ProseWriter()},
        ingester=EchoIngester(),
        reader=None,
    )


def test_both_variants_continue_the_same_seed_toward_the_same_target():
    with_structure, prose_only = compare()

    assert (with_structure.condition, prose_only.condition) == (WITH_STRUCTURE, PROSE_ONLY)
    seed_texts = [
        list(v.chronicle.utterances.order_by("order").values_list("text", flat=True))[:16]
        for v in (with_structure, prose_only)
    ]
    assert seed_texts[0] == seed_texts[1]
    assert with_structure.texts[-2:] == [c.prose for c in STRUCTURED]
    assert prose_only.texts[-2:] == [c.prose for c in PROSE_ONLY_SCRIPT]


def test_each_variant_is_measured_against_the_target():
    with_structure, prose_only = compare()

    assert dict(with_structure.metrics)["twist recall at reveal - 1"] == "yes"
    assert dict(prose_only.metrics)["twist recall at reveal - 1"] == "n/a"  # its prose added no beats


def test_the_rater_export_lists_the_stories_under_random_ids_without_their_condition(tmp_path):
    variants = compare()

    export_for_raters(variants, tmp_path)

    stories = sorted((tmp_path / "for-raters").glob("*.md"))
    assert len(stories) == 2
    assert all(re.fullmatch(r"[0-9a-f]{8}\.md", story.name) for story in stories)
    texts = [story.read_text() for story in stories]
    assert any("Bram took the key from Oskar's boathouse." in text for text in texts)
    assert any("Rain fell on the boats." in text for text in texts)
    for text in texts:
        for giveaway in ["structure", "prose-only", "prose only", "Writer", "generated"]:
            assert giveaway not in text
    key = json.loads((tmp_path / "condition-key.json").read_text())
    assert key == {
        story.stem: (WITH_STRUCTURE if "Bram took the key" in story.read_text() else PROSE_ONLY)
        for story in stories
    }


def test_the_compare_command_prints_both_variants_side_by_side_and_exports_them(settings, tmp_path):
    settings.INJECTED = {
        **settings.INJECTED,
        "StoryWriter": f"{__name__}.StructuredWriter",
        "ProseOnlyStoryWriter": f"{__name__}.ProseWriter",
        "Ingester": f"{__name__}.EchoIngester",
    }
    output = StringIO()

    call_command(
        "compare",
        "ferryman",
        "--target",
        "betrayal T=bram V=oskar",
        "--beats",
        "2",
        "--reader",
        "none",
        "--output-dir",
        str(tmp_path / "runs"),
        "--export-dir",
        str(tmp_path / "export"),
        stdout=output,
    )

    lines = output.getvalue().splitlines()
    assert any(re.match(r"^Metric\s+with structure\s+prose only$", line) for line in lines)
    assert any(re.match(r"^twist recall at reveal - 1\s+yes\s+n/a$", line) for line in lines)
    assert len(list((tmp_path / "export" / "for-raters").glob("*.md"))) == 2
    assert {path.name for path in (tmp_path / "runs").iterdir()} == {
        "ferryman-with-structure",
        "ferryman-prose-only",
    }
