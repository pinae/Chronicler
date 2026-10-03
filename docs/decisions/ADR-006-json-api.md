# ADR-006: The JSON API between backend and frontend

**Status:** accepted (2026-10-03) · **Work package:** WP-032

## Context
The GM/writer screens (React, ADR-001) need a JSON API: mostly reads (chronicles, beats in a scope at
`t`, the lattice at `t`, expectations, who knows what) plus one dry-run POST. The codebase is fully
typed (mypy, django-stubs), the frontend is strict TypeScript, and every interaction must be logged as
a `UsageEvent` (RQ2). Small team, readability first.

## Options considered
1. **Django REST framework 3.18.** Mature, huge ecosystem, browsable API; serializers and viewsets
   are verbose for a small read-mostly API and loosely typed.
2. **django-ninja 1.7.** Endpoints are typed functions with Pydantic schemas; validates input and
   output; publishes an OpenAPI schema from which TypeScript types can be generated. Smaller
   ecosystem than DRF.
3. **Plain Django views returning `JsonResponse`.** No dependency; validation, error format and API
   documentation all by hand.

## Decision
django-ninja (`django-ninja>=1.7,<2`), one `NinjaAPI` in `gm_ui/api.py` mounted at `/api/`, URL namespace
`api`. Usage logging is a middleware (`gm_ui.middleware.UsageEventMiddleware`) that records every
`/api/` request (view name, chronicle, `t`, parameters), so no endpoint can forget it. No
authentication in v1: a single trusted local user.

## Reasoning
- Recent comparisons recommend django-ninja as the default for new Django API projects that value
  typed code and automatic OpenAPI documentation, and DRF where its mature plugin ecosystem
  (permissions, browsable API, heavy CRUD) is needed. That ecosystem is not a factor here
  ([DRF vs Ninja 2026](https://softaims.com/blog/django-rest-framework-vs-ninja-api-guide-2026),
  [HackerOne: high-level comparison](https://www.hackerone.com/blog/django-rest-framework-vs-django-ninja-high-level-comparison),
  [Loopwerk: DRF versus Django Ninja](https://www.loopwerk.io/articles/2024/drf-vs-ninja/)).
- Typed schemas match the mypy-checked backend; the OpenAPI schema lets the frontend get types
  instead of hand-written duplicates.
- Both projects are actively maintained and support Django 5.2 (PyPI, checked 2026-10-03:
  django-ninja 1.7.1 of 2026-09-19, djangorestframework 3.18.1 of 2026-09-07).

## Consequences
- API endpoints are plain typed functions; tests call them with Django's test client.
- `/api/openapi.json` and `/api/docs` document the API; they are not logged as usage.
- Adding authentication later means a ninja auth class plus a decision recorded in a new ADR.
