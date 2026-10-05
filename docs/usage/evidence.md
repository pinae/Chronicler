# Weigh the evidence

The evidence matrix is the story map's fourth view: every beat set against the competing readings,
as in Heuer's *analysis of competing hypotheses*. Rows are the beats, columns the readings an
audience holds at a chosen beat (strongest first, with their share), followed by those refuted by
then. A cell names the steps the beat filled for that reading, or **refuted**. The last column,
**Evidence**, says what the row is worth:

- **tells them apart**: the beat fills or refutes some readings but not the others. These beats
  carry the plot;
- **fits every reading**: it fills a step of every reading, so it proves nothing about which one is
  true;
- **supports none**: it fills no step of these readings. It sets the scene, or misleads;
- with a single reading, **supports it** or **refutes it**.

A column with no marks is a reading nothing supports, such as a player's theory said out loud. The
design and its sources are in `docs/research/visualizations.md` (§4).

## Before you start
- The app runs and the example stories have been replayed (see *Before you start* in
  `story-map.md`).

## Open the evidence matrix
1. Go to **/** and click **The Broken Jug (an adventure)**.
2. Click **Story map**, then **Evidence**.

**Result:** **Evidence** is marked in the story map's views. **Seen by** is **All beats** and **Up to
beat** is **32**. The table **Evidence seen by All beats** has the columns
**Hidden crime: C = Judge Adam, V = Frau Marthe, I = ? (90%)**,
**Hidden crime: C = Judge Adam, V = Eve, I = ? (10%)**,
**Hidden crime: C = Ruprecht, V = Frau Marthe, I = ? (0%)**,
**Hidden crime: C = Lebrecht, V = Frau Marthe, I = ? (0%)** and **Evidence**.

## Find the beats that carry the plot
1. On the evidence matrix of **The Broken Jug (an adventure)**, look at the rows of beats 14, 19
   and 26.

**Result:**
- Beat 26 (*Walter learns from Eve that the judge broke the jug*) has **discovery** under the judge
  and Frau Marthe and **tells them apart**.
- Beat 19 (*Licht suspects the judge*) has **suspicion** under both of the judge's readings and
  nothing under Ruprecht's and Lebrecht's: it **tells them apart** too.
- Beat 14 (*Marthe accuses Ruprecht of breaking her jug*) **supports none**. The columns of Ruprecht
  and Lebrecht stay empty all the way down: the players' theories were voiced, never supported.

## Look back to an earlier beat
1. On the same matrix, set **Up to beat** to `20`.

**Result:** the table lists beats 1 to 20 only, and the judge's readings head it with their shares
at beat 20: **Hidden crime: C = Judge Adam, V = Frau Marthe, I = ? (68%)** and
**Hidden crime: C = Judge Adam, V = Eve, I = ? (25%)**.

## Weigh a player's evidence
1. Open **Macbeth (a session)**, click **Story map**, then **Evidence**, and choose **Dora** in
   **Seen by**.

**Result:** the table **Evidence seen by Dora** shows what Dora's readings rest on. In the row of
beat 29 (*Macduff suspects Macbeth*), the column **Hidden crime: C = Macbeth, V = The grooms, I = ?
(2%)** says **suspicion, refuted**: one reading of that thread gained a suspicion while another was
refuted. In the row of beat 32 (the doctor's report), **Hidden crime: C = Macbeth, V = King Duncan,
I = ? (30%)** has **crime, discovery**.
