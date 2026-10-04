import dataclasses
from io import StringIO

import pytest
import yaml
from django.core.management import CommandError, call_command

from schemas.definitions import parse_schema
from schemas.library import LIBRARY_DIR, definition_of, load_library, read_library, save_schema
from schemas.models import Schema, Step

pytestmark = pytest.mark.django_db


def betrayal_definition():
    return parse_schema(yaml.safe_load((LIBRARY_DIR / "betrayal.yaml").read_text()), source="betrayal.yaml")


def test_loading_the_library_stores_betrayal_and_its_steps_in_order():
    load_library()

    betrayal = Schema.objects.get(slug="betrayal")
    assert (betrayal.name, betrayal.prior, betrayal.payoff_steps, betrayal.origin) == (
        "Betrayal",
        -2.0,
        ["reveal"],
        "library",
    )
    assert [(step.step_id, step.order, step.phase) for step in betrayal.steps.all()] == [
        ("trust", 1, "setup"),
        ("access", 2, "development"),
        ("harm", 3, "development"),
        ("benefit", 4, "development"),
        ("reveal", 5, "payoff"),
    ]


def test_stored_schema_reads_back_as_the_same_definition():
    load_library()

    assert definition_of(Schema.objects.get(slug="betrayal")) == betrayal_definition()


def test_loading_an_unchanged_library_twice_creates_no_duplicates():
    definitions = read_library()

    load_library()
    load_library()

    assert Schema.objects.count() == len(definitions)
    assert Step.objects.count() == sum(len(definition.steps) for definition in definitions)


def test_saving_a_changed_definition_updates_the_schema_in_place():
    original = save_schema(betrayal_definition())
    trust = original.steps.get(step_id="trust")
    definition = betrayal_definition()
    stronger_trust = dataclasses.replace(definition.steps[0], weight=0.75)

    save_schema(dataclasses.replace(definition, steps=(stronger_trust, *definition.steps[1:])))

    updated = Step.objects.get(pk=trust.pk)
    assert updated.weight == 0.75


def test_step_removed_from_a_definition_is_removed_from_the_schema():
    save_schema(betrayal_definition())
    definition = betrayal_definition()
    without_benefit = tuple(step for step in definition.steps if step.step_id != "benefit")

    schema = save_schema(dataclasses.replace(definition, steps=without_benefit))

    assert list(schema.steps.values_list("step_id", flat=True)) == ["trust", "access", "harm", "reveal"]


def test_load_schemas_command_reports_what_it_loaded():
    output = StringIO()

    call_command("load_schemas", stdout=output)

    assert "Loaded 2 schemas: betrayal, blame" in output.getvalue()


def test_load_schemas_command_fails_with_the_file_and_problem(tmp_path):
    (tmp_path / "broken.yaml").write_text(
        "slug: broken\nname: Broken\nroles: {}\nsteps: []\npayoff_steps: [end]\n"
    )

    with pytest.raises(CommandError, match=r"broken\.yaml: payoff step 'end' is not a step"):
        call_command("load_schemas", directory=str(tmp_path))
    assert Schema.objects.count() == 0


def test_schema_and_step_read_as_their_names():
    schema = save_schema(betrayal_definition())

    assert str(schema) == "Betrayal"
    assert str(schema.steps.get(step_id="harm")) == "betrayal.harm"


def test_stored_roles_keep_their_order_on_any_database():
    """PostgreSQL stores JSON objects as JSONB, which sorts their keys; a list keeps the order of
    the schema file, which decides e.g. which open role a readout asks about first."""
    load_library()

    stored = Schema.objects.filter(slug="betrayal").values_list("roles", flat=True).get()

    assert stored == [["T", "character"], ["V", "character"], ["S", "secret"]]
    assert list(definition_of(Schema.objects.get(slug="betrayal")).roles) == ["T", "V", "S"]


def test_the_library_can_be_limited_to_some_schemas(settings):
    settings.SCHEMA_LIBRARY_SLUGS = ["blame"]

    assert [definition.slug for definition in read_library()] == ["blame"]


def test_every_schema_file_in_the_library_parses(settings):
    settings.SCHEMA_LIBRARY_SLUGS = None

    assert [definition.slug for definition in read_library()] == [
        "betrayal",
        "blame",
        "hidden_crime",
        "prophecy",
        "usurpation",
    ]
