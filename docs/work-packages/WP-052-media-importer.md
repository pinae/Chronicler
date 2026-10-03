# WP-052: Media importer and claim ingest

**Milestone:** R3 · **Serves:** RQ4

## Goal
Turn a collection of news articles about one event into a `media` chronicle in which every
statement is a claim by its outlet.

## Acceptance criteria
- Outlets become entities of kind `source`; each article passage becomes an utterance with
  `{outlet, author, published_at, url}` and the outlet as speaker.
- Ingesting media utterances wraps every statement as `says(who=<outlet>, what=<prop>)` with
  `source_kind = claim`.
- Schemas with `claimed_by` patterns match these claims (end-to-end test on a small media fixture).

## Dependencies
WP-014, WP-031.

## Out of scope
Fact labels (WP-053); a Rete matcher for large corpora (deferred, §13).

## Notes
- Open: the input format of the article collection, and whether a chronicle covers one event
  (§11 R3) or one event and outlet (§9.4); the concept says both.

## Status
open
