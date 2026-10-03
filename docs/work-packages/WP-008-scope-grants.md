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
done

## Summary
`ScopeGrant` records "subject knows beat since t" for exactly one character or player and cannot
change once stored. `BeatDraft` carries the ids of present characters and players; appending creates
their grants at the beat's `t`, plus a grant for the implicit audience of literature and media. A
`learns(who, what={beat: n})` beat grants beat `n` to `who` with `via_beat` set; learning a
proposition grants nothing. `known_by_chars_at(t)` / `known_by_players_at(t)` ignore later grants,
and presence ids from other chronicles are rejected.
