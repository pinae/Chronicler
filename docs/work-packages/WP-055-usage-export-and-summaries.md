# WP-055: Usage event export and session summaries

**Milestone:** R4 · **Serves:** RQ2

## Goal
Export the recorded UI interactions and summarize which engine outputs a GM or writer acted on.

## Acceptance criteria
- Usage events can be exported per chronicle and date range.
- A session summary lists engine outputs (expectations, dry-run results) and whether a matching
  beat followed them.

## Dependencies
WP-039.

## Out of scope
Consent and anonymisation (WP-056); analysing the study.

## Notes
- "Acted on" needs a definition. Proposed: a dry-run draft or an expected candidate that is later
  appended as a beat. Confirm before starting.

## Status
done

## Summary
Usage events now also record the response status and, for POSTs, the JSON body (the tried beat),
and a view can set the `t` it acted at (`request.usage_t`; the dry run uses the t the beat would
get). `manage.py export_usage [--chronicle] [--since] [--until] [--output]` writes JSON lines.
`manage.py usage_summary <chronicle>` lists the successful dry runs and every candidate of the
expectations shown, with the proposed definition of "acted on": the same beat narrated from the
tried t on, or a later fill of the asked step with the candidate in its role in the same lattice.
The latest-readouts query moved to `reader.expectations.latest_expectations`, shared with the API.
Usage doc: `docs/usage/usage-study.md`.
