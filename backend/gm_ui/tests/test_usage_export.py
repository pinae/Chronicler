import json
from datetime import UTC, datetime
from io import StringIO

import pytest
from django.core.management import CommandError, call_command

from chronicle.models import Chronicle
from gm_ui.models import UsageEvent

pytestmark = pytest.mark.django_db


def event(view, chronicle, day, t=None):
    created = UsageEvent.objects.create(
        view=view, chronicle=chronicle, t=t, params={"t": str(t)} if t else {}
    )
    UsageEvent.objects.filter(pk=created.pk).update(created_at=datetime(2026, 10, day, 20, 0, tzinfo=UTC))
    return created


@pytest.fixture
def two_tables():
    wend = Chronicle.objects.create(kind="session", title="Wend")
    harbour = Chronicle.objects.create(kind="session", title="Harbour")
    event("get_lattice", wend, day=1, t=10)
    event("list_beats", wend, day=2)
    event("get_lattice", harbour, day=2, t=3)
    event("list_expectations", wend, day=3, t=12)
    return wend, harbour


def export(*options):
    output = StringIO()
    call_command("export_usage", *options, stdout=output)
    return [json.loads(line) for line in output.getvalue().splitlines()]


def test_the_usage_of_one_chronicle_is_exported_as_json_lines_in_order(two_tables):
    wend, _ = two_tables

    events = export("--chronicle", str(wend.pk))

    assert [(e["view"], e["t"]) for e in events] == [
        ("get_lattice", 10),
        ("list_beats", None),
        ("list_expectations", 12),
    ]
    assert events[0]["chronicle"] == wend.pk
    assert events[0]["params"] == {"t": "10"}
    assert events[0]["created_at"] == "2026-10-01T20:00:00+00:00"


def test_the_export_can_be_limited_to_a_range_of_days(two_tables):
    events = export("--since", "2026-10-02", "--until", "2026-10-02")

    assert [e["view"] for e in events] == ["list_beats", "get_lattice"]


def test_the_export_can_be_written_to_a_file(two_tables, tmp_path):
    target = tmp_path / "usage.jsonl"

    output = StringIO()
    call_command("export_usage", "--output", str(target), stdout=output)

    assert len(target.read_text().splitlines()) == 4
    assert f"Exported 4 usage events to {target}" in output.getvalue()


def test_a_malformed_day_is_rejected(two_tables):
    with pytest.raises(CommandError, match="--since must be a day like 2026-10-04"):
        export("--since", "last week")
