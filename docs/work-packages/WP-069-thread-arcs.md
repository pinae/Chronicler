# WP-069: Thread arcs and open threads

**Milestone:** M8 (follow-up) · **Serves:** RQ2

## Goal
Selecting a thread on the story map draws arcs between the beats that filled its steps and lists the
open steps of every live reading, oldest setup first (§2 of the research note).

## Acceptance criteria
- Clicking a band selects its thread; arcs connect its filled steps in order, labelled with the
  step names; open steps are listed.
- An **Open threads** list names, for each live reading, the steps still open and the age of its
  oldest fill.

## Dependencies
WP-068.

## Status
done (2026-10-05). Each river thread now carries the required steps its strongest reading still
lacks (`open_steps`) and the beat of its first fill (`waiting_since`); a thread nothing supports
waits since no beat. Clicking a band selects its thread: a lane between the beats and the rivers
draws an arc from each filled step to the next, labelled with the step names, and a dashed line
labelled *to come* for the open steps; clicking again or Escape clears it. **Open threads** lists,
per chosen audience, the threads with open steps, the longest waiting first, and selects one on
click. Usage: `docs/usage/story-map.md` (*See a thread's steps*, *List the open threads*), covered
by e2e tests.
