# WP-071: Tension and surprise strip

**Milestone:** M8 (follow-up) · **Serves:** RQ1, RQ2

## Goal
A narrow strip beside the beat list with surprise (how much the readings' shares moved) and tension
(share of readings waiting for their payoff) per beat and audience (§6 of the research note).

## Dependencies
WP-067, WP-068.

## Status
done (2026-10-05). Every moment of the river now carries `surprise` (the total variation between
the readings' shares at t and at t−1, 0 when nothing was held before) and `tension` (the share of
the readings with a development step filled and no payoff step). The strip became the story map's
third view, **Pacing** (`/map/pacing`), rather than a strip inside the river view, which already
holds bands, marks and arcs: one column per audience beside the beats, tension as an area and
surprise as a bar per row, on the same 0–100 % scale, with a tooltip per row and a table view.
Suspense (the spread of the reader's answers) is left for when the language model's readouts are
calibrated (WP-063, WP-044). Usage: `docs/usage/pacing.md`, covered by e2e tests.
