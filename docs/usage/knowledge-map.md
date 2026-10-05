# Read the knowledge map

The knowledge map is the story map's second view: who knew which beat from when. Next to the list
of beats, each player at the table has a narrow column, and every row says whether that player
knew the beat:

- a **filled square**: they knew it when it happened (they were there, or were shown it at once);
- a **hollow square with a fuse**: they learned it later. The fuse burns down from the beat's own
  row to the row of the beat at which they learned it, where it ends in a spark. A long fuse is a
  reveal of the past;
- **nothing**: they never learned it. A row empty in some columns is the game master's secret, or
  dramatic irony when other players know it.

Pointing at a mark shows a tooltip such as **Beat 3, Anna: learned at t = 26 via beat 26**.
The design and its sources are in `docs/research/visualizations.md` (§3).

## Before you start
- The app runs and the example stories have been replayed (see *Before you start* in
  `story-map.md`).

## Open the knowledge map
1. Go to **/** and click **The Broken Jug (an adventure)**.
2. Click **Story map**, then **Knowledge map**.

**Result:** **Knowledge map** is marked in the story map's views (next to **Story river**). A legend
names **Knew it when it happened**, **Learned it later, where the fuse ends** and **Never learned
it**, and beside the beats there are three columns: **Anna**, **Ben** and **Clara**.

## Watch the game master's notes reach the players
1. On the knowledge map of **The Broken Jug (an adventure)**, look at the rows of beats 1 to 3: the
   game master's notes on what happened last night.

**Result:** in every player's column, beat 3 (*Adam breaks Frau Marthe's jug*) burns down to beat
26, when Eve tells Walter that the judge broke the jug, and beat 2 (*Adam threatens Eve*) burns
down to beat 30. Beat 1 (*Judge Adam came to Eve's room*) stays empty: no player ever learns it.
The two fuses are nested; the one that starts later runs inside.

## See who missed a scene
1. On the same knowledge map, look at the rows of beats 19 and 20.

**Result:** only **Ben** has a filled square in row 19 (*Licht suspects the judge*), and nobody has
one in row 20 (*Adam hides that he broke the jug*): Ben plays Licht, whose suspicion was an aside to
the game master, and the judge's cover-up is the game master's alone.

## Show who knew what as a table
1. On the knowledge map, click **Show as table**.

**Result:** the table **Who knew what** has a row per beat with its text and a column per player.
In the row of beat 3, every player's cell says **learned at t = 26 via beat 26**; in the row of
beat 1, **not learned**; in the row of beat 5, **when it happened**.

2. Click **Show as map**.

**Result:** the columns are back.
