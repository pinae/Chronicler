# See what the audience expects next

For each hypothesis in the lattice, the reader model is asked after every beat which entity the
audience expects to fill the hypothesis' next open step. These expectations are what a game master
plans twists around.

## Before you start
- The app runs (see `docs/usage/browse-chronicles.md`) and the story `steward` has been replayed with
  readouts (`uv run python manage.py replay steward --reader uniform --per-player`, or `--reader
  configured` with a language model).

## See what the audience expects next
1. Open the lattice of **The Steward of Wend** (see `docs/usage/lattice.md`) and set **Up to beat** to
   `10`.
2. Click the **Expectations** button in the row **T = Aldric, V = ?, S = ? (voiced)**.

**Result:** a section **Expectations for T = Aldric, V = ?, S = ?** appears below the lattice with the
question **Next: ___ trusts Aldric.**, the note **asked at t = 10**, and one line per candidate with
its probability, from **Mira: 17%** to **nothing like this yet: 17%**. (With the uniform reader every
candidate gets the same share; a language model gives real probabilities.)

## A hypothesis nobody was asked about
1. On the lattice of **The Steward of Wend** (at the last beat), click the **Expectations** button in
   the row **T = Aldric, V = Mira, S = The family seal**.

**Result:** the section **Expectations for T = Aldric, V = Mira, S = The family seal** says
**No expectations yet**: the hypothesis rests on beats the table never saw, so the table was never
asked about it.
