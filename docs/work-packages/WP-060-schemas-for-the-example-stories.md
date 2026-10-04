# WP-060: Schemas for the example stories

**Milestone:** M3 (follow-up) · **Serves:** RQ1

## Goal
The library holds the narrative patterns that two well-known plays turn on, so that the example
stories of WP-061 can show what the engine reads: a hidden crime (a whodunit), a usurpation and a
prophecy. Adding schemas must not change what the existing tests expect.

## Acceptance criteria
- `hidden_crime`: a harm, killing or theft seeds a reading; so does an investigator's suspicion of
  the culprit (victim still open). Blaming someone else covers it up; the reading completes when
  the investigator learns of the crime, and the culprit must have known the crime, the
  investigator not before the discovery.
- `usurpation`: a ruler's favour seeds a reading; the favoured one wants the power, kills the ruler
  and takes the power.
- `prophecy`: a foretelling ("X will have Y") seeds a reading; it is fulfilled when X has Y or is
  given Y.
- A betrayer who kills the victim has done the betrayal's harm.
- `SCHEMA_LIBRARY_SLUGS` limits which library files are read (None: all); the test settings pin
  the schemas the matcher's tests were written against.

## Dependencies
WP-011, WP-012.

## Out of scope
Schemas for other genres; tuning weights against a corpus (WP-050).

## Status
done

## Summary
Three new YAML files and one new pattern each in `betrayal` (harm by `kills`) and `prophecy`
(fulfilment by `gives`). `schemas/tests/test_library_readings.py` runs each schema over a few plain
beats. `read_library` filters by `settings.SCHEMA_LIBRARY_SLUGS`; the test settings pin
`["betrayal", "blame"]`, so 21 tests whose expected lattices were written against those two schemas
keep their meaning. The schema library usage doc now lists what each schema reads.
