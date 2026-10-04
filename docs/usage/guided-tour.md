# Guided tour: Macbeth and The Broken Jug

Two plays you already know, run through the engine, so that you can judge whether it reads them the
way you do. *Macbeth* is played as a roleplaying session in which four players each play a main
character and know their own deeds. Kleist's *The Broken Jug* is played as a pen-and-paper
adventure in which three players investigate a crime that only the game master knows about.

Every scenario below says what to do, what you should see, and why. If what you see differs, either
the software or this tour is wrong; both are worth reporting. The tour needs no language model:
it uses the uniform reader, which gives every possible answer the same probability. The last
section says what changes with a model.

## How to read the screens

- A story is a list of **beats**: formal facts such as "Macbeth kills Duncan", numbered by `t`.
- **Seen by** chooses whose view you look at. **All beats** is the game master's view: every beat.
  A player's view holds the beats that player was shown or heard about, from the moment they
  learned them.
- **Up to beat** turns back time: every screen shows the story as it stood at that beat.
- The **lattice** lists the readings (hypotheses) of the story the engine holds, grouped by schema
  (**Hidden crime**, **Usurpation**, **Prophecy**, **Betrayal**). Each row casts characters in the
  schema's roles:

  | Schema | Roles |
  |---|---|
  | Hidden crime | C = culprit, V = victim, I = investigator who finds out |
  | Usurpation | U = usurper, R = ruler, P = the power taken |
  | Prophecy | S = seer, H = the one the prophecy is about, X = what is foretold |
  | Betrayal | T = traitor, V = victim, S = secret |

  `?` means nobody is cast in that role yet. **Status** is **live** (could still happen),
  **complete** (every required step happened), **refuted** (something made it impossible),
  **pruned** or **merged**. **Weight** grows with every step that is filled; a reading no beat
  supports starts at about -2. **Filled steps** name the beats (by `t`) that fill each step; a beat a
  player learned of later still shows its own `t`. **(voiced)** marks a theory a player said out
  loud.

The **Story map** tab (`story-map.md`) shows much of this tour at a glance: one river of readings
per audience beside the beats, with the game master's secrets hatched. The scenarios below use the
other screens, which show the details.

## Before you start

1. Start the database: `docker compose up -d` in the repository root.
2. In `backend/`, run `uv run python manage.py migrate`.
3. Run `uv run python manage.py load_schemas`.

**Result:** `Loaded 5 schemas: betrayal, blame, hidden_crime, prophecy, usurpation`.

4. Run `uv run python manage.py replay macbeth --reader uniform --per-player`.
5. Run `uv run python manage.py replay broken-jug --reader uniform --per-player`.

**Result:** `Replayed 36 beats of macbeth; run file: …` and `Replayed 32 beats of broken-jug; run
file: …`. `--per-player` builds a lattice for every player besides the game master's. Each replay
adds a new chronicle; if you replay a story twice, the list shows it twice, newest first.

6. Run `uv run python manage.py runserver` (with the frontend built, see `browse-chronicles.md`) and
   go to **/**.

**Result:** the list of chronicles holds **Macbeth (a session)** with **session · 36 beats** and
**The Broken Jug (an adventure)** with **session · 32 beats**.

## Macbeth as a roleplaying session

Anna plays Macbeth, Ben Lady Macbeth, Clara Banquo and Dora Macduff; the game master plays everyone
else and shows scenes privately to the players whose characters are in them
(`backend/fixtures/stories/macbeth/`).

| t | What happens | Who at the table sees it |
|---|---|---|
| 2–4 | the witches hail Macbeth as Thane of Cawdor and king, and foretell that Banquo's son Fleance will be king | Anna, Clara |
| 5 | Duncan makes Macbeth Thane of Cawdor | Anna, Clara |
| 6 | Macbeth wants the crown (an aside) | Anna |
| 8–10 | at court, Duncan trusts Macbeth and Banquo and names Malcolm his heir | everyone |
| 17 | Macbeth kills the sleeping Duncan while his wife keeps watch | Anna, Ben |
| 20 | Macbeth says the grooms killed Duncan | everyone |
| 22 | Macbeth is crowned | everyone |
| 23 | Banquo suspects Macbeth; Clara says "I'm sure Macbeth killed the king himself" | Clara |
| 25–26 | Macbeth sends murderers; they kill Banquo | Anna; Clara |
| 29 | Macduff suspects Macbeth | Dora |
| 32 | the doctor hears Lady Macbeth confess the murder in her sleep | everyone |
| 33 | Macduff learns that Macbeth killed Duncan | everyone |
| 35–36 | Macduff kills Macbeth; Malcolm is crowned | everyone |

### The game master sees the plot lines of the play
1. Click **Macbeth (a session)**, then **Lattice**.

**Result:** under the heading **Lattice of Macbeth (a session)**, with **All beats** in **Seen by**:
- **Usurpation**: the first row, **U = Macbeth, R = King Duncan, P = The crown of Scotland**, is
  **complete**, with **murder (t=17)** and **seizure (t=22)** among its filled steps.
- **Prophecy**: the first row, **S = The three witches, H = Macbeth, X = The crown of Scotland**, is
  **complete**. The row **S = The three witches, H = Fleance, X = The crown of Scotland** is
  **live** with **fulfilment** among its open steps.
- **Hidden crime**: the first row, **C = Macbeth, V = King Duncan, I = Macduff**, is **complete**,
  with **cover_up (t=20)** (blaming the grooms) and **discovery (t=33)**.

**Why:** these are the play's plot lines, read from nothing but the beats. Fleance's prophecy stays
open because the play ends before it comes true; a game master would see a thread left to pick up.

### A dead investigator discovers nothing
1. On the lattice of **Macbeth (a session)**, look at the **Hidden crime** table.

**Result:** the row **C = Macbeth, V = King Duncan, I = Banquo** is **refuted**.

**Why:** Banquo suspected Macbeth (t=23), but the murderers killed him (t=26) before he could find
out. A reading in which he discovers the crime has become impossible.

### Dora does not know of the murder until the doctor's report
1. On the lattice of **Macbeth (a session)**, choose **Dora** in **Seen by**.
2. Set **Up to beat** to `31`.

**Result:** the slider shows **t = 31 of 36**. No row of **Hidden crime** begins with
**C = Macbeth, V = King Duncan**. In **Usurpation**, the row
**U = Macbeth, R = King Duncan, P = The crown of Scotland** is **live** with weight **0.00** and
**murder** among its open steps.

3. Set **Up to beat** to `32`.

**Result:** the same usurpation row now has weight **2.00** and **murder (t=17)** among its filled
steps, and **Hidden crime** has the row **C = Macbeth, V = King Duncan, I = The doctor**, **complete**.

**Why:** Dora saw Macbeth favoured and crowned, but not the murder; to her, Macbeth's rise was
suspicious, not proven. At t=32 she hears the doctor's report, and the murder of t=17 enters her
lattice then. The usurpation still lacks **ambition**: Dora never heard Macbeth's aside at t=6.

### Clara voices what she suspects
1. On the lattice of **Macbeth (a session)**, choose **Clara** in **Seen by**.
2. Set **Up to beat** to `23`.

**Result:** **Hidden crime** has the row **C = Macbeth, V = King Duncan, I = ? (voiced)** with weight
**-2.00** and no filled steps.

3. Set **Up to beat** to `32`.

**Result:** the same row has **crime (t=17)** among its filled steps and weight **-1.00**.

**Why:** Clara's theory is kept like any other reading, but nothing she saw supported it, so it
starts at the schema's prior. At t=32 the confession confirms it.

### Who knows what about the murder
1. On the page of **Macbeth (a session)**, click **Who knows what**.
2. Choose **Dora** in **Who** and set **Up to beat** to `31`.

**Result:** the table **Known beats** does not list
**Macbeth kills the sleeping Duncan while his wife keeps watch.**

3. Set **Up to beat** to `32`.

**Result:** the beat is listed with **learned at t = 32** in the column **How**. Choosing **Ben**
instead lists it with **saw it**: Ben's Lady Macbeth kept watch.

## The Broken Jug as a pen-and-paper adventure

Anna plays Walter, the judicial counsellor inspecting the village court; Ben plays Licht, the
clerk; Clara plays Ruprecht, the accused. The game master plays everyone else, the culprit included
(`backend/fixtures/stories/broken-jug/`).

| t | What happens | Who at the table sees it |
|---|---|---|
| 1–3 | the game master's notes: Judge Adam came to Eve's room, threatened her with a forged letter and broke Frau Marthe's jug fleeing through the window | nobody |
| 4 | Ruprecht believes the man in Eve's room was Lebrecht | Clara |
| 5–8 | the judge has two wounds on his head and no wig; he says he fell out of bed | everyone |
| 14 | Marthe accuses Ruprecht; Anna says "I think the boy did it" (voiced at t=16) | everyone |
| 16 | the judge declares that Ruprecht broke the jug | everyone |
| 18 | Ruprecht says it was Lebrecht; Clara says "Lebrecht broke the jug" | everyone |
| 19 | Licht suspects the judge (an aside); Ben says "The judge broke that jug himself" | Ben |
| 20 | the judge presses Eve to name Ruprecht (the game master notes: he hides his own deed) | nobody |
| 21 | Walter openly distrusts the judge | everyone |
| 22–24 | Brigitte brings the wig from under Eve's window; it is the judge's; Walter concludes he was there | everyone |
| 25 | the judge sentences Ruprecht for breaking the jug | everyone |
| 26–29 | Eve names the judge before the court: Walter, Licht, Ruprecht and Marthe learn who broke the jug | everyone |
| 30 | Walter learns how the judge threatened Eve | everyone |

### The game master knows from the first scene
1. Click **The Broken Jug (an adventure)**, then **Lattice**.
2. Set **Up to beat** to `3`.

**Result:** **Hidden crime** has the rows **C = Judge Adam, V = Frau Marthe, I = ?** and
**C = Judge Adam, V = Eve, I = ?**, both **live**, with **crime (t=3)** and **crime (t=2)**.

**Why:** the game master's notes are beats like any other. The game master's lattice holds the
truth from the start; the investigator is still open, because nobody has found out yet.

### The players start with nothing
1. On the lattice of **The Broken Jug (an adventure)**, choose **Anna** in **Seen by**.
2. Set **Up to beat** to `15`.

**Result:** the page says **No hypotheses at this point**.

3. Set **Up to beat** to `16`.

**Result:** **Hidden crime** has one row, **C = Ruprecht, V = Frau Marthe, I = ? (voiced)**, with
weight **-2.00** and no filled steps.

**Why:** Anna never saw the game master's notes. Her theory that Ruprecht did it is only a claim
she believed; no beat supports it.

### A suspicion said aside stays with the player who said it
1. On the lattice of **The Broken Jug (an adventure)**, choose **Ben** in **Seen by**.
2. Set **Up to beat** to `19`.

**Result:** **Hidden crime** has the rows **C = Judge Adam, V = ?, I = Licht** with
**suspicion (t=19)**, and **C = Judge Adam, V = Frau Marthe, I = ? (voiced)**.

3. Choose **Clara** in **Seen by**.

**Result:** **Hidden crime** has only the row **C = Lebrecht, V = Frau Marthe, I = ? (voiced)**.

**Why:** Licht's suspicion was an aside to the game master, so only Ben's lattice takes it up. It
starts a hidden crime with the judge as culprit and Licht as investigator; whom the judge harmed is
still open.

### Ask what Ben expects the judge to have done
1. On Ben's lattice of **The Broken Jug (an adventure)** at beat `19`, click the **Expectations**
   button in the row **C = Judge Adam, V = ?, I = Licht**.

**Result:** the section **Expectations for C = Judge Adam, V = ?, I = Licht** shows the question
**Next: Judge Adam harms ___.**, **asked at t = 19**, and one line per character Ben has met, among
them **Eve: 13%** and **Frau Marthe: 13%**, and **nothing like this yet: 13%**.

**Why:** this is the question the reader model answers for Ben's seat. The uniform reader spreads
its answer evenly; a language model should put most of it on Frau Marthe (it is her jug) and some
on Eve. This is the place to judge your model.

### The engine connects the judge's accusation with Walter's suspicion
1. On the lattice of **The Broken Jug (an adventure)**, choose **Clara** in **Seen by**.
2. Set **Up to beat** to `25`.

**Result:** **Hidden crime** has the row **C = Judge Adam, V = Frau Marthe, I = Walter** with
**suspicion (t=21, 24)** and **cover_up (t=25)**.

**Why:** Clara never suspected the judge herself, but she saw Walter's suspicion grow (t=21, 24).
When the judge again pins the broken jug on Ruprecht (t=25), the engine reads it as covering up a
harm to Frau Marthe and casts her as the victim. This is the earliest t at which Clara's lattice
holds the truth.

### The confession
1. On the lattice of **The Broken Jug (an adventure)**, choose **Anna** in **Seen by**.
2. Set **Up to beat** to `25`.

**Result:** the row **C = Judge Adam, V = Frau Marthe, I = Walter (voiced)** is **live** with only
**cover_up (t=25)** filled: Anna said at t=24 that she would prove the judge did it.

3. Set **Up to beat** to `26`.

**Result:** the same row is **complete**, with **crime (t=3); cover_up (t=25); discovery (t=26)**.

**Why:** the game master's beat of t=3 reaches Anna's lattice when she hears Eve's confession at
t=26, and it completes her theory together with the discovery itself.

### Who knows what about the jug
1. On the page of **The Broken Jug (an adventure)**, click **Who knows what**.
2. Choose **Anna** in **Who** and set **Up to beat** to `25`.

**Result:** **Known beats** does not list **Adam breaks Frau Marthe's jug as he leaps out of the
window.**

3. Set **Up to beat** to `26`.

**Result:** the beat is listed with **learned at t = 26** in the column **How**.

## Compare the players

`evaluate` measures how early each lattice held the truth of a story's `ground_truth.yaml`
(see `evaluate.md`).

1. In `backend/`, run `uv run python manage.py evaluate macbeth --audience Dora`, and the same for
   `all`, `Anna`, `Ben` and `Clara`.

**Result:** the row **lead time** reads `15 beats (first held at t = 17)` for `all`, `Anna` and
`Ben`, `9 beats (first held at t = 23)` for `Clara` and `0 beats (first held at t = 32)` for
`Dora`.

**Why:** Anna and Ben were there at the murder; Clara guessed it at t=23; Dora only learned it with
everyone else. The lead time is a property of what each player knew, not of the story alone.

2. Run `uv run python manage.py evaluate broken-jug --audience Ben`, and the same for `all`, `Anna`
   and `Clara`.

**Result:** `23 beats (first held at t = 3)` for `all`, `7 beats (first held at t = 19)` for `Ben`,
`2 beats (first held at t = 24)` for `Anna`, `1 beats (first held at t = 25)` for `Clara`.

**Why:** the game master knew from the start; Ben suspected the judge first; Anna named him after
the wig; Clara's lattice made the connection itself at t=25.

## Is it working? A checklist

The engine works as intended if, in both stories:

- the game master's lattice (**All beats**) holds the true reading from the beat of the crime on;
- a player's lattice holds it only once that player saw the crime, guessed it, or heard of it;
- beats only the game master or other players saw never show up in a player's lattice before the
  player learns of them, and then show up with their original `t`;
- voiced theories appear in the speaker's lattice, marked **(voiced)**, even when nothing supports
  them;
- readings that became impossible are **refuted** (Banquo as investigator after his death).

## What the engine does not do yet

You will see these in the two stories; they are known limits, not bugs:

- **Rival theories are not refuted by a confession.** After t=26, Anna's
  **C = Ruprecht, V = Frau Marthe** stays **live**: nothing in the schema contradicts it. Its weight
  (-2.00, nothing filled) is what tells it apart from the truth.
- **Readings that can never complete stay live.** **Betrayal: T = Macbeth, V = King Duncan** waits
  for Duncan to learn of the harm; the engine does not know that the dead learn nothing.
- **One row per possible investigator.** Everyone who hears a confession is a discoverer of the
  crime, so the game master's lattice of *The Broken Jug* ends with complete hidden crimes for Walter,
  Licht, Ruprecht and Frau Marthe.
- **Questions are phrased as "Next: …"**, which fits what lies ahead better than a crime a player
  believes already happened (Clara's theory is asked as **Next: Macbeth harms King Duncan.**).
- **Candidate answers include unlikely ones**, such as **Judge Adam** as the judge's own victim.
- **The beats of these stories are written by hand.** In a live session the ingester drafts them
  from the transcript with a language model (`draft-beats.md`); a beat it gets wrong changes
  everything the engine reads afterwards.

## With your language model

The matcher does not use a language model: the lattice of a story is the same with any reader. The
model answers the expectation questions and the reader rows of `evaluate`.

1. Check the model first: `uv run python -m llm.smoke` (see `ollama-smoke-check.md`).

**Result:** **answer-letter mass, thinking off** is close to 100%. If it is low, the model does not
answer multiple-choice questions with a letter, and the percentages below mean little.

2. Replay with your model: `uv run python manage.py replay broken-jug --reader configured
   --per-player` (it uses `OLLAMA_BASE_URL` and `OLLAMA_READER_MODEL` from `backend/.env`).
3. Open the expectations of Ben's **C = Judge Adam, V = ?, I = Licht** at beat `19` again (see
   *Ask what Ben expects the judge to have done*).

**Result:** the percentages are no longer equal. A useful model puts more on **Frau Marthe**, whose
jug was broken, than on bystanders such as **Walter**.

4. See the raw token probabilities behind them: `uv run python manage.py inspect_readouts
   broken-jug --t 19 --audience Ben` (see `inspect-readouts.md`).

**Result:** the block for **Hidden crime: C = Judge Adam, V = ?, I = Licht** lists the model's first
token, its top alternatives with their probabilities, and the answers read from them, with the share
that fell **outside the letters**.

5. Run `uv run python manage.py evaluate broken-jug`.

**Result:** **retrospective fit**, **largest surprise** and **calibration** now have values. A good
reader finds the clues in the dormant window (fit above 0%: the wig, the judge's wounds and his
eagerness to convict fit "the judge did it" better than its rival), its belief in the truth rises
most at the confession (largest surprise at t = 26), and its answer to "Who broke Frau Marthe's
jug?" at t=23 lies close to the annotated one (calibration near 0). Retrospective fit scores every
dormant-window beat token by token (ADR-009), so the first run takes a few hundred short requests;
re-runs come from the call log.
