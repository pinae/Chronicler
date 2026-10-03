from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse

MISSING_BUILD = "The frontend has not been built yet: run `npm run build` in frontend/ (see README.md)."


def healthz(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


def frontend_app(request: HttpRequest) -> HttpResponse:
    """The built single-page app; its router handles every path the backend does not (ADR-007)."""
    index = settings.FRONTEND_DIST_DIR / "index.html"
    if not index.exists():
        return HttpResponse(MISSING_BUILD, status=503, content_type="text/plain")
    return HttpResponse(index.read_bytes(), content_type="text/html")
