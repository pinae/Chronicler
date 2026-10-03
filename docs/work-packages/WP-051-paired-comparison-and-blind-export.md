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
open
