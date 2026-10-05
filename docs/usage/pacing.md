# Read the pacing

The pacing is the story map's third view: how each beat moved each audience. Next to the list of
beats, every audience (the game master's **All beats** and each player) has a column with two
measures, both from nothing at the column's left edge to all of the engine's belief at its right
(the dashed line marks half):

- **Tension** (the shaded area): how much of the belief rests on stories that are building up, with
  a development step filled and the payoff still open. It rises while a plot thickens and falls
  when it pays off: a rough Freytag curve.
- **Surprise** (the bar in a beat's row): how much of the belief moved at that beat, half the summed
  change of every reading's share. Twists and reveals have long bars; the first readings an
  audience holds surprise nobody.

Both are read from the readings' shares, as in the story river (`story-map.md`); with a language
model the reader's beliefs could refine them. Pointing at a row shows a tooltip such as
**t = 26, Anna: surprise 59%, tension 7%**. The design and its sources (Ely, Frankel and Kamenica's
suspense and surprise) are in `docs/research/visualizations.md` (§6).

## Before you start
- The app runs and the example stories have been replayed (see *Before you start* in
  `story-map.md`).

## Open the pacing
1. Go to **/** and click **The Broken Jug (an adventure)**.
2. Click **Story map**, then **Pacing**.

**Result:** **Pacing** is marked in the story map's views. A legend names **Tension: belief in
stories building towards a payoff** and **Surprise: how much belief moved at this beat**, and beside
the beats there are four columns: **All beats**, **Anna**, **Ben** and **Clara**.

## Feel the confession
1. On the pacing of **The Broken Jug (an adventure)**, look at the rows of beats 21 to 26.

**Result:** in every player's column the tension swells from beat 21, when Walter starts to
distrust the judge, to beat 25, when the judge sentences Ruprecht, and collapses at beat 26, when
Eve names the judge; beat 26 has a long surprise bar in every column.

2. Click **Show as table**.

**Result:** the table **Pacing** has, per beat, a surprise and a tension column for every audience.
In the row of beat 25, the tension of every player is above 80% (**Ben: tension** is **100%**); in
the row of beat 26, it is below 10%, and every player's surprise is above 30%.

## See a twist reach one player
1. Open **Macbeth (a session)**, click **Story map**, then **Pacing**, then **Show as table**.

**Result:** in the row of beat 32 (*The doctor hears Lady Macbeth confess the murder of Duncan in
her sleep*), **Dora: surprise** is above 30% while **All beats: surprise** is below 10%: the murder
was no news to the game master, but Dora learns of it only now.

## Show the pacing as a chart again
1. On the table, click **Show as chart**.

**Result:** the columns are back.
