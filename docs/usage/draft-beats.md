# Drafting a story's beats

`draft_beats` lets the configured ingester (the language model in production) read a story's
transcript and draft its `beats.yaml` and `entities.yaml`. The drafts are for human review: you
correct them in the YAML files before the story is replayed or evaluated.

## Before you start
- The backend is installed and migrated, and the Ollama settings are configured (see
  `docs/usage/ollama-smoke-check.md`).
- The story has a `transcript.yaml`, e.g. from `docs/usage/import-prose.md` or
  `docs/usage/import-session.md`.

## Draft the beats of a story
1. In `backend/`, run `uv run python manage.py draft_beats alice`.

**Result:** the command prints `Drafted <n> beats and <m> entities from <k> utterances; <r> marked for review`
and writes `fixtures/stories/alice/beats.yaml` and `entities.yaml`. Every beat carries the
ingester's `confidence`. Utterances are drafted in order, each against the entities and beats drafted
before it, so later beats can refer to earlier ones. Nothing is stored in the database. If the story
already has an `entities.yaml` (for example the outlet written by `docs/usage/import-media.md`),
those entities are known from the start, may speak (a media outlet), and are kept.

## Review the draft
1. Search `beats.yaml` for `review:`.

**Result:** each mark says what to decide:
- `unknown predicate '<pred>': …` on a beat: map it onto a predicate of the vocabulary
  (`backend/schemas/vocabulary.yaml`), or keep it as it is (it will be quarantined).
- a list of problems on an utterance: drafts the ingester had to drop, or why the utterance's beats
  could not be appended (for example an unknown entity); add the missing beats yourself.

2. Delete each mark once you have dealt with it.

**Result:** while any mark is left, loading the story fails with
`beats.yaml, utterance <n>, beat <m>: still marked for review: …`.

## Reviewed beats are not overwritten
1. Run `uv run python manage.py draft_beats alice` again.

**Result:** the command stops with `alice already has a beats.yaml; pass --force to replace it`.
