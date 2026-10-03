# WP-029: Ingester protocol and fixture ingester

**Milestone:** M7 · **Serves:** RQ1, RQ4

## Goal
Utterances turn into beat drafts through an injected `Ingester`; tests use one that replays
hand-authored fixture beats.

## Acceptance criteria
- `Ingester` is a `typing.Protocol`: an utterance (with the chronicle's state) → beat drafts with
  presence information, entity references and voiced theories.
- `FixtureIngester` yields exactly the fixture's beats for each utterance, in order; utterances
  without beats yield none.
- It accepts table talk (`session`), prose with `speaker: narrator` (`literature`) and articles
  with `speaker: <outlet>` (`media`).
- Test settings bind `Ingester → FixtureIngester`.

## Dependencies
WP-010, WP-022, WP-024.

## Out of scope
LLM-based ingest (WP-031).

## Status
done

## Summary
`chronicle/ingest/interfaces.py` defines the `Ingester` protocol: an utterance of a chronicle goes in;
an `IngestResult` with beat drafts, voiced theories and first-mentioned entities comes out. Drafts
use the compact `@slug` argument notation of fixture stories, so the fixture and LLM ingesters share
the pipeline that creates entities and appends beats (WP-030). `FixtureIngester` takes no arguments:
it finds its story through `chronicle.meta["fixture"]` in `settings.FIXTURE_STORIES_DIR` and returns
that utterance's beats in order, for session, literature and media stories alike. Test and base
settings bind it as `Ingester` until the Ollama ingester exists (WP-031).
