# WP-038: Knowledge screen

**Milestone:** M8 · **Serves:** RQ2

## Goal
Answer "what does X know at t" for any character or player.

## Acceptance criteria
- An API endpoint returns the beats a character or player knew at `t`, each with how it was
  learned (present when it happened, or via a `learns` beat).
- The screen lets the user choose a character or player and a `t`.
- Usage doc and e2e tests cover the scenarios; usage events are written.

## Dependencies
WP-008, WP-035.

## Out of scope
Changing scope from the UI; scope changes are beats.

## Status
done

## Summary
- `GET /api/chronicles/{id}/knowledge?character=…|player=…[&t=…]` returns every beat the knower
  knew at `t` (default: the last beat) with `known_since_t` and `learned_via_t` (the `learns` beat,
  or `null` when they were present / were shown it). Exactly one knower is required (400 otherwise);
  a knower of another chronicle is 404. When a beat was granted more than once, the earliest grant
  wins.
- `GET /api/chronicles/{id}/entities[?kind=…]` lists entities in order of introduction, so the screen
  can offer the characters.
- The knowledge screen (`/chronicles/{id}/knowledge`, linked as **Who knows what**) has a **Who**
  choice (characters and players), the shared **Up to beat** slider and a **Known beats** table whose
  column **How** says "present", "saw it" (players) or "learned at t = N". The choices live in the URL
  like the other screens.
- Usage events come from the API middleware; a test pins that the knowledge endpoint records one.
- Usage doc `docs/usage/knowledge.md`; four e2e scenarios in `e2e/tests/knowledge.spec.ts`.
