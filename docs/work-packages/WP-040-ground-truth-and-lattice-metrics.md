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
done

## Summary
- `evaluation/ground_truth.py` reads `ground_truth.yaml` (format in `fixtures/stories/README.md`)
  into `GroundTruth` (entities as slugs) and rejects it unless the schema and its roles exist, every
  slug is an entity of the story of the kind its role needs, `reveal_t` and `dormant_window` lie
  within the story, the window ends before the reveal, and each reader belief lies within the story
  with probabilities adding up to 1. A story without the file has no ground truth (`None`).
- `evaluation/metrics.py`, pure functions over a parsed run file, per audience ("all" or a player
  name), tested against hand-built run files (`evaluation/tests/synthetic_runs.py`) and once against
  a real replay of `steward`:
  - **holding the truth**: a live or complete hypothesis of the true schema that binds every role of
    the true binding the same way (more specific hypotheses count; open roles do not);
  - `twist_recall(run, truth, k)` at `reveal_t - k` (None before the story began), `RECALL_KS`;
  - `first_held_t` and `lead_time` = `reveal_t - first_held_t` (None if not held by the reveal);
  - `coverage`: beats filling a step of any hypothesis ever made (refuted, pruned and merged ones
    too, from the last lattice), and beats quarantined, as `Share(count, total)`;
  - `voiced_agreement(run, k)`: of the voiced theories (one per utterance, judged at the t it was
    voiced first), how many match a reading among the engine's top k held hypotheses at that t.
    Hypotheses without fills are excluded from the top k: they exist only because a player voiced
    them. Ties rank the older first, as pruning does.
- Prerequisite fix (first commit): hypotheses record `voiced_at_t`, so the lattice and the run file
  show a voicing only from the t it happened (the replay guarantee was broken for theories that
  marked an older hypothesis). Run files now carry `voiced_in` and `voiced_at_t`.
