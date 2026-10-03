# steward

- **Kind:** session
- **Provenance:** written for the test suite (WP-020); our own material.
- **License:** same as this repository.

A betrayal at the court of Wend, 24 beats at a table of two players (Anna, Ben). Lady Mira trusts
her steward Aldric and her captain Ronan; Edda the maid helps her. Mira hides the family seal and a
ledger in the cellar. Aldric learns where the seal is hidden and steals it at night; the raider who
pays him kills Ronan at the gate. Edda, who knows where the ledger is, slaps Mira in public. At t=22
Edda tells Mira that she saw Aldric take the seal (the reveal); at t=24 the raider kills Aldric.

Matcher events the story is built to exercise (with `MATCHER_MAX_LIVE_PER_SCHEMA = 4`):

| t | event |
|---|---|
| 2, 3, 4, 11 | seeding: betrayals by Aldric, Ronan, Edda, and of Aldric by Mira |
| 7, 10 | refinement: Aldric's and Edda's betrayals gain the secret (seal, ledger) |
| 9 | refutation by contradiction: Ronan is killed before any harm |
| 11 | pruning: five live betrayals, the newest weakest is pruned |
| 14 | refutation by constraint: Mira witnesses Edda's harm before any reveal |
| 22 | completion: Mira learns of the theft at the reveal |
| 24 | refutation by contradiction: Aldric is killed (the hypothesis without the seal) |
