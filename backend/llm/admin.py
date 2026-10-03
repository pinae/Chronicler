import json
from typing import Any

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import SafeString

from llm.models import LLMCall
from narrative_engine.read_only_admin import ReadOnlyAdmin


def indented_json(value: Any) -> SafeString:
    return format_html("<pre>{}</pre>", json.dumps(value, indent=2, ensure_ascii=False))


@admin.register(LLMCall)
class LLMCallAdmin(ReadOnlyAdmin):
    list_display = ["__str__", "model", "endpoint", "server_version", "created_at"]
    list_filter = ["model", "endpoint"]
    readonly_fields = (
        "request_hash",
        "model",
        "endpoint",
        "server_version",
        "created_at",
        "request_json",
        "response_json",
        "metadata_json",
    )
    fields = readonly_fields

    @admin.display(description="request")
    def request_json(self, call: LLMCall) -> SafeString:
        return indented_json(call.request)

    @admin.display(description="response")
    def response_json(self, call: LLMCall) -> SafeString:
        return indented_json(call.response)

    @admin.display(description="metadata")
    def metadata_json(self, call: LLMCall) -> SafeString:
        return indented_json(call.metadata)
