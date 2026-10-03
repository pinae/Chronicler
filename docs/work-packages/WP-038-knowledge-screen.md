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
open
