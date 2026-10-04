import json
from collections.abc import Callable
from typing import Any

from django.http import HttpRequest, HttpResponse

from chronicle.models import Chronicle
from gm_ui.models import UsageEvent

API_PREFIX = "/api/"
SCHEMA_PATHS = {"/api/openapi.json", "/api/docs"}
# A view acting at a t that is not a query parameter (e.g. the t a dry-run beat would get) sets it here.
USAGE_T_ATTRIBUTE = "usage_t"


class UsageEventMiddleware:
    """Records every API request as a UsageEvent, so no endpoint can forget to (RQ2)."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        if request.path.startswith(API_PREFIX) and request.path not in SCHEMA_PATHS:
            record_usage(request, response)
        return response


def record_usage(request: HttpRequest, response: HttpResponse) -> None:
    match = request.resolver_match
    kwargs = match.kwargs if match else {}
    requested_chronicle = kwargs.get("chronicle_id")
    params: dict[str, Any] = {**request.GET.dict(), **kwargs, "status": response.status_code}
    body = json_body(request)
    if body is not None:
        params["body"] = body
    UsageEvent.objects.create(
        view=(match.url_name if match and match.url_name else request.path),
        # A request for a chronicle that does not exist is still recorded, without the link.
        chronicle=Chronicle.objects.filter(pk=requested_chronicle).first() if requested_chronicle else None,
        t=usage_t(request),
        params=params,
    )


def usage_t(request: HttpRequest) -> int | None:
    t = getattr(request, USAGE_T_ATTRIBUTE, None) or request.GET.get("t")
    if isinstance(t, int):
        return t
    return int(t) if t and t.isdigit() else None


def json_body(request: HttpRequest) -> Any:
    """What a POST sent as JSON, e.g. the beat a GM tried; None for anything else."""
    if request.method != "POST" or request.content_type != "application/json":
        return None
    try:
        return json.loads(request.body)
    except ValueError:
        return None
