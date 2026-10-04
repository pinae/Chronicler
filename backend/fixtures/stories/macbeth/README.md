# macbeth

- **Kind:** session
- **Provenance:** adapted from William Shakespeare's *Macbeth* (first performed c. 1606). The play
  is in the public domain; the quoted lines follow its public-domain text. The framing as a
  roleplaying session, the transcript and the beats are our own material.
- **License:** same as this repository.

Shakespeare's tragedy played as a roleplaying session, 36 beats at a table of four players, each
playing a main character: Anna plays Macbeth, Ben Lady Macbeth, Clara Banquo, Dora Macduff. The
game master plays everyone else and shows scenes privately to the players whose characters are in
them. Anna and Ben know the murder of Duncan from the moment it happens (t=17); Clara and Dora only
see its consequences. Everyone at the table learns the truth when the doctor hears Lady Macbeth
confess in her sleep (t=32), and Macduff hears of it (t=33).

Ground truth (`ground_truth.yaml`): a hidden crime, Macbeth kills Duncan, revealed at t=32. A guided
tour through this story is in `docs/usage/guided-tour.md`.

What the full schema library reads in the game master's lattice at the end:

| Reading | Status | Why |
|---|---|---|
| Usurpation: Macbeth, King Duncan, the crown | complete | favour (t=5, 8), ambition (t=6), murder (t=17), crowned (t=22) |
| Prophecy: the witches, Macbeth, the crown / Cawdor | complete | foretold (t=2, 3), fulfilled (t=5, 22) |
| Prophecy: the witches, Fleance, the crown | live | foretold (t=4); the play ends before it comes true |
| Hidden crime: Macbeth, King Duncan, Macduff | complete | crime (t=17), blamed on the grooms (t=20), suspicion (t=29), discovery (t=33) |
| Hidden crime: Macbeth, King Duncan, Banquo | refuted | Banquo is killed (t=26) before he can discover anything |
| Usurpation: Malcolm, King Duncan, the crown | live | Malcolm is favoured and crowned, but neither wanted the crown nor killed for it |
| Betrayal: Macbeth, King Duncan | live | trust (t=8), harm (t=17); the reveal (Duncan learning of it) can never happen |

Players' theories: Dora voices a usurpation by Macbeth (utterance 7) and blames Malcolm for
Duncan's death (utterance 16), later Macbeth for Banquo's (utterance 25); Clara voices that Macbeth
killed Duncan (utterance 19).
