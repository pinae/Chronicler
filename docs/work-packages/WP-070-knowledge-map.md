# WP-070: Knowledge map

**Milestone:** M8 (follow-up) · **Serves:** RQ2

## Goal
A story-map tab showing who knew which beat from when, with beats learned later drawn as fuses from
the row where they happened to the row where they were learned (§3 of the research note).

## Acceptance criteria
- One column per audience aligned with the beat rows; known, learned later (with the fuse) and
  unknown are distinguishable without colour.
- In The Broken Jug, the game master's notes burn down in every player's column: the broken jug
  (t=3) to t=26, the threat to Eve (t=2) to t=30; the judge's visit (t=1) is never learned.
  (Corrected while implementing: the first draft said all three notes reach t=26, but the fixture
  reveals them at different beats.)

## Dependencies
WP-068.

## Status
done (2026-10-05). `GET /api/chronicles/{id}/knowledge_map` lists, per player at the table, every
beat they came to know with `known_since_t` and `learned_via_t` (sharing the first-grant logic with
the *Who knows what* endpoint). The story map now has two views, **Story river** (`/map`) and
**Knowledge map** (`/map/knowledge`), sharing the beat rows, column headers and toolbar
(`BeatRows`, `MapColumn`, `MapToolbar`, extracted from the river view). A player's column shows a
filled square for a beat known when it happened, a hollow square with a dashed fuse down to a spark
in the row where it was learned, and nothing for a beat never learned; fuses that start while
another burns nest inside it, so none cross. Every mark has a tooltip, and **Show as table** gives
the same facts as **Who knew what**. The game master's column is left out: they know every beat
when it happens. Characters' columns (the research note's option) are left for later. Usage:
`docs/usage/knowledge-map.md`, covered by e2e tests.
