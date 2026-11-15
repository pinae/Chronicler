# ADR-013: Predicates for identity and kinship

**Status:** accepted (2026-11-15) · **Work package:** WP-075

## Context
Two classic kinds of plot twist turn on facts that link two entities: the person known as A is
really B (an alias, a disguise, a twin standing in for his brother), and two characters are kin.
The starter vocabulary (concept §5) cannot state either. `is(who, trait)` takes only a literal, so
"Vader is Luke's father" would lose Luke as an entity, and no schema could bind both characters.
Growing the vocabulary is a reviewed change; the concept asks to map new verbs onto existing
predicates first.

## Options considered
1. **Literal traits** (`is(Vader, "Luke's father")`). No change, but the second entity is lost; the
   matcher compares literals exactly, so no schema can read the twist.
2. **An entity role on `is`** (`is(who, trait, of?)`). One predicate fewer, but every `is` pattern
   would then also match relations, and `trait` would mean two different things.
3. **Merge entities when an identity is revealed.** Truest to "they are one person", but the
   chronicle is append-only and time-indexed: before the reveal they must stay two, so a merge is
   itself a fact at a time, i.e. a beat.
4. **Two predicates:** `poses_as(who, whom)` for identity (alias, disguise, twin) and
   `kin(who, whom, as?)` for family, `as` naming how ("father").

## Decision
Option 4. The vocabulary grows from 28 to 30 predicates, within the limit of about 40. `poses_as`
uses the existing person roles so readout questions say "someone" for an open role; `kin` keeps
the relation as an optional literal, so a schema can match any kinship or, later, one kind.

## Consequences
- The ingester learns the two predicates from the vocabulary like any other.
- Entities stay separate after an identity reveal; the `poses_as` beat links them. Views that
  should treat both as one person would read that beat (not needed so far).
