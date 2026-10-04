# WP-056: Consent and anonymisation

**Milestone:** R4 · **Serves:** RQ2

## Goal
Recorded tables can be used in the study only with consent, and exports never reveal who played.

## Acceptance criteria
- Consent is recorded per player; chronicles with a player who has not consented are excluded
  from study exports.
- Exports replace player names and speaker identities with stable pseudonyms.

## Dependencies
WP-055.

## Out of scope
Study design and ethics approval.

## Notes
- Legal requirements (e.g. GDPR) need clarifying with the human before this package starts.

## Status
done (technical safeguards; the legal review is still open)

## Summary
Players record `consent_given_at` (editable in the admin) and carry a random, unique, read-only
`pseudonym`; implicit players need no consent. `export_usage` leaves out chronicles where any human
player has not consented (and says so on stderr) and replaces player ids in the parameters with
pseudonyms; the new `export_session <chronicle>` exports utterances with pseudonymous speakers and
player names in the text replaced, and refuses without everyone's consent. Characters and outlets
keep their names. The legal requirements (GDPR: lawful basis, retention, erasure requests, the
wording of consent) still need clarifying with the human; nothing here settles them. Usage doc:
`docs/usage/consent.md`.
