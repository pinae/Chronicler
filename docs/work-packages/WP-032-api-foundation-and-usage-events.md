# WP-032: API foundation and usage events

**Milestone:** M8 · **Serves:** RQ2

## Goal
The backend exposes a JSON API for the frontend, and every interaction is logged as raw material
for the RQ2 study.

## Acceptance criteria
- An ADR records how the API is built (e.g. Django REST framework, django-ninja or plain Django
  views).
- `GET /api/chronicles/` returns the chronicles with id, title, kind and number of beats.
- Every API request writes a `UsageEvent` with view, chronicle, `t`, parameters and timestamp.
- API tests cover the list (including the empty list) and the usage event.

## Dependencies
WP-006.

## Out of scope
Authentication: v1 assumes a single trusted local user. If deployment needs more, that is an ADR
and its own package.

## Status
done

## Summary
ADR-006 chooses django-ninja: one `NinjaAPI` in `gm_ui/api.py` at `/api/` with an OpenAPI schema for the
frontend. `GET /api/chronicles/` lists chronicles (id, title, kind, beat count), newest first.
`gm_ui.middleware.UsageEventMiddleware` records every `/api/` request as a `UsageEvent` with view name,
chronicle, `t` and parameters, so endpoints need no logging code; schema and docs requests are not
recorded.
