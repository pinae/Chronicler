# WP-068: Story map with the story river

**Milestone:** M8 (follow-up) · **Serves:** RQ2

## Goal
The story map screen: the beat list with the story river beside it, one column per audience, as
designed in `docs/research/visualizations.md` §1.

## Acceptance criteria
- The beat list and the river columns share one row per beat.
- Bands are coloured by schema, separated by gaps, hatched where secret, with event glyphs; a legend
  names the schemas and the hatching; hovering a band shows its reading, share, status and secret.
- A **Show as table** control shows the same numbers as a table.
- Pointing at a band brings out the compatible readings (same schema, same characters where both
  cast a role) in every column and fades the rest.
- Usage doc `docs/usage/story-map.md` with browser tests.

## Dependencies
WP-066, WP-067.

## Out of scope
Arcs, knowledge map and strips (WP-069 to WP-071).

## Status
done

## Summary
A **Story map** tab (first in the chronicle's navigation): the beat list with fixed row heights and
one SVG river per audience, drawn by React from `riverLayout` (pure, tested geometry; d3-shape for the
smooth band outlines). Bands carry the validated schema colours with 2px surface gaps, the hatching
for secrets, and ink glyphs for fills, completion, refutation and voicing; a tooltip gives the share,
reading, status and events at the pointed beat, and pointing links the compatible readings across
columns. **Show as table** gives the same shares per audience. Six browser scenarios on The Broken
Jug and Macbeth.
