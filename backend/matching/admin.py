from django.contrib import admin

from matching.models import Expectation, Hypothesis, StepFill
from narrative_engine.read_only_admin import ReadOnlyAdmin, ReadOnlyInline


class StepFillInline(ReadOnlyInline):
    model = StepFill
    fields = ["step", "beat"]


@admin.register(Hypothesis)
class HypothesisAdmin(ReadOnlyAdmin):
    list_display = [
        "__str__",
        "chronicle",
        "weight",
        "created_at_t",
        "status_changed_at_t",
        "for_player",
        "voiced_by",
    ]
    list_filter = ["status", "schema"]
    inlines = [StepFillInline]


@admin.register(StepFill)
class StepFillAdmin(ReadOnlyAdmin):
    list_display = ["__str__", "hypothesis"]


@admin.register(Expectation)
class ExpectationAdmin(ReadOnlyAdmin):
    list_display = ["question", "computed_at_t", "for_player", "hypothesis", "llm_call"]
