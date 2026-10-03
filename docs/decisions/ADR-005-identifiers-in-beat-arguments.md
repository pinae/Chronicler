# ADR-005: Identifiers in beat arguments

**Status:** accepted (2026-10-03) · **Work package:** WP-006

## Context
Concept §4.1 writes beat arguments as `{"entity": 17}` and `{"beat": 42}` without saying what the
numbers identify. Schemas reference other steps' beats (`$harm`), `learns` beats point to the beat
being learned, and the replay test (concept §11, M4) compares a lattice built over a whole story
with one built over a prefix, in a fresh chronicle. Identifiers must therefore mean the same thing
in both runs.

## Options considered
1. **Database primary keys for both.** Simple, but a story loaded twice gets different keys, so
   identical stories produce different arguments and every comparison needs translating.
2. **`t` for beats, primary keys for entities.** A beat's `t` is its identity within a chronicle
   (unique, consecutive from 1, never changes) and is the same in every replay of a story.
   Entities have no such ordinal; their keys are stable within a chronicle.
3. **Slugs or names for entities too.** Readable, but names change through aliases, and the
   ingester resolves mentions to rows anyway.

## Decision
Option 2.
- `{"beat": n}` refers to the beat with `t = n` **in the same chronicle**, and `n` must be smaller than
  the referring beat's `t`: a beat can only point backwards in time.
- `{"entity": id}` is the primary key of an `Entity` **of the same chronicle**.
- `Chronicle.append` rejects references that break either rule (`InvalidReference`), including
  references nested inside propositions.
- `t` starts at 1, so `t = 0` means "before the first beat": the empty lattice and empty views.

## Reasoning
The replay guarantee (concept §4, "the lattice at any t is a filter, not a snapshot") is the single
most important property of the project. Keeping beat references in `t` makes beats self-contained
records of the story rather than of a particular database load. Comparisons across runs then only
need to translate entity keys (by canonical name), not beat references.

## Consequences
- Code that follows a beat reference looks up `chronicle.beats.get(t=n)`, not `Beat.objects.get(pk=n)`.
- Hypothesis bindings store entity primary keys, and `$step` references compare beat `t`s.
- Fixture loaders translate entity slugs to primary keys; beat references in fixtures are `t`s as is.
