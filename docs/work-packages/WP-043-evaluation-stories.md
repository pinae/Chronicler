# WP-043: Evaluation stories

**Milestone:** M9 · **Serves:** RQ1

## Goal
Two complete hand-authored stories prove the pipeline end to end: the engine sees each twist
coming.

## Acceptance criteria
- Two stories under `fixtures/stories/` (our own material), each with transcript, beats,
  entities, `ground_truth.yaml` and a README with provenance and chronicle kind. `steward` may be
  extended to be one of them.
- A test replays both with the fixture ingester and the test reader and asserts twist recall at
  k = 5 on both.

## Dependencies
WP-042.

## Out of scope
Public-domain and recorded-session corpora (R1); LLM-backed ingest or readouts.

## Status
done

## Summary
- `steward` (session) got a `ground_truth.yaml`: Aldric betrays Mira (T, V; the seal is left out
  because the table never hears of it, so the reader could never be asked about a truth naming
  it), reveal at t=22, dormant window 8–21, one annotated belief at t=16.
- New story `ferryman` (literature, 18 beats, our own material): Tilde betrays Oskar and steals the
  ledger key while the prose points at Bram, a red herring no betrayal step matches beyond trust.
  Its truth binds the key as well (T, V, S), so it is held only once the refined hypothesis exists
  (t=7). Reveal at t=17, window 7–16, one annotated belief at t=13.
- `evaluation/tests/test_evaluation_stories.py` replays both with the fixture ingester and the
  uniform reader and asserts twist recall at k = 5; a second test checks that the ferryman lattice
  holds the red herring next to the truth at t=13.
- With the uniform reader: steward recalls the twist at k = 1, 5 and 20 (lead time 20 beats);
  ferryman at k = 1 and 5 (lead time 10; k = 20 lies before the story). Coverage is 50 % for both.
- Found on the way: a flat belief curve reported its first beat as the "largest surprise";
  `largest_surprise_t` now returns None when the belief never rises.
