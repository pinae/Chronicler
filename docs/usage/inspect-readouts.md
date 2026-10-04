# Inspect what the reader model answered

Every expectation the engine shows is read from the probabilities of the language model's first
token. `inspect_readouts` shows those raw numbers for one beat: the question, how long the prompt
was, which token the model produced, its top alternatives with their probabilities, and the answer
distribution the engine read from them. Use it to check that the model really answers the questions
and to compare models.

## Before you start
- The backend is installed and migrated, and a story has been replayed with a reader, e.g.
  `uv run python manage.py replay steward --reader configured --per-player` (with the language model
  from `backend/.env`) or `--reader uniform` (without one).

## Inspect the table's readouts at a beat
1. In `backend/`, run `uv run python manage.py inspect_readouts steward --t 16`.

**Result:** the first line reads `Readouts at t=16 for the table (steward, chronicle 7)` (with the
id of the newest replay of `steward`). For each question asked at that beat, a block such as

```
Betrayal: T = Aldric, V = Mira, S = ?
  Next: Aldric harms Mira.
  model gemma4:e4b · prompt 812 tokens · first token "A"
  first-token alternatives: "A" 71.3% · "B" 22.0% · " A" 3.1% · "The" 1.2% · …
  answers: A) this happens next 77.6% · B) nothing like this yet 22.4% · outside the letters 3.6%
```

**first-token alternatives** are the model's own probabilities for its first token, at most 20 of
them. **answers** adds up the spellings of each letter (`A`, ` A`, `A)`) and renormalizes over the
letters; **outside the letters** is the probability that went to anything else. A large outside
share means the model did not take the question as a multiple-choice question.

## A player's readouts
1. Run `uv run python manage.py inspect_readouts steward --t 16 --audience Anna`.

**Result:** the first line names `Anna`; the questions are those asked about Anna's lattice, from
what Anna saw.

## A readout in which the model was thinking
Readouts asked before thinking was switched off for them (WP-063) may show

```
  the model was thinking ("Let"): its first token is no answer. Replay to ask again.
```

The model spent its one token on its reasoning, so the answers are noise. Replaying the story asks
again with thinking off (the changed request is not answered from the call log).

## Readouts without a model
1. Run `uv run python manage.py replay steward --reader uniform`.
2. Run `uv run python manage.py inspect_readouts steward --t 16`.

**Result:** each block says `no language model was asked (uniform reader)` above its answers.

## Errors
- `uv run python manage.py inspect_readouts steward --t 2` prints `No readouts at t=2 for the
  table.`: no question had a candidate the table had seen yet.
- `uv run python manage.py inspect_readouts macbeth --t 5` before any replay of `macbeth` stops
  with `no chronicle 'macbeth'; replay the story first or give a chronicle id`. A chronicle id
  (as in the browser's address, `/chronicles/7`) works too.
