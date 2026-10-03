# WP-004: Chronicle, player, utterance and entity models

**Milestone:** M0/M1 · **Serves:** RQ1, RQ4

## Goal
Store the containers of a story-world record: chronicles of all three kinds, their audience,
the raw utterances with source metadata, and the entities beats will refer to.

## Acceptance criteria
- `Chronicle`, `Player`, `Utterance` and `Entity` exist with the fields from concept §4.
- A chronicle's kind must be `session`, `literature` or `media`; any other value fails validation.
- Creating a `literature` chronicle creates exactly one implicit player named `reader`; a `media`
  chronicle creates exactly one named `public`; a `session` chronicle creates none.
- Two utterances of one chronicle cannot share an `order`.
- `Utterance.source` round-trips `{chapter}` metadata and `{outlet, author, published_at, url}`
  metadata unchanged.
- An utterance's speaker can be a player, an entity (an outlet of kind `source`), or neither
  (GM / narrator).
- An entity's kind must be one of the six kinds in §4; aliases are stored as a list.

## Dependencies
WP-001.

## Out of scope
Beats, entity attributes, scope grants, fact labels.

## Status
open
