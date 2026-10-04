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
done

## Summary
Decided: one story per event and outlet (concept §9.4), because completion per outlet needs a
lattice built from that outlet's claims alone; the input is a YAML collection (`event`, `title`,
`articles` with outlet, author, published_at, url, text). `manage.py import_media` writes, per
outlet, a `media` transcript (one utterance per paragraph, spoken by the outlet, with its source
fields) and `entities.yaml` with the outlet as `source`; `draft_beats` now starts from a story's
declared entities and lets an outlet speak. `OllamaIngester` wraps everything an outlet states as
`says(who=@outlet, what=…)` with kind `claim`. The new library schema `blame` (claimed_by patterns
only) is completed by the claims of the media fixture `harbour-fire`, while `betrayal` ignores its
claim that Petra trusted Holt. Usage doc: `docs/usage/import-media.md`.
