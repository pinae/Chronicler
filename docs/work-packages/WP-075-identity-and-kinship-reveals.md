# WP-075: Identity and kinship reveals

**Milestone:** M3 (follow-up) · **Serves:** RQ1, RQ3

## Goal
Two classic kinds of twist need facts the vocabulary could not state: that the person known as A
is really B (Keyser Söze, Tyler Durden, the twins of *The Prestige*, Odysseus as a beggar), and that
two characters are kin (Oedipus and Laius, Vader and Luke). Two predicates state these facts, and
two schemas read the twists that reveal them.

## Acceptance criteria
- The vocabulary has `poses_as(who, whom)`: the person `who` appears as, or hides behind, `whom`;
  and `kin(who, whom, as?)`: `who` is related to `whom`, `as` names how (`father`). Both have a
  sentence template for readout questions. The concept's starter predicates stay.
- `identity_reveal`: a disguise (`poses_as`) seeds a reading; it completes when someone other than
  the persona learns of the disguise, as a beat or a proposition, or recognises the persona by a
  token the person behind it has (Odysseus' scar).
- `hidden_kinship`: a kinship fact seeds a reading; clashes between the two (opposes, harms,
  kills) develop it; it completes when someone learns of the kinship. Learning of a kinship nobody
  stated before (Vader's "I am your father") seeds and completes a reading at once.
- A beat that could refine several readings refines the most specific one (most roles bound, then
  most fills), so the recognition by a token goes to the reading that knows the token.
- ADR-013 records why the vocabulary grows by these two predicates.

## Dependencies
WP-005, WP-074.

## Out of scope
Merging two entities into one when an identity is revealed (the chronicle keeps both, linked by the
`poses_as` beat). Example stories with these twists.

## Status
done

## Summary
`poses_as` and `kin` joined the vocabulary and the readout templates (ADR-013); the vocabulary test
now checks that the concept's starter predicates are contained rather than equal to the whole set.
`identity_reveal` and `hidden_kinship` start at −1.5 (prior −2.5): unlike the other twists their
seeds are rare. Writing the recognition by a token showed that `refine` gave a beat to the oldest
of several readings it could refine, not the best supported; it now prefers the most specific one,
which changed no other test and nothing in the example stories.
