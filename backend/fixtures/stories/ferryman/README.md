# ferryman

- **Kind:** literature (a narrator, no players: the implicit player reads everything)
- **Provenance:** written for the evaluation harness (WP-043); our own material.
- **License:** same as this repository.

A betrayal with a red herring, 18 beats in five short chapters. Oskar the ferryman trusts his
apprentice Tilde and, reluctantly, his rival Bram. He hides the key to his ledger box; Tilde sees
where. Bram asks about the key, is seen at the boathouse and is blamed, but it is Tilde who steals
the key and sells it to a stranger. When the harbour watch catches the stranger, he tells Oskar
(t=17, the reveal).

What the story is built to show:

| t | event |
|---|---|
| 2, 4 | seeding: betrayals of Oskar by Tilde and by Bram |
| 5, 9 | both suspects help Oskar (trust fills) |
| 7 | refinement: Tilde's betrayal gains the key |
| 8, 10, 13, 15 | the red herring: beats about Bram that no betrayal step matches |
| 11, 12 | harm and benefit fill Tilde's betrayal only |
| 17 | completion: Oskar learns of the theft at the reveal |

Ground truth: `ground_truth.yaml` (twist recall at k = 5 is asserted in
`evaluation/tests/test_evaluation_stories.py`).
