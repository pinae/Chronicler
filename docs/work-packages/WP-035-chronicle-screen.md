# WP-035: Chronicle screen

**Milestone:** M8 · **Serves:** RQ2

## Goal
A GM or writer can read a chronicle's beats as any audience saw them, at any point in time.

## Acceptance criteria
- An API endpoint returns a chronicle's beats up to `t` (default: the latest), filtered by scope:
  all beats, the table view, or one player's view.
- The screen lists beats with `t`, text and predicate, and has controls for scope and `t`.
- A private backstory beat appears only under that player's filter.
- Usage doc and e2e tests cover the scenarios; each interaction writes a usage event.

## Dependencies
WP-009, WP-034.

## Out of scope
Adding or ingesting utterances from the UI.

## Status
open
