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
done

## Summary
`GET /api/chronicles/{id}` returns title, kind, latest `t` and the (non-implicit) players.
`GET /api/chronicles/{id}/beats?audience=all|table|<player id>&t=` lists the beats that audience had
seen up to `t`, resolved by `gm_ui.audiences`, which the later screens reuse. The page
`/chronicles/:id` has a **Seen by** selector and an **Up to beat** slider; both are kept in the
address, so a view can be linked and the back button works. Quarantined beats are marked, and an
unknown chronicle shows **Chronicle not found**. While testing, the usage middleware was fixed to
record requests for missing chronicles without a broken link. `docs/usage/chronicle.md` has five
scenarios, each with a browser test.
