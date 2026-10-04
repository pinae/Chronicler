# Consent and pseudonyms

Recorded tables may be used in the study only when every player at the table has agreed, and study
exports never reveal who played. (The legal requirements, e.g. under the GDPR, are still to be
clarified; these are the technical safeguards.)

## Record a player's consent
1. Open the admin (`docs/usage/admin.md`), choose **Players** and open the player.
2. Set **Consent given at** to the date and time they agreed, and save.

**Result:** the player list shows when each player consented and their **pseudonym** (e.g.
`player-3fa94c1e`), which is random, fixed for the player, and cannot be edited. Players of
literature and media chronicles (the implicit reader or public) need no consent.

## Exports leave out tables without everyone's consent
1. Run `uv run python manage.py export_usage --output usage.jsonl` (`docs/usage/usage-study.md`)
   while one player of a chronicle has not consented.

**Result:** besides `Exported <n> usage events …`, the command reports
`Left out 1 chronicle without every player's consent.`, and none of that chronicle's events are in
the file. In the exported events, a player named in the parameters (the audience, the players a
tried beat was shown to) appears by pseudonym.

## Export a recorded session
1. Run `uv run python manage.py export_session <chronicle id> > session.json`.

**Result:** a JSON document with the title, the players' pseudonyms and every utterance with its
speaker (a player's pseudonym, a character's or outlet's name, or `gm`). Whole-word mentions of a
player's name in the text are replaced by their pseudonym. If any player has not consented, the
command stops with `not every player of <title> has consented; nothing was exported`.
