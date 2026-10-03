from django.contrib import admin

from narrative_engine.read_only_admin import ReadOnlyAdmin, ReadOnlyInline
from schemas.models import Schema, Step


class StepInline(ReadOnlyInline):
    model = Step
    fields = ["order", "step_id", "phase", "required", "repeatable", "trigger", "weight"]


@admin.register(Schema)
class SchemaAdmin(ReadOnlyAdmin):
    """Read-only: the YAML files in schemas/library/ are the spec (manage.py load_schemas)."""

    list_display = ["name", "slug", "prior", "origin"]
    inlines = [StepInline]


@admin.register(Step)
class StepAdmin(ReadOnlyAdmin):
    list_display = ["__str__", "phase", "weight", "required", "repeatable", "trigger"]
