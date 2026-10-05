# WP-072: Evidence matrix and clue ledger

**Milestone:** M8 (follow-up) · **Serves:** RQ2

## Goal
Heuer's matrix of beats against the strongest readings, and for one reading the grid of its steps
against the players (§4 and §5 of the research note).

## Dependencies
WP-068.

## Status
in progress (two commits).

1. **Evidence matrix** (done, 2026-10-05): the story map's fourth view, **Evidence**
   (`/map/evidence`), built from the river's threads and events without a backend change. For a
   chosen audience (**Seen by**) and beat (**Up to beat**), the columns are the threads held at that
   beat, strongest first, then those refuted by then (so refutations stay visible); a cell names the
   steps a beat filled or **refuted**, and the **Evidence** column says whether the beat **tells
   them apart**, **fits every reading** or **supports none**. Usage: `docs/usage/evidence.md`.
2. **Clue ledger**: next.
