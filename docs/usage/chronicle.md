# Read a chronicle

A chronicle's page lists its beats (the formal facts of the story) and lets a game master or writer
see them as any audience saw them, at any point in the story.

## Before you start
- The app runs (see `docs/usage/browse-chronicles.md`) and the story `steward` has been replayed
  (`uv run python manage.py replay steward --reader none`).

## Read a chronicle
1. Go to **/**.
2. Click **The Steward of Wend**.

**Result:** the heading **The Steward of Wend** is shown with the kind **session**. The **Beats** table
lists 24 beats with their **t**, **Predicate** and text, among them **Aldric steals the seal from Mira.**
The slider **Up to beat** shows **t = 24 of 24**, and **Seen by** shows **All beats**.

## Move between the chronicle's screens
1. Go to **/** and click **The Steward of Wend**.

**Result:** below the breadcrumb **All chronicles › The Steward of Wend**, the navigation
**Beats · Lattice · Who knows what · Try a beat** marks **Beats** as the current screen.

2. Click **Lattice** in that navigation.

**Result:** the heading **Lattice of The Steward of Wend** appears and **Lattice** is marked
instead. **All chronicles** leads back to the list.

## See what the table saw
1. On the page of **The Steward of Wend**, choose **The table** in **Seen by**.
2. Set **Up to beat** to `21`.

**Result:** the table keeps **Mira trusts Aldric.** but no longer shows the beats only the game master
or a single player knows, such as **Aldric steals the seal from Mira.** or
**Aldric learns where Mira hides the seal.**

3. Set **Up to beat** to `22`.

**Result:** **Aldric steals the seal from Mira.** appears: at t=22 everyone at the table hears Edda
tell Mira about the theft, so the table now knows that beat, although it happened at t=13.
**Aldric learns where Mira hides the seal.** stays hidden.

## See one player's view
1. On the page of **The Steward of Wend**, choose **Ben** in **Seen by**.

**Result:** the table shows **Aldric learns where Mira hides the seal.** (Ben's private information)
but not **Mira hides the seal in the cellar.** (known only to the game master).

## Go back in time
1. On the page of **The Steward of Wend**, set the slider **Up to beat** to `10`.

**Result:** the slider shows **t = 10 of 24**; the table ends with beat 10, shows
**The raider kills Ronan at the gate.** and no longer shows **Aldric steals the seal from Mira.**

## A chronicle that does not exist
1. Go to **/chronicles/999**.

**Result:** the page says **Chronicle not found**.
