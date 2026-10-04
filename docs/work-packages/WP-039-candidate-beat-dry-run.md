# WP-039: Candidate beat dry run

**Milestone:** M8 · **Serves:** RQ2

## Goal
A GM can ask "which hypotheses would this beat strengthen?" before narrating it.

## Acceptance criteria
- An API endpoint takes a draft beat, runs the matcher's Fill and Maintain phases on it without
  committing, and returns which hypotheses would be seeded, filled, refined, completed or
  refuted, with their weight changes.
- Nothing is persisted: beat, hypothesis and fill counts are unchanged afterwards.
- An invalid draft returns the validation errors.
- The screen has a form to compose a draft beat (predicate, role values from the chronicle's
  entities) and shows the result.
- Usage doc and e2e tests cover the scenarios; usage events are written.

## Dependencies
WP-036.

## Out of scope
Readouts for the draft beat: a dry run makes no LLM calls.

## Status
done

## Summary
- `matching/dry_run.py`: `dry_run(chronicle, CandidateBeat, for_player=None)` appends the candidate
  as the next beat and steps the stored matcher inside a transaction that is always rolled back.
  The candidate thus takes exactly the path of a narrated beat (validation, scope grants, entity
  attributes, Fill and Maintain), and nothing is kept. Each `Effect` names the hypothesis (id, or
  None for one the beat would create), its binding, the changes (`seeded`, `refined`, `filled`,
  then `completed`, `refuted`, `merged` or `pruned`), the filled step, the status and the weight
  before and after. Merged and pruned are reported too, since Maintain does them.
- Unlike narration, a dry run rejects an unknown predicate instead of quarantining it: a quarantined
  beat matches nothing, so "no change" would be misleading.
- `POST /api/chronicles/{id}/dry-run` takes the candidate (predicate, args, present characters, the
  players it is shown to, and `audience`: "all" for the GM's lattice or a player id for that
  player's lattice; "table" is 400). Validation errors are 422 with the message as `detail`.
  `GET /api/vocabulary` lists the predicates and their roles for the form. Both write usage events
  through the middleware (the candidate itself is not recorded).
- The **Try a beat** screen (`/chronicles/{id}/try`) composes a candidate: a role that takes entities
  is a choice of the chronicle's entities, a beat-only role is a number (`t`), a literal-only role is
  text; roles that only take a proposition (e.g. `says.what`) cannot be composed in the form yet.
  **Present** and **Shown to** set the initial scope (all players ticked by default), **Lattice of**
  picks the lattice. The table **Effects** shows change and weight ("0.0 → 1.5", "new: -1.5").
- Usage doc `docs/usage/try-a-beat.md`; seven e2e scenarios in `e2e/tests/try-a-beat.spec.ts`.
