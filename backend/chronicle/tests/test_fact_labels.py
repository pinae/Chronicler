from io import StringIO

import pytest
from django.core.exceptions import ValidationError
from django.core.management import CommandError, call_command

from chronicle.fact_labels import FactLabelRow, import_fact_labels
from chronicle.models import FactLabel

pytestmark = pytest.mark.django_db


@pytest.fixture
def harbour_fire(load_story):
    return load_story("harbour-fire")


def test_a_fact_label_gives_a_beat_an_external_verdict(harbour_fire):
    accusation = harbour_fire.beats.get(t=1)

    label = FactLabel.objects.create(
        beat=accusation, verdict="unverified", labeler="FactDesk", note="No witness named."
    )

    assert list(accusation.fact_labels.all()) == [label]
    with pytest.raises(ValidationError):
        FactLabel(beat=accusation, verdict="probably", labeler="FactDesk").full_clean()


def test_rows_are_attached_to_the_beats_they_name(harbour_fire):
    rows = [
        FactLabelRow(line=2, t=1, verdict="unverified", labeler="FactDesk", note="No witness named."),
        FactLabelRow(line=3, t=4, verdict="false", labeler="FactDesk", note="Holt sold his land claim."),
    ]

    result = import_fact_labels(harbour_fire, rows)

    assert (result.imported, result.problems) == (2, [])
    assert harbour_fire.beats.get(t=4).fact_labels.get().verdict == "false"


def test_rows_naming_unknown_beats_or_verdicts_are_reported_and_the_rest_imported(harbour_fire):
    rows = [
        FactLabelRow(line=2, t=1, verdict="unverified", labeler="FactDesk"),
        FactLabelRow(line=3, t=99, verdict="false", labeler="FactDesk"),
        FactLabelRow(line=4, t=2, verdict="probably", labeler="FactDesk"),
    ]

    result = import_fact_labels(harbour_fire, rows)

    assert result.imported == 1
    assert result.problems == [
        "line 3: the chronicle has no beat at t=99",
        "line 4: unknown verdict 'probably' (verified, false, unverified, misleading)",
    ]


def test_importing_again_updates_a_labelers_verdict_instead_of_adding_one(harbour_fire):
    import_fact_labels(harbour_fire, [FactLabelRow(line=2, t=1, verdict="unverified", labeler="FactDesk")])

    import_fact_labels(harbour_fire, [FactLabelRow(line=2, t=1, verdict="false", labeler="FactDesk")])

    assert list(harbour_fire.beats.get(t=1).fact_labels.values_list("verdict", flat=True)) == ["false"]


def test_the_command_imports_an_annotation_sheet_and_reports_what_it_could_not(harbour_fire, tmp_path):
    sheet = tmp_path / "labels.csv"
    sheet.write_text("t,verdict,labeler,note\n1,unverified,FactDesk,No witness named.\n99,false,FactDesk,\n")
    output = StringIO()

    call_command("import_fact_labels", str(harbour_fire.pk), str(sheet), stdout=output)

    assert output.getvalue().splitlines() == [
        "Imported 1 fact label into The Harbour Fire (The Courier).",
        "1 row could not be imported:",
        "  line 3: the chronicle has no beat at t=99",
    ]


def test_the_command_rejects_a_sheet_without_the_expected_columns(harbour_fire, tmp_path):
    sheet = tmp_path / "labels.csv"
    sheet.write_text("beat,label\n1,false\n")

    with pytest.raises(CommandError, match="the sheet needs the columns t, verdict, labeler"):
        call_command("import_fact_labels", str(harbour_fire.pk), str(sheet), stdout=StringIO())


def test_the_command_names_a_chronicle_that_does_not_exist(tmp_path):
    sheet = tmp_path / "labels.csv"
    sheet.write_text("t,verdict,labeler\n1,false,FactDesk\n")

    with pytest.raises(CommandError, match="there is no chronicle 999"):
        call_command("import_fact_labels", "999", str(sheet), stdout=StringIO())
