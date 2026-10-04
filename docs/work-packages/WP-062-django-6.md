# WP-062: Upgrade to Django 6.1

**Milestone:** M0 (follow-up) · **Serves:** maintenance

## Goal
The backend runs on a recent Django 6.x, as the project owner asked, with type stubs to match.

## Acceptance criteria
- The project depends on Django 6.1 and django-stubs 6.1; a test states the Django version.
- The full suite, ruff and mypy pass on SQLite and PostgreSQL; `makemigrations --check` finds no
  changes and `manage.py check` no issues.
- ADR-002 records the change from 5.2 LTS to 6.1.

## Dependencies
WP-001.

## Out of scope
Using new Django 6 features (template partials, the tasks framework, CSP middleware).

## Status
done

## Summary
Django 6.1.1 and django-stubs 6.1.1. The upgrade needed no code changes: none of the APIs that 6.0
and 6.1 changed are used, `DEFAULT_AUTO_FIELD` was already set, and no migrations were generated.
ADR-002 has an amendment explaining why the project left the LTS line.
