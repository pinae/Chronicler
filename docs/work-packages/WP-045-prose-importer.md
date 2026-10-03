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
open
