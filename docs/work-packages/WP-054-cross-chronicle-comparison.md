# WP-054: Cross-chronicle comparison

**Milestone:** R3 · **Serves:** RQ4

## Goal
Compare how strongly different outlets instantiate the same narrative patterns, and how much of
that rests on unverified or false claims.

## Acceptance criteria
- Schema completion per outlet, overlap of filled steps between outlets, and completion
  conditioned on fact labels (the share of a schema's weight resting on claims labeled `false` or
  `unverified`), each tested on synthetic data.
- The usage doc states the boundary from §1: the engine measures narrative instantiation; it does
  not adjudicate truth.

## Dependencies
WP-040, WP-053.

## Out of scope
Any statement about which outlet is right.

## Status
done

## Summary
`evaluation/outlets.py` compares outlets as plain `OutletLattice`s (readings with entity slugs, and
the beats labeled false or unverified): `completion` (required steps of the best held reading),
`step_overlap` (Jaccard of (reading, step) pairs, the source role left out since each outlet is its
own source) and `suspect_weight_share` (share of the strongest reading's step weight, with the
repeat cap, resting on doubted claims), each tested on synthetic data. `manage.py compare_outlets
<chronicle ids>` prints them per instantiated schema after the §1 boundary statement; a second
media fixture, `harbour-fire-herald`, backs the command test. Usage doc: `docs/usage/compare-outlets.md`.
