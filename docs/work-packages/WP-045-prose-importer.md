# WP-045: Prose importer

**Milestone:** R1 · **Serves:** RQ1

## Goal
Turn a plain-text or Project Gutenberg book into a `literature` fixture transcript.

## Acceptance criteria
- The Gutenberg header and footer are stripped, chapters are detected, and each paragraph becomes
  an utterance with `speaker: narrator` and `source: {chapter}`.
- The importer writes `transcript.yaml` and a README skeleton with provenance and license fields.
- Tested on a short sample text.

## Dependencies
WP-029.

## Out of scope
Producing beats (WP-047); input formats other than plain text.

## Status
done

## Summary
`manage.py import_prose <text file> <slug> [--title] [--stories-dir] [--force]` strips the Project
Gutenberg header and footer, takes title and eBook number from the header, and writes one narrator
utterance per paragraph with `source: {chapter}` plus a README skeleton (provenance filled for
Gutenberg books, licence `TODO`). Chapters are counted from `CHAPTER I.` / `Chapter 2: …` headings
followed by text, so a table of contents adds none; text before the first heading is front matter
and dropped, and decorations and `[...]` notes are skipped. Usage doc: `docs/usage/import-prose.md`.
