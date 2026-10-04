# WP-066: Steampunk theme and app shell

**Milestone:** M8 (follow-up) · **Serves:** RQ2

## Goal
The interface looks like a tool made for a gaming table: a steampunk fantasy theme (ADR-012) with a
shared header, navigation between a chronicle's screens, and every existing screen restyled.

## Acceptance criteria
- Design tokens for a light and a dark theme; the theme follows the system and can be switched with
  a **Theme** control that is remembered.
- Every page has the header **Chronicler** linking to the chronicle list; a chronicle's pages share
  a navigation with **Story map**, **Beats**, **Lattice**, **Who knows what** and **Try a beat**,
  the current one marked.
- The chronicle list shows each chronicle as a card with its kind and beat count.
- All existing usage scenarios and tests keep passing (accessible names unchanged).

## Dependencies
WP-034, WP-064.

## Out of scope
New views (WP-068 and later).

## Status
open
