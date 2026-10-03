# See who knows what

Characters and players learn different things at different times. The knowledge screen answers
"what does this character (or this player) know at beat t?" and says how each beat became known:
by being there, or through a later beat in which they learned of it.

## Before you start
- The app runs (see `docs/usage/browse-chronicles.md`) and the story `steward` has been replayed
  (`uv run python manage.py replay steward --reader uniform --per-player`).

## Open the knowledge screen
1. Open **The Steward of Wend** from the list of chronicles.
2. Click **Who knows what**.

**Result:** the heading **Who knows what in The Steward of Wend** appears with a **Who** choice, the
**Up to beat** slider and the prompt **Choose a character or a player.**

## What a character witnessed
1. On the knowledge screen of **The Steward of Wend**, choose **Mira** in **Who**.

**Result:** the table **Known beats** lists **Mira trusts Aldric.** with **present** in the column
**How**: Mira was there when it happened.

## A character learns a secret later
1. On the knowledge screen of **The Steward of Wend**, choose **Mira** in **Who**.
2. Set **Up to beat** to `21`.
3. Set **Up to beat** to `22`.

**Result:** at beat 21 **Aldric steals the seal from Mira.** is not in the table **Known beats**.
At beat 22 it is, with **learned at t = 22** in the column **How**: Edda told her.

## What a player was shown
1. On the knowledge screen of **The Steward of Wend**, choose **Ben** in **Who**.

**Result:** the table **Known beats** lists **Aldric learns where Mira hides the seal.** with
**saw it** in the column **How**: the game master showed it to Ben privately. Choosing **Anna**
instead does not list this beat.
