# Try a beat before narrating it

Before you narrate something, you can ask which hypotheses it would start, strengthen, complete or
refute. The beat is tried as if it were the next beat of the chronicle and then thrown away:
nothing you try is kept, and no language model is asked.

## Before you start
- The app runs (see `docs/usage/browse-chronicles.md`) and the story `steward` has been replayed
  (`uv run python manage.py replay steward --reader uniform --per-player`).

## Open the form
1. Open **The Steward of Wend** from the list of chronicles.
2. Click **Try a beat**.

**Result:** the heading **Try a beat in The Steward of Wend** appears above a form with a
**Predicate** choice, the groups **Present** (the characters) and **Shown to** (the players, all
ticked), a **Lattice of** choice and the button **Try it**.

## A beat that starts a new suspicion
1. On the form of **The Steward of Wend**, choose **trusts** in **Predicate**.
2. Choose **Edda** in **who** and **Mira** in **whom**.
3. Click **Try it**.

**Result:** the heading **If this were beat 25** appears above the table **Effects**, which has the row
**Betrayal: T = Mira, V = Edda, S = ?** with the change **seeded (trust)** and the weight **new: -1.5**.

## A beat that strengthens a suspicion
1. On the form of **The Steward of Wend**, choose **helps** in **Predicate**.
2. Choose **Mira** in **who** and **Aldric** in **whom**.
3. Click **Try it**.

**Result:** the table **Effects** has the row **Betrayal: T = Mira, V = Aldric, S = ?** with the change
**filled trust** and the weight **-1.5 → -1.0**.

## A beat that refutes a suspicion
1. On the form of **The Steward of Wend**, choose **kills** in **Predicate**.
2. Choose **The raider** in **who** and **Mira** in **whom**.
3. Click **Try it**.

**Result:** the table **Effects** has the row **Betrayal: T = Mira, V = Aldric, S = ?** with the change
**refuted**: a dead traitor cannot betray anyone any more.

## A player's lattice only changes if the player sees the beat
1. On the form of **The Steward of Wend**, choose **helps** in **Predicate**, **Mira** in **who** and
   **Aldric** in **whom**.
2. Untick **Anna** in **Shown to** and choose **Anna** in **Lattice of**.
3. Click **Try it**.

**Result:** the page says **No hypothesis would change.** Ticking **Anna** again and clicking
**Try it** shows the row **Betrayal: T = Mira, V = Aldric, S = ?** with **filled trust**.

## A beat with a missing role
1. On the form of **The Steward of Wend**, choose **steals** in **Predicate** and **Aldric** in **who**.
2. Click **Try it**.

**Result:** the page says **steals: missing role 'from'**.

## Nothing you try is kept
1. Try any beat on the form of **The Steward of Wend**.
2. Click **Beats of The Steward of Wend**.

**Result:** the chronicle still ends at beat 24 (**t = 24 of 24**).
