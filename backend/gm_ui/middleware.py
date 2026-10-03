from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

from chronicle.models import Chronicle
from gm_ui.models import UsageEvent

API_PREFIX = "/api/"
SCHEMA_PATHS = {"/api/openapi.json", "/api/docs"}


class UsageEventMiddleware:
    """Records every API request as a UsageEvent, so no endpoint can forget to (RQ2)."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        if request.path.startswith(API_PREFIX) and request.path not in SCHEMA_PATHS:
            record_usage(request)
        return response


def record_usage(request: HttpRequest) -> None:
    match = request.resolver_match
    kwargs = match.kwargs if match else {}
    t = request.GET.get("t")
    requested_chronicle = kwargs.get("chronicle_id")
    UsageEvent.objects.create(
        view=(match.url_name if match and match.url_name else request.path),
        # A request for a chronicle that does not exist is still recorded, without the link.
        chronicle=Chronicle.objects.filter(pk=requested_chronicle).first() if requested_chronicle else None,
        t=int(t) if t and t.isdigit() else None,
        params={**request.GET.dict(), **kwargs},
    )
