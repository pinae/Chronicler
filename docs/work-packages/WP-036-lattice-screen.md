# WP-036: Lattice screen

**Milestone:** M8 · **Serves:** RQ2

## Goal
Show the hypothesis lattice at a chosen `t` (default: now), so a GM can see which stories the
chronicle currently supports.

## Acceptance criteria
- An API endpoint returns `Lattice.at(chronicle, t)`, optionally for one player: schema, binding
  with entity names, weight, status, filled and open steps, and the `refines` parent.
- The screen shows hypotheses grouped by schema and ordered by weight, with a `t` control.
- Moving `t` back shows the lattice as it was then (the same data as `Lattice.at`).
- Usage doc and e2e tests cover the scenarios; usage events are written.

## Dependencies
WP-021, WP-035.

## Out of scope
Expectations (WP-037).

## Status
done

## Summary
`GET /api/chronicles/{id}/lattice?audience=all|<player id>&t=` returns `Lattice.at(t)` for the GM's
view or one player's: schema, binding with entity names, status, weight, filled steps with their beat
`t`s, open steps, `refines` and whether the hypothesis was voiced. The table has no lattice of its
own and gets a 400 that says so. `/chronicles/:id/lattice` groups hypotheses by schema, strongest
first, and shares the **Seen by** / **Up to beat** controls (now `useChronicleView`) with the
chronicle page. Replay and `seed_e2e` gained `--per-player`, so player lattices exist to show.
`docs/usage/lattice.md` has four scenarios, each with a browser test.
