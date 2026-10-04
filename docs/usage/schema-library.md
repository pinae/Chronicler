# Schema library

Narrative patterns (schemas) are written as YAML files in `backend/schemas/library/` and loaded into
the database with one command. The files are the specification; change a schema by editing its file
and loading again.

## Before you start
- The backend is installed and migrated (`cd backend && uv run python manage.py migrate`).

## Load the library
1. In `backend/`, run `uv run python manage.py load_schemas`.

**Result:** the command prints `Loaded 5 schemas: betrayal, blame, hidden_crime, prophecy, usurpation`
(one name per file in the library). Running it again changes nothing: schemas are updated in place,
not duplicated.

## What the library reads

| Schema | Roles | The plot | Starts from | Payoff |
|---|---|---|---|---|
| `betrayal` | T(raitor), V(ictim), S(ecret) | V trusts T; T gets access to V's secret and harms (or kills) V | trust | V learns of the harm |
| `blame` | O (a source), A(ccused), V(ictim) | a news outlet claims that A harmed V, had a motive, and that people turn against A (media chronicles) | the accusation | the claimed condemnation |
| `hidden_crime` | C(ulprit), V(ictim), I(nvestigator) | C harms, kills or robs V and covers it up (e.g. blames someone else); I grows suspicious | the crime, or I's suspicion of C | I learns of the crime |
| `usurpation` | U(surper), R(uler), P(ower) | R favours U; U wants P, kills R and takes P | a favour or trust R grants | U has P |
| `prophecy` | S(eer), H(older), X (the thing foretold) | S foretells that H will have X; H wants or fears it | the foretelling | H has X, or is given it |

The [guided tour](guided-tour.md) shows these schemas at work on two well-known plays.

To load only some files (the test suite does this, so that its expectations do not change whenever
the library grows), set `SCHEMA_LIBRARY_SLUGS = ["betrayal", "blame"]` in the settings module.

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

**Result:** `Loaded 6 schemas: betrayal, blame, hidden_crime, prophecy, rivalry, usurpation`.

## Constraints
A schema may list constraints that every match must satisfy; a hypothesis that violates one is
refuted:

```yaml
constraints:
  - {type: distinct, roles: [T, V]}                     # different entities
  - {type: before, steps: [trust, harm]}                # first trust fill before first harm fill
  - {type: after, steps: [harm, trust]}                 # the mirror of before
  - {type: knows, role: T, step: harm}                  # T knew the harm beat when it happened
  - {type: not_knows, role: V, step: harm, until: reveal}  # V must not know it before the reveal
  - {type: same_place, roles: [T, V], step: harm}       # both at the same place at the harm
```

Knowledge changes while a story is told, so `not_knows` takes an `until` step: from that step's
fill on, the character may know. Without `until`, the character may never know.

## A broken schema
1. In `rivalry.yaml`, change `payoff_steps: [showdown]` to `payoff_steps: [finale]`.
2. Run `uv run python manage.py load_schemas`.

**Result:** the command fails with `CommandError: rivalry.yaml: payoff step 'finale' is not a step`
and no schema in the database changes. Other errors name the step and pattern, for example
`rivalry.yaml: step 'clash', pattern 1: unknown predicate 'stabs'`.
