# WP-026: Context builder

**Milestone:** M6 (§9.3) · **Serves:** RQ1

## Goal
Feed the reader model a bounded, player-visible context that fits the model's window, even for
long stories.

## Acceptance criteria
- `ContextBuilder` is a `typing.Protocol`; the default implementation returns the most recent
  N beats verbatim plus the beats that fill steps of the top-k live hypotheses (N and k from
  settings), in `t` order and without duplicates.
- It reports which beats it included.
- It never includes a beat outside `visible_to(player, t)`.
- The same inputs always give the same context.

## Dependencies
WP-020, WP-024.

## Out of scope
Prose vs. canonical context experiments (§13).

## Status
done

## Summary
`reader.context.bounded_context` takes the last `READER_CONTEXT_RECENT_BEATS` (30) visible beats plus the
visible beats that filled the `READER_CONTEXT_TOP_HYPOTHESES` (5) strongest hypotheses. It returns them
in `t` order without duplicates, as a `ReaderContext` that reports `included_beat_ts`.
`RecentAndSupportingBeats` (bound as `ContextBuilder` in `settings.INJECTED`) feeds it only
`visible_to(player, t)`. Beats without a written note are phrased from their predicate template with
entity names. Supporting hypotheses are passed as plain `(weight, beat_ts)`, so the builder does not
depend on the matcher.
