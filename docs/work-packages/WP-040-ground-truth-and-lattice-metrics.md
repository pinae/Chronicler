# WP-040: Ground truth and lattice metrics

**Milestone:** M9 · **Serves:** RQ1

## Goal
The metrics that need only the lattice history: did the engine hold the twist, since when, and
how much of the story did it cover?

## Acceptance criteria
- `ground_truth.yaml` (§9.1) is parsed and validated: the schema exists, the bound entities
  exist, and `reveal_t` and `dormant_window` lie within the story.
- Pure functions in `evaluation/metrics.py`, each tested against a synthetic run file with known
  answers:
  - twist recall at `reveal_t - k` for k ∈ {1, 5, 20};
  - lead time;
  - coverage: share of beats filling at least one step, and share quarantined;
  - voiced-hypothesis agreement with the engine's top-k at the voicing `t`.

## Dependencies
WP-022, WP-030.

## Out of scope
Metrics that need the reader model (WP-041).

## Status
open
