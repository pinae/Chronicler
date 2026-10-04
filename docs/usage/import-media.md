# Importing news coverage as stories

`import_media` turns a collection of news articles about one event into `media` fixture stories,
one per outlet: every paragraph becomes an utterance spoken by the outlet, and the outlet is an
entity of kind `source`. When the beats are drafted (`docs/usage/draft-beats.md`), everything an
outlet states becomes a claim by that outlet, `says(who=<outlet>, what=<statement>)`, never a fact:
schemas see claims only through `claimed_by` patterns (concept §9.4). Each outlet gets its own
story because comparing outlets (WP-054) needs a lattice built from one outlet's claims alone.

## Before you start
- The backend is installed (`cd backend && uv sync`).
- The articles are collected in a YAML file:

```yaml
event: harbour-fire
title: The Harbour Fire
articles:
  - outlet: The Courier
    author: Ines Varga
    published_at: "2026-05-02T07:30:00Z"
    url: https://courier.example/harbour-fire
    text: |
      Fire destroyed old Petra's boat shed last night.

      Witnesses saw Mayor Holt nearby.
```

## Import a collection
1. In `backend/`, run `uv run python manage.py import_media ~/news/harbour-fire.yaml`.

**Result:** the command prints `Wrote 2 outlets, <n> passages of harbour-fire: harbour-fire-the-courier, harbour-fire-harbour-herald`.
Each story directory holds a `transcript.yaml` (kind `media`, the outlet's paragraphs in order of
publication, each with `source: {outlet, author, published_at, url}`), an `entities.yaml` with the
outlet as a `source`, and a README skeleton whose provenance and licence are marked `TODO`.

2. Run `uv run python manage.py draft_beats harbour-fire-the-courier`.

**Result:** the drafted beats are claims by `@the-courier` (`kind: claim`), and the outlet stays in
`entities.yaml`.

## An article without its outlet
1. Import a collection in which an article has no `outlet`.

**Result:** the command stops with `article <n>: missing 'outlet'`.

## Existing stories are not overwritten
1. Run the same import again.

**Result:** the command stops with `harbour-fire-the-courier already has a transcript.yaml; pass --force to replace it`.
