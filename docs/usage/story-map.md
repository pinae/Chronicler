# Read the story map

The story map shows every story the engine reads in a chronicle, beat by beat, for the game master
and for each player side by side. Next to the list of beats, each audience has a *river*: every
reading it holds is a band, and the wider the band at a beat, the more of the engine's belief that
reading holds there. The design and its sources are in `docs/research/visualizations.md`.

How to read it:
- **Colour** is the schema (the legend names them); grey is all other readings together.
- **Width** is the reading's share: the plausibility `exp(weight)` of the reading against all
  readings held at that beat, so the shares of a row add up to the whole column.
- A reading and the more specific readings refined from it share one band, named by the reading it
  started as.
- **Hatching** (game master's column) marks what no player holds yet: the game master's secrets.
- **Marks** on a band: a dot where a beat fills a step, a star where the reading completes, a cross
  where it is refuted, a diamond where a player voices it.
- **Arcs** (between the beats and the rivers, once you click a band): the beats that filled the
  thread's steps, each joined to the next; a dashed line below the last one names the required
  steps still to come.

## Before you start
- The app runs (see `browse-chronicles.md`) and the example stories have been replayed with player
  lattices (`uv run python manage.py replay broken-jug --reader uniform --per-player`, the same for
  `macbeth`; see `guided-tour.md`).

## Open the story map
1. Go to **/** and click **The Broken Jug (an adventure)**.
2. Click **Story map**.

**Result:** the heading **Story map of The Broken Jug (an adventure)** appears above a legend
(**Hidden crime**, **Other readings**, **Only the game master holds it** and the marks), the list of
beats and four rivers headed **All beats**, **Anna**, **Ben** and **Clara**. **Story map** is marked
in the chronicle's navigation, and **Story river** in the story map's views; the other views,
**Knowledge map**, **Pacing**, **Evidence** and **Clues**, are described in `knowledge-map.md`,
`pacing.md`, `evidence.md` and `clues.md`.

## See what only the game master knows
1. On the story map of **The Broken Jug (an adventure)**, look at the **All beats** column.

**Result:** the big band is hatched from beat 3 to beat 18 and plain from beat 19 on: the game
master's notes (beats 1–3) say that the judge broke the jug, and no player holds that reading until
Ben voices it after beat 19.

2. Click **Show as table**.

**Result:** the table **Shares seen by All beats** shows, in the column
**Hidden crime: C = Judge Adam, V = Frau Marthe, I = ?**, a share marked **(secret)** in the rows of
beats 3 to 18, and shares without the mark from beat 19 on.

## Read a band
1. On the story map of **The Broken Jug (an adventure)**, point at the middle of the **All beats**
   column in the row of beat 20.

**Result:** a tooltip shows the share first (for example **68% at t = 20**), then the reading
**Hidden crime: C = Judge Adam, V = Frau Marthe, I = ?**, its status **live**, and what happened to
it at this beat (**This beat: cover_up filled**).

## Compare the players
1. Point at the same band as in *Read a band*.

**Result:** in every column, the bands that could be the same story (the same schema, and the same
characters wherever both cast a role) stay bright; the others fade. In **Anna**'s column, her own
theory **C = Ruprecht** fades, while Walter's suspicion of the judge stays bright.

## See a thread's steps
1. On the story map of **The Broken Jug (an adventure)**, click the middle of the **All beats**
   column in the row of beat 20 (the band of *Read a band*).

**Result:** next to the beats, the arcs **Steps of Hidden crime: C = Judge Adam, V = Frau Marthe,
I = ? (All beats)** join the beats that filled the reading's steps: **crime** at beat 3,
**cover_up** at beat 16, **suspicion** at beat 19 and so on down to **discovery** at beat 29. The
bands that could be the same story stay bright in every column, as in *Compare the players*.

2. Press **Escape** (or click the band again).

**Result:** the arcs are gone and the lane says **Click a band to see its steps**.

## List the open threads
1. Open **Macbeth (a session)** and click **Story map**.
2. Look at **Open threads** below the rivers.

**Result:** **Open threads seen by** is set to **All beats**, and the list names every reading of
the game master's column whose required steps are not all filled, the longest waiting first. The
first is **Prophecy: S = The three witches, H = Fleance, X = The crown of Scotland · open:
fulfilment · waiting since t = 4**: the witches' promise to Banquo's son is still a loaded gun.

3. Click **Prophecy: S = The three witches, H = Fleance, X = The crown of Scotland**.

**Result:** the arcs show its one filled step, **foretelling** at beat 4, and a dashed line down to
the last beat labelled **to come: fulfilment**.

4. Open **The Broken Jug (an adventure)**, click **Story map** and choose **Anna** in **Open threads
   seen by**.

**Result:** the list **Open threads seen by Anna** holds **Hidden crime: C = Ruprecht, V = Frau
Marthe, I = ? · open: crime, discovery · no beat supports it yet**: Anna's theory, which no beat has
backed.

## Show the river as a table
1. On the story map, click **Show as table**.

**Result:** one table per audience (**Shares seen by All beats**, **Shares seen by Anna**, …) with a
row per beat and a column per reading, holding the same shares as the river.

2. Click **Show as river**.

**Result:** the rivers are back.

## Watch a twist reach a player
1. Open **Macbeth (a session)** and click **Story map**.
2. Click **Show as table**.

**Result:** in the table **Shares seen by Dora**, the column
**Hidden crime: C = Macbeth, V = King Duncan, I = ?** is empty up to beat 31 and holds a share from
beat 32 on: Dora hears of the murder only from the doctor's report. In the river, the blue band in
Dora's column begins at that row.
