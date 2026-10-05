# Check the clues

The clue ledger is the story map's fifth view. It applies the Three Clue Rule ("for any conclusion
you want the players to reach, include at least three clues"): for one of the game master's
readings, it lists the beats that filled the reading's steps (its clues) and, for every player, how
they came to know each one. The footer counts, per player, the clues they knew before the reading
paid off (before the first beat that filled a step of its payoff phase, such as **discovery**):

- **knew it from the start**: the player saw the reading's first clue happen, so they never needed
  to deduce it (typically, they took part in the crime);
- **N of M**: they knew N of the M clues before the payoff;
- **N of M: fewer than three** (highlighted): the payoff came with fewer than three clues behind it
  for that player. Expect them to be surprised, or to feel cheated.

While a reading has not paid off yet, the footer says **Clues so far** and counts what each player
knows now. Steps still open are listed below the table. The design and its sources are in
`docs/research/visualizations.md` (§5).

## Before you start
- The app runs and the example stories have been replayed (see *Before you start* in
  `story-map.md`).

## Open the clue ledger
1. Go to **/** and click **The Broken Jug (an adventure)**.
2. Click **Story map**, then **Clues**.

**Result:** **Clues** is marked in the story map's views, and **Reading** shows the game master's
strongest reading at the last beat, **Hidden crime: C = Judge Adam, V = Frau Marthe, I = ?**. The
table **Clues to Hidden crime: C = Judge Adam, V = Frau Marthe, I = ?** lists its clues from beat 3
(**crime**, which every player **learned at t = 26 via beat 26**) to beat 29, the steps of beats 26
to 29 marked **discovery (payoff)**.

## See whether the players were prepared
1. Look at the footer of the same table.

**Result:** **Clues before the payoff at t = 26**: **Anna** knew **4 of 7**, **Ben** **5 of 7**
(he alone saw Licht's suspicion at beat 19) and **Clara** **4 of 7**. The confession was well
prepared for everyone.

## Find a player who was not
1. Open **Macbeth (a session)**, click **Story map**, then **Clues**.
2. Choose **Hidden crime: C = Macbeth, V = King Duncan, I = ?** in **Reading**.

**Result:** the footer says **Clues before the payoff at t = 32**: **Anna** and **Ben** **knew it
from the start** (they played the murder at beat 17), while **Clara** and **Dora** each had
**2 of 4: fewer than three**. The doctor's report at beat 32 is the twist that surprises them most
(compare `pacing.md`).
