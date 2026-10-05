# WP-072: Evidence matrix and clue ledger

**Milestone:** M8 (follow-up) · **Serves:** RQ2

## Goal
Heuer's matrix of beats against the strongest readings, and for one reading the grid of its steps
against the players (§4 and §5 of the research note).

## Dependencies
WP-068.

## Status
done (2026-10-05), in two commits.

1. **Evidence matrix**: the story map's fourth view, **Evidence** (`/map/evidence`), built from the
   river's threads and events without a backend change. For a chosen audience (**Seen by**) and
   beat (**Up to beat**), the columns are the threads held at that beat, strongest first, then
   those refuted by then (so refutations stay visible); a cell names the steps a beat filled or
   **refuted**, and the **Evidence** column says whether the beat **tells them apart**, **fits
   every reading** or **supports none**. Usage: `docs/usage/evidence.md`.
2. **Clue ledger**: the fifth view, **Clues** (`/map/clues`). The river's threads now name their
   payoff steps (`payoff_steps`, the schema's payoff phase). For one of the game master's readings
   (the strongest at the last beat by default), the ledger lists the beats that filled its steps
   against the players, each cell saying how the player came to know the beat (from the knowledge
   map), and counts per player the clues known before the first payoff beat, warning below three.
   A player who saw the first clue happen "knew it from the start" (a heuristic: the first clue
   is usually the setup, such as the crime). Usage: `docs/usage/clues.md`.

Both are covered by e2e tests.
