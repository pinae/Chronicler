# broken-jug

- **Kind:** session
- **Provenance:** adapted from Heinrich von Kleist's comedy *Der zerbrochne Krug* (*The Broken
  Jug*, first performed 1808), which is in the public domain. The framing as a pen-and-paper
  adventure, the English transcript and the beats are our own material.
- **License:** same as this repository.

Kleist's comedy played as a pen-and-paper adventure, 32 beats at a table of three players: Anna
plays Walter, the judicial counsellor inspecting the village court; Ben plays Licht, the clerk;
Clara plays Ruprecht, the accused. The game master plays everyone else, the culprit included. The
adventure opens with the game master's notes (t=1 to 3, shown to no player): last night Judge Adam
threatened Eve with a forged letter and broke Frau Marthe's jug fleeing through the window. The
players have to find out what the game master knows from the start, while Adam judges the case.

Ground truth (`ground_truth.yaml`): a hidden crime, Adam breaks Marthe's jug, revealed at t=26 when
Eve names him before the court. A guided tour through this story is in `docs/usage/guided-tour.md`.

What the story is built to show:

| t | event |
|---|---|
| 3 | the game master's lattice holds the truth from the first scene: Hidden crime, C = Judge Adam, V = Frau Marthe |
| 16 | Anna voices the obvious theory, Ruprecht did it (a hidden crime no beat supports) |
| 18 | Clara, who believes she saw Lebrecht, voices that he did it |
| 19 | Ben's private suspicion of the judge starts a reading in his lattice only; he voices that the judge did it |
| 21, 24 | Walter's suspicion (Anna's, said openly) starts the same reading in every player's lattice |
| 25 | the judge blames Ruprecht again; in Clara's lattice this binds the victim, Frau Marthe |
| 26 | Eve's confession: the GM-only crime of t=3 enters every player's lattice, which completes |
| 30 | Walter also learns how Adam threatened Eve: a second hidden crime completes |
