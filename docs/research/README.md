# Research reports

Reports written by `manage.py report` (see `docs/usage/report.md`) from replays of the fixture
stories. They are regenerated, not edited; notes on them belong here.

## rq1-baseline.md (2026-10-04)

The two evaluation stories (`steward`, `ferryman`) replayed with the fixture ingester and the
uniform reader, i.e. hand-written beats and a reader that believes nothing in particular.

- **The matcher holds both twists well before the reveal**: from the first trust beat in `steward`
  (lead time 20 beats) and from the refinement that binds the key in `ferryman` (10 beats), and
  still at reveal − 5 and − 1. In `ferryman` it holds the red herring (Bram) at the same time.
- **Coverage is 50 %** in both stories: half the beats fill no step of the one schema in the
  library (`betrayal`). They set scenes or mislead (`is_at`, `opposes`, `seeks`, `distrusts`).
  More schemas, not more vocabulary, would raise it; nothing was quarantined.
- **The reader-based rows mean nothing yet**: the uniform reader makes retrospective fit 0 %, the
  surprise curve flat (`n/a`) and the Brier score the distance of a uniform guess from the
  annotation. They become meaningful with the language model (WP-044 for Bayes factors) and on
  the real corpus (WP-057).
