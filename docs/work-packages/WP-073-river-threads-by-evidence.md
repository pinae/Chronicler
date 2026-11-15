# WP-073: River threads by evidence

**Milestone:** M8 (follow-up) · **Serves:** RQ2

## Goal
The story river shows at most seven threads per column. It chose the seven with the largest peak
share, but a share is relative: a reading that is alone early in a story holds 100 % of the belief
even when one claim is all that supports it. Schemas that start from common beats (the twist
schemas of WP-074) would then crowd the main plot out of the river. Threads are chosen by their
evidence instead: the peak weight of their strongest reading.

## Acceptance criteria
- The river's threads are the seven whose strongest reading reaches the highest weight at some
  beat (ties: the earlier thread), shown in order of appearance; the rest is "other".
- A weakly supported reading that is alone early in a story does not take a thread's place from
  better supported readings that come later.
- What the existing river, pacing, evidence and clue tests and the usage docs show still holds.

## Dependencies
WP-067.

## Out of scope
Changing shares, surprise or tension: they still compare every reading held at a beat.

## Status
done

## Summary
`strongest_threads` ranks a thread by the highest weight its strongest reading reaches, not by its
peak share. The Broken Jug keeps its threads; in Macbeth and The Steward, readings seeded by a lone
trust or favour (Banquo betraying Duncan) give way to better supported ones (Lady Macbeth's crime
against the grooms, which Ben saw). Shares, surprise and tension are unchanged; all backend tests
and the 63 browser tests pass.
