# WP-007: Entity attribute view

**Milestone:** M1 · **Serves:** RQ1

## Goal
Entity state (`is`, `has`, `is_at`) is available as a derived view with provenance, and can be
rebuilt from the beat log for any point in time.

## Acceptance criteria
- Appending an `is` beat creates or updates the subject's `EntityAttribute` row for that key,
  with `source_beat` set to the beat. The same holds for `has` and `is_at`.
- Rebuilding the view from scratch yields rows identical to the incrementally maintained ones
  (entity, key, value, source beat).
- The projection is a pure function over a sequence of beats; the attributes as of `t` are the
  projection of the beats with `t' ≤ t`.
- Quarantined beats never change the view.

## Dependencies
WP-006.

## Out of scope
Entity resolution and alias matching (ingest, WP-031).

## Notes
- Open: how `is` traits map onto keys (one row per trait or one `trait` key), and how a
  multi-valued `has` fits "one row per (entity, key)". Decide at the start of the package and
  record the rule in the summary.

## Status
open
