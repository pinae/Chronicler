# Importing a recorded session as a story

`import_session` turns the transcript of a recorded play session into the transcript of a new
`session` fixture story: one utterance per turn, spoken by a player or by the GM. Beats and
entities are drafted afterwards (WP-047) and reviewed by a human.

## Before you start
- The backend is installed (`cd backend && uv sync`).
- Everyone at the table agreed to the recording being used (see WP-056).
- The transcript is a UTF-8 text file with one turn per line, `Speaker: text`, optionally after a
  timestamp like `[00:01:23]`. A line without a speaker continues the previous turn. Chat logs and
  diarized transcriptions can usually be converted to this with a search-and-replace.

```
[00:00:05] GM: Lady Mira holds court in the great hall of Wend.
She trusts her steward Aldric with everything.
[00:00:21] Anna: I bet the steward is up to something.
```

## Import a session
1. In `backend/`, run `uv run python manage.py import_session ~/sessions/wend.txt wend --title "The Court of Wend"`.

**Result:** the command prints `Wrote <n> turns by the GM and 2 players (Anna, Ben) to …/fixtures/stories/wend/transcript.yaml`.
Every speaker other than the GM becomes a player of the story, in order of first appearance; turns
by the GM are spoken by `gm`. Each utterance records the line it starts on (`source: {line: 1}`).
`README.md` is a skeleton whose provenance, licence and description are marked `TODO`.

## The GM goes by another name
1. Run the import with `--gm DM` (repeat the option for several names, e.g. `--gm DM --gm Narrator`).

**Result:** turns by **DM** are the GM's; **DM** is not listed as a player.

## A transcript in another format
1. Import a file whose first line has no `Speaker:`.

**Result:** the command stops with `line 1: expected 'Speaker: text'`.
