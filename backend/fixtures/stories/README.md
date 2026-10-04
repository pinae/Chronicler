# Fixture stories

Hand-written (or LLM-drafted and human-reviewed) stories that tests and the `replay` command run
through the pipeline (concept §9.1). One directory per story, named by its slug:

```
fixtures/stories/<slug>/
  README.md          provenance, license (public domain or our own material only), chronicle kind
  transcript.yaml    title, kind, players and the utterances
  entities.yaml      entity table with aliases
  beats.yaml         canonical beats per utterance
  ground_truth.yaml  optional: the twist the engine should see coming (evaluation, WP-040)
  schemas/           optional: story-specific schemas
```

Load one in a test with the `load_story` fixture: `chronicle = load_story("minimal")`.

## transcript.yaml

```yaml
title: The Minimal Hall
kind: session            # session | literature | media
players: [Anna, Ben]     # sessions only; literature and media get their implicit player
utterances:
  - order: 1
    speaker: gm          # gm or narrator (no speaker), a player name, or an entity slug (media outlet)
    text: In the great hall, Lady Mira hands the cellar key to her steward.
    source: {chapter: 1} # or {outlet, author, published_at, url}
```

## entities.yaml

```yaml
aldric: {kind: character, name: Aldric, aliases: [the steward]}
key: {kind: object, name: The cellar key}
```

The key is the entity's slug. Every entity must be mentioned by some beat; it is introduced at the
`t` of its first mention.

## beats.yaml

```yaml
- utterance: 1
  beats:
    - t: 3                     # optional; checked against the beat's position
      pred: gives
      kind: action             # narration (default) | action | claim
      args: {who: "@mira", what: "@key", to: "@aldric"}
      present: [mira, aldric]  # characters who witness the beat
      players: [Ben]           # sessions: players who learn it; omit for everyone, [] for GM only
      text: Mira gives Aldric the cellar key.
      tags: [secretly]
      confidence: 1.0
```

Argument values use a compact notation:

| Written as | Means |
|---|---|
| `"@aldric"` | the entity with slug `aldric` |
| `"#3"` | the beat at `t = 3` |
| `{pred: is_at, args: {...}}` | a nested proposition (claims, beliefs) |
| anything else, e.g. `nervous` | a literal |
| `{literal: "@home"}` | a literal that would otherwise be read as a reference |

Beats are appended in file order, so `t` counts up from 1 across all utterances. Utterances
without beats can be listed with `beats: []` or left out.

### Theories

A player utterance can carry the theories the player voiced:

```yaml
- utterance: 3          # spoken by a player
  theories:
    - {schema: betrayal, binding: {T: aldric}}   # role -> entity slug; other roles stay open
```

A theory is voiced at the `t` of the last beat before its utterance. It marks the live hypothesis
with exactly that binding as voiced, or becomes a hypothesis of its own (WP-022).

## ground_truth.yaml

The twist the engine should see coming, for the evaluation metrics (concept §9.1, §9.2):

```yaml
reveal_t: 22                      # the beat that reveals the twist
true_hypothesis:
  schema: betrayal
  binding: {T: aldric, V: mira}   # role -> entity slug; roles left out may be bound to anyone
dormant_window: [8, 21]           # where the true hypothesis should be live but not dominant
reader_beliefs:                   # optional: annotated beliefs, for calibration
  - {t: 16, question: "Who will harm Mira?", answer: {aldric: 0.4, edda: 0.4, none: 0.2}}
```

`evaluation.ground_truth.read_ground_truth(slug)` checks it against the story and the schema
library: the schema and its roles exist, every slug is an entity of the story of the kind the role
needs, `reveal_t` and the window lie within the story, the window ends before the reveal, and each
answer's probabilities add up to 1 (`none`: nothing like this).

A lattice holds the true hypothesis at `t` when one of its live or complete hypotheses is of the
true schema and binds every role of `binding` the same way.
