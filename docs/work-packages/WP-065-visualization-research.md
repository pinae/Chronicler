# WP-065: Research visualizations of story structure

**Milestone:** M8 (follow-up) · **Serves:** RQ2

## Goal
A considered set of views that let a game master see what the engine sees and how a story is built
and moves, grounded in visualization research and roleplaying practice, with an order to build them.

## Acceptance criteria
- `docs/research/visualizations.md` lists the game master's questions, the techniques that answer
  them (with sources), shared design rules and the proposed views in build order.
- ADR-011 decides how charts are drawn and validates the schema palette for colour-vision deficiency
  in both themes.
- The views are split into work packages.

## Dependencies
WP-037, WP-038.

## Out of scope
Building the views (WP-066 to WP-072).

## Status
done

## Summary
Eight proposals, from the owner's story river (one column per audience, hatching for what only the
game master holds) to thread arcs, a knowledge map, a tension and surprise strip, an evidence
matrix, a clue ledger, storylines and a reading genealogy, all on one shared vertical beat axis.
ADR-011: d3-scale/d3-shape for geometry, React for SVG, a five-colour steampunk schema palette that
passes all-pairs CVD checks in light and dark.
