# See the lattice

The lattice shows which narrative patterns (schemas such as **Betrayal**) the chronicle currently
supports, how strongly, and which steps are still open: the stories the audience could be
expecting. A game master uses it to see which twists are set up.

## Before you start
- The app runs (see `docs/usage/browse-chronicles.md`) and the story `steward` has been replayed with
  per-player lattices (`uv run python manage.py replay steward --reader none --per-player`).

## See which stories the chronicle supports
1. Go to **/** and click **The Steward of Wend**.
2. Click **Lattice**.

**Result:** the heading **Lattice of The Steward of Wend** is followed by a section **Betrayal** with a
table of hypotheses, strongest first. The first row reads
**T = Aldric, V = Mira, S = The family seal** with status **complete**; its filled steps include
**harm (t=13)** and **reveal (t=22)**.

## See the lattice before the twist
1. On the lattice page of **The Steward of Wend**, set the slider **Up to beat** to `21`.

**Result:** the slider shows **t = 21 of 24**; the row **T = Aldric, V = Mira, S = The family seal**
now has status **live** and lists **reveal** among its open steps.

## See a player's lattice
1. On the lattice page of **The Steward of Wend**, choose **Anna** in **Seen by**.

**Result:** the table shows only what Anna could have pieced together: there is no row with
**S = The family seal**, because Anna never saw how Aldric learned where the seal was hidden.

## Spot a theory a player voiced
1. On the lattice page of **The Steward of Wend**, set **Up to beat** to `10`.

**Result:** one row reads **T = Aldric, V = ?, S = ? (voiced)**: Anna's guess "I bet the steward is
up to something", kept in the lattice like any other hypothesis.
