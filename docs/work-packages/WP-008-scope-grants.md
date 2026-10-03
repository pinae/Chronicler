# WP-008: Scope grants

**Milestone:** M2 · **Serves:** RQ1, RQ2

## Goal
Record who knows each beat and since when: characters present, players at the table, the
implicit audience of literature and media, and characters who learn things later.

## Acceptance criteria
- Appending a beat with presence information (characters present, players present) creates one
  `ScopeGrant` per subject with `t = beat.t`.
- In `literature` and `media` chronicles, every appended beat is granted to the implicit player
  at its `t`, without presence information.
- A `learns(who, what={beat: n})` beat adds a grant on beat `n` for character `who` at the
  `learns` beat's `t`, with `via_beat` pointing to the `learns` beat.
- `Beat.known_by_chars_at(t)` and `Beat.known_by_players_at(t)` exclude grants with `t' > t`.
- Grants are append-only: `save()` on an existing grant raises.

## Dependencies
WP-006.

## Out of scope
Player-visible chronicle views (WP-009).

## Status
open
