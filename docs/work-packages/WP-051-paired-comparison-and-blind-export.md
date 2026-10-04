# WP-051: Paired comparison and blind export

**Milestone:** R2 · **Serves:** RQ3

## Goal
Compare stories written with and without the engine's structure, and prepare them for human
raters who must not know which is which.

## Acceptance criteria
- A harness generates both variants from the same seed story and settings, and computes the §9.2
  metrics for each.
- The rater export lists stories under random ids, contains no condition information, and keeps
  the id → condition key in a separate file.

## Dependencies
WP-050.

## Out of scope
Collecting and analysing the ratings.

## Notes
- The same reader model guides and judges (§9.4), so human ratings carry the headline result.

## Status
done

## Summary
`writing/comparison.py`: `compare_writers` continues one seed toward one target with each writer
(same ingester, reader and number of continuations) and measures each `Variant` against the target;
`generate` now uses the same `generate_variant`. `export_for_raters` writes each story as Markdown
under a random 8-hex id in `for-raters/` with no condition information, and the id → condition key
to `condition-key.json` beside it. `manage.py compare <seed> --target … --beats N --export-dir DIR`
runs the structured and the prose-only writer, writes both runs and prints the metrics side by side
(the text table now takes any number of columns). Usage doc: `docs/usage/compare.md`.
