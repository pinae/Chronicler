# Seeing the story: visualizations for the game master

What would help a game master (or writer) see what the engine sees, and how a story is built and
moves? This note starts from the questions a game master asks during a session, looks at what
visualization research and roleplaying practice offer for each, and proposes views. The proposals
are ordered by what they cost and what they answer; the first ones are built in WP-067 to WP-069.

## The questions

| # | The game master asks | Data the engine already has |
|---|---|---|
| Q1 | Which stories are in play right now, and how strongly? Which are rising, which fading? | the lattice at every t: readings, weights, status |
| Q2 | What does each player believe, and what do I know that they don't? | one lattice per player; the scope of every beat |
| Q3 | Which threads did I set up and not pay off yet? | the steps of each reading, filled or open |
| Q4 | Which beats carry the plot, and which tell the readings apart? | which beat filled which step; refutations |
| Q5 | Have the players had enough clues to reach the conclusion I want? | the steps of a reading seen by each player |
| Q6 | How tense is it? Where did the table get surprised? | expectations per t; reader beliefs (with a model) |
| Q7 | Who was where, with whom? | `present` of every beat |
| Q8 | When did each player learn what, compared with when it happened? | scope grants with `known_since_t` and `learned_via` |

## What the research and practice offer

- **ThemeRiver and streamgraphs.** Themes as bands flowing along a time axis, width proportional
  to their strength at each moment ([Havre, Hetzler & Nowell, InfoVis 2000](https://ieeexplore.ieee.org/document/885098));
  Byron and Wattenberg analyse the trade-offs of the baseline: a centred, wiggling baseline looks
  organic, a straight one is easier to read ([Stacked Graphs – Geometry & Aesthetics, 2008](https://leebyron.com/streamgraph/stackedgraphs_byron_wattenberg.pdf)).
  Ordering the bands by first appearance keeps them from jumping around
  ([Di Bartolomeo & Hu, 2016](https://onlinelibrary.wiley.com/doi/10.1111/cgf.12910)).
- **Arc diagrams.** Items on one axis, arcs between related positions; Wattenberg's *Shape of Song*
  makes the repetitions of a piece visible at a glance
  ([Arc Diagrams: Visualizing Structure in Strings, 2002](https://www.researchgate.net/publication/4000926_Arc_Diagrams_Visualizing_Structure_in_Strings),
  [The Shape of Song](https://www.bewitched.com/song.html)). A story's setups and payoffs are the
  same kind of long-range structure.
- **Storyline charts.** One line per character along time; lines run together while characters
  share a scene, as in XKCD's movie narrative charts
  ([Tanahashi & Ma, 2012](https://www.researchgate.net/publication/260582986_Design_Considerations_for_Optimizing_Storyline_Visualizations),
  [StoryFlow, Liu et al. 2013](https://www.researchgate.net/publication/256837272_StoryFlow_Tracking_the_Evolution_of_Stories)).
  Their difficulty is the layout (crossings); good layouts need optimisation.
- **Story curves.** Narrative order on one axis, story order on the other: a straight diagonal for
  a linear story, jumps for flashbacks; lay readers learn to read it in a few minutes
  ([Kim et al., InfoVis 2017](https://vcg.seas.harvard.edu/publications/20180101-visualizing-nonlinear-narratives-with-story-curves/paper)).
  In a session, "when the player learned it" against "when it happened" is the same picture.
- **Analysis of Competing Hypotheses.** Heuer's matrix puts evidence in rows and hypotheses in
  columns, marks each cell consistent or inconsistent, and asks the analyst to work *across* rows:
  evidence that fits every hypothesis is not diagnostic
  ([Analysis of competing hypotheses](https://en.wikipedia.org/wiki/Analysis_of_competing_hypotheses)).
  The engine's lattice is exactly such a set of competing hypotheses.
- **Suspense and surprise.** Ely, Frankel and Kamenica define suspense as the expected size of the
  next belief change and surprise as the size of the actual change
  ([Suspense and Surprise, JPE 2015](https://www.journals.uchicago.edu/doi/abs/10.1086/677350)).
  Both can be computed from the engine's numbers.
- **The Three Clue Rule.** "For any conclusion you want the PCs to make, include at least three
  clues"; game masters keep a *revelation list* of conclusions and the clues pointing to each
  ([The Alexandrian: node-based scenario design](https://thealexandrian.net/wordpress/7985/roleplaying-games/node-based-scenario-design-part-3-inverting-the-three-clue-rule)).
  A reading's steps are its clues; the engine knows which of them each player has seen.

## Shared design rules

- **One time axis for every view: the beats, top to bottom**, aligned row by row with the beat
  list. Reading a row across shows everything about one moment; the beat text is always next to
  the picture. (Vertical, because beat texts are lines of text and lists scroll vertically.)
- **Colour means schema** (Betrayal, Hidden crime, Usurpation, Prophecy, Blame): one categorical
  palette, assigned in a fixed order and the same in every view, validated for colour-vision
  deficiency. Several readings of one schema share its colour and are told apart by gaps,
  position and labels.
- **Texture means secret**: diagonal hatching marks what only the game master holds. It works
  without colour, in print and in forced-colours mode.
- **Every chart has a table view** with the same numbers, and a tooltip on every mark.
- **Width means plausibility.** The lattice weight is a log-score (prior plus the weights of the
  filled steps), so `exp(weight)` is read as unnormalised plausibility and divided by the sum
  over the readings held at that beat. A reading's *share* is "how much of the engine's belief it
  holds now". This is a modelling choice: the weights are hand-set, not calibrated
  probabilities. With a language model the reader's belief ("Is the story X?") could replace it.

## The proposals

### 1. Story river (Q1, Q2) — the owner's idea, worked out

Next to the beat list, one column per audience (game master, then each player). In each column,
every reading the engine holds is a band whose width at a beat is its share; the bands of one
moment fill the column like a 100 % stacked bar, and flow smoothly from beat to beat.

```
 t  beat                                   GM            Anna     Ben      Clara    Dora
 16 Lady Macbeth drugs the grooms.        ▓▓▓██░░░▒▒▒   ███░░    ███░     ██░░     ░░░
 17 Macbeth kills the sleeping Duncan.    ▓▓▓▓███░░▒▒   ████░    ████░    ██░░     ░░░
 18 Duncan is found murdered.             ▓▓▓▓███░░▒▒   ████░    ████░    ██░░     ░░░
        ▓ = hatched: only the GM holds this reading   █ ░ ▒ = schema colours
```

- **Thread identity.** A reading that gets more specific (the engine *refines* "someone killed
  Duncan" into "Macbeth killed Duncan, Macduff will find out") keeps its band: a band is a
  reading together with its refinements, labelled with its strongest member.
- **At most seven bands per column**, the seven that are strongest at some beat; the rest form one
  grey "other" band. Bands keep the order of their first appearance, so they do not jump.
- **Secret** (game master's column): hatched where no player holds the same reading. The hatching
  ends at the beat at which the first player learns enough to hold it; dramatic irony becomes a
  visible region.
- **Events on the band**: a dot where a beat fills a step, a star where the reading completes, a
  cross where it is refuted, a diamond where a player voices it.
- The owner's alternative, one river with patterns for readings only some players hold, is the
  same data drawn denser; the columns are easier to compare (small multiples share one scale),
  and the hatching keeps the one fact the overlay was for: what the players do not know.

Answers at a glance: which stories dominate, when a twist lands (bands swap width), who is behind.

### 2. Thread arcs (Q3, Q4)

Selecting a band draws its reading's arcs over the beat axis: an arc from the beat that filled
one step to the beat that filled the next, labelled with the step names, open steps as a dashed
arc to the bottom ("still to come"). Setups and payoffs, and how far apart they are, become a
shape — the *Shape of Song* for a plot. A list beside it names the open steps of every live
reading, oldest setup first: the game master's list of loaded guns.

### 3. Knowledge map (Q2, Q8)

The same rows, one narrow column per audience (and optionally per main character). A filled cell
means the audience knew the beat from that row on; a beat learned later is drawn as a fuse: a thin
line from the row where it happened down to the row where it was learned, then filled. Rows with
a filled game-master cell and empty player cells are dramatic irony; long fuses are reveals of the
past (the Broken Jug's game-master notes burn down to beat 26). This is the story curve of a
session, drawn in the shared layout.

### 4. Evidence matrix (Q4)

Heuer's matrix with the engine's data: rows are beats, columns the strongest readings at a chosen
beat, a cell marks the step a beat filled (or a cross where it refuted the reading). Rows that
support one reading and not its rivals are the diagnostic beats; rows that fill nothing are
colour or misdirection (the coverage metric, made visible).

### 5. Clue ledger (Q5)

For one reading (typically the twist the game master is building towards), a grid of its steps
against the players: which steps each player has seen, and since when. The Three Clue Rule as a
check: if no player has seen two of the three setups, the reveal will fall flat.

### 6. Tension and surprise strip (Q6)

A narrow column of horizontal bars beside the beat list:
- **surprise** at a beat: how much the readings' shares moved from the previous beat (half the sum
  of absolute share changes, between 0 and 1). Large at twists and reveals, computable without a
  language model;
- **tension**: the share held by readings that have set up their payoff but not reached it
  (development steps filled, payoff open); a rough Freytag curve;
- **suspense** (with a model): the uncertainty of the expectations at that beat — how spread the
  reader's answers are, following Ely, Frankel and Kamenica.

### 7. Storyline (Q7)

Characters as lines along the beats, running together while they are present in the same beats,
apart otherwise, in the XKCD style. Rich and good for preparing a session, but it needs a layout
algorithm that keeps crossings low; worth building once the other views exist.

### 8. Reading genealogy (debugging)

An alluvial chart of how readings were born, refined, merged, completed and refuted. It answers
"why does the engine hold this?" and is mainly a developer's tool.

## Recommendation and order

| Order | View | Cost | Why first |
|---|---|---|---|
| 1 | Story river with per-player columns, hatching and events | backend timeline + one chart | the owner's idea; answers Q1 and Q2 |
| 2 | Thread arcs on selection, open-steps list | small; reuses the river's data | makes the structure of one plot visible |
| 3 | Knowledge map | small backend addition + one chart | dramatic irony and reveals, the heart of a session |
| 4 | Tension and surprise strip | computed from the river's shares | a quick read of pacing |
| 5 | Evidence matrix, clue ledger | tables with marks | preparing and checking a mystery |
| 6 | Storyline, genealogy | layout work | later |

All views share the beat list on the left and the time axis, so they become tabs of one screen,
the **story map**, rather than separate pages.
