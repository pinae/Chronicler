# Schema library

Narrative patterns (schemas) are written as YAML files in `backend/schemas/library/` and loaded into
the database with one command. The files are the specification; change a schema by editing its file
and loading again.

## Before you start
- The backend is installed and migrated (`cd backend && uv run python manage.py migrate`).

## Load the library
1. In `backend/`, run `uv run python manage.py load_schemas`.

**Result:** the command prints `Loaded 1 schema: betrayal` (one name per file in the library).
Running it again changes nothing: schemas are updated in place, not duplicated.

## Write a schema
Create `backend/schemas/library/rivalry.yaml`:

```yaml
slug: rivalry
name: Rivalry
roles: {A: character, B: character}
prior: -1.0
payoff_steps: [showdown]
steps:
  - step_id: clash
    phase: setup
    trigger: true
    patterns:
      - {pred: opposes, args: {who: $A, whom: $B}}
    weight: 1.0
  - step_id: showdown
    phase: payoff
    patterns:
      - {pred: harms, args: {who: $A, whom: $B}}
    weight: 2.0
```

Pattern values: `$A` is a role variable, `$clash` the beat that filled step `clash`, `"*"` matches
anything, a nested `{pred, args}` matches inside a claim or belief, and anything else is a literal.
Optional pattern keys: `tags_any`, `tags_all`, `scope: {players_know: true}` and
`claimed_by: $Source`.

Run `uv run python manage.py load_schemas`.

**Result:** `Loaded 2 schemas: betrayal, rivalry`.

## A broken schema
1. In `rivalry.yaml`, change `payoff_steps: [showdown]` to `payoff_steps: [finale]`.
2. Run `uv run python manage.py load_schemas`.

**Result:** the command fails with `CommandError: rivalry.yaml: payoff step 'finale' is not a step`
and no schema in the database changes. Other errors name the step and pattern, for example
`rivalry.yaml: step 'clash', pattern 1: unknown predicate 'stabs'`.
