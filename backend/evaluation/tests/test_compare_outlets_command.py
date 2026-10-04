import re
from io import StringIO

import pytest
from django.core.management import CommandError, call_command

from chronicle.fact_labels import FactLabelRow, import_fact_labels
from evaluation.replay import replay_story

pytestmark = pytest.mark.django_db


@pytest.fixture
def outlets():
    courier = replay_story("harbour-fire", reader=None)
    herald = replay_story("harbour-fire-herald", reader=None)
    import_fact_labels(
        courier,
        [
            FactLabelRow(line=2, t=1, verdict="unverified", labeler="FactDesk"),
            FactLabelRow(line=3, t=4, verdict="false", labeler="FactDesk"),
        ],
    )
    return courier, herald


def compare(*chronicles):
    output = StringIO()
    call_command("compare_outlets", *(str(chronicle.pk) for chronicle in chronicles), stdout=output)
    return output.getvalue()


def row(report, start):
    return next(line for line in report.splitlines() if line.startswith(start))


def test_the_comparison_shows_per_outlet_completion_and_the_weight_on_doubted_claims(outlets):
    report = compare(*outlets)

    assert "The engine measures how strongly each outlet's coverage instantiates a narrative" in report
    assert re.fullmatch(
        r"The Harbour Fire \(The Courier\)\s+100% \(3 of 3\)\s+43%",
        row(report, "The Harbour Fire (The Courier)"),
    )
    assert re.fullmatch(
        r"The Harbour Fire \(Harbour Herald\)\s+33% \(1 of 3\)\s+0%",
        row(report, "The Harbour Fire (Harbour Herald)"),
    )


def test_the_comparison_shows_how_much_the_outlets_agree(outlets):
    report = compare(*outlets)

    assert row(report, "Overlap of filled steps") == (
        "Overlap of filled steps, The Harbour Fire (The Courier) and The Harbour Fire (Harbour Herald): "
        "25% (1 of 4)"
    )


def test_the_comparison_needs_two_chronicles(outlets):
    with pytest.raises(CommandError, match="compare at least two chronicles"):
        compare(outlets[0])
