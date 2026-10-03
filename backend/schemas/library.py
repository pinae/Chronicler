"""The schema library: YAML files under schemas/library/ loaded into the database."""

from pathlib import Path
from typing import Any

import yaml
from django.db import transaction

from schemas.definitions import SchemaDefinition, StepDefinition, parse_schema
from schemas.models import Schema, Step

LIBRARY_DIR = Path(__file__).with_name("library")


def read_library(directory: Path = LIBRARY_DIR) -> list[SchemaDefinition]:
    return [
        parse_schema(yaml.safe_load(path.read_text()), source=path.name)
        for path in sorted(directory.glob("*.yaml"))
    ]


def load_library(directory: Path = LIBRARY_DIR) -> list[Schema]:
    """Parse every file first, so one broken file leaves the database untouched."""
    definitions = read_library(directory)
    with transaction.atomic():
        return [save_schema(definition) for definition in definitions]


def save_schema(definition: SchemaDefinition) -> Schema:
    with transaction.atomic():
        schema, _ = Schema.objects.update_or_create(
            slug=definition.slug,
            defaults={
                "name": definition.name,
                "roles": dict(definition.roles),
                "constraints": [constraint.to_document() for constraint in definition.constraints],
                "payoff_steps": list(definition.payoff_steps),
                "prior": definition.prior,
                "origin": definition.origin,
            },
        )
        for step in definition.steps:
            Step.objects.update_or_create(schema=schema, step_id=step.step_id, defaults=step_fields(step))
        schema.steps.exclude(step_id__in=[step.step_id for step in definition.steps]).delete()
        return schema


def step_fields(step: StepDefinition) -> dict[str, Any]:
    return {
        "order": step.order,
        "phase": step.phase,
        "patterns": [pattern.to_document() for pattern in step.patterns],
        "required": step.required,
        "repeatable": step.repeatable,
        "weight": step.weight,
        "contradicts": [pattern.to_document() for pattern in step.contradicts],
        "trigger": step.trigger,
    }


def definition_of(schema: Schema) -> SchemaDefinition:
    document = {
        "slug": schema.slug,
        "name": schema.name,
        "roles": schema.roles,
        "prior": schema.prior,
        "payoff_steps": schema.payoff_steps,
        "constraints": schema.constraints,
        "origin": schema.origin,
        "steps": [
            {"step_id": step.step_id, **step_fields_from_row(step)} for step in schema.steps.order_by("order")
        ],
    }
    return parse_schema(document, source=f"schema '{schema.slug}'")


def step_fields_from_row(step: Step) -> dict[str, Any]:
    return {
        "phase": step.phase,
        "patterns": step.patterns,
        "required": step.required,
        "repeatable": step.repeatable,
        "weight": step.weight,
        "contradicts": step.contradicts,
        "trigger": step.trigger,
    }
