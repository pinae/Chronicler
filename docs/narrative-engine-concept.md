# Narrative Interpretation Engine — Developer Concept & TDD Plan

**Status:** concept, ready for implementation of the v1 core
**Nature:** research project (see §1); the v1 core is the instrument the research questions are investigated with
**Stack:** Python ≥ 3.12, `uv` for packaging, Django (current LTS, 5.2+), pytest + pytest-django, PostgreSQL (SQLite in unit tests), LLM calls to an external Ollama server with a capable GPU
**Audience:** a developer starting the codebase from scratch

---

## 0. Read this first

This engine supports a tabletop game master (GM), and later also writers and analysts. It consumes what is said at the table (or the text of a story, or a corpus of news articles), keeps a formal record of the narrated world (the **Chronicle**), matches that record against a library of narrative patterns (**Schemas**), maintains the set of partial matches (**Hypotheses**), and asks a language model which continuations an audience currently expects (**Expectations**). A GM uses this to plan beats that set up plausible plot twists; the research questions in §1 ask what else the same structure is good for.

Four things shape every design decision below:

1. **This is a research project.** The code is an instrument for answering the questions in §1. Every feature should be traceable to one of them, and the first thing the instrument has to be able to do is *measure* — hence the emphasis on replay and evaluation.

2. **The concepts will be validated against existing stories.** Public-domain literature and recorded play sessions will be fed through the pipeline, and we will measure whether the engine "saw the twist coming" the way a reader would. This means the whole pipeline must be **replayable** and **time-indexed**: any question the GM can ask about *now* must also be answerable about *beat 40 of a 200-beat story*. Do not build anything that only works for the live, latest state. Read §9 before writing a single model.

3. **All LLM calls sit behind interfaces with fake implementations.** Production calls go to an external Ollama server (§8). Tests never reach the network. The matcher, the lattice, the scope logic and the evaluation harness are deterministic and fully tested with hand-authored fixtures. LLM-backed implementations are integration work that comes after, gated behind a flag.

4. **The Chronicle is append-only.** Nothing is ever edited or deleted; corrections are new beats. Derived views (entity attributes, who-knows-what, hypothesis weights) are projections that can be rebuilt from the beat log at any point in time.

Out of scope for v1: ingest quality, weight calibration, UI polish, multi-session campaigns, and the research tracks R1–R4 (§11) beyond what the core must leave room for.

---

## 1. Research questions and what they demand from the code

| # | Question | Corpus | What the code must provide | Where |
|---|---|---|---|---|
| **RQ1** | Can a data structure of Beats and Schemas capture classic literary stories *and* the interactive stories that emerge in pen-and-paper roleplaying sessions? | Public-domain prose; transcribed play sessions | The core data model and matcher; ingesters for both prose and table talk; the evaluation harness with twist-recall, lead-time and retrospective-fit metrics | M1–M4, M7, M9 |
| **RQ2** | Is analysing stories this way helpful for writers and game masters? | The same, plus live use | A GM/writer UI over the lattice and expectations, including dry-run of candidate beats; usage logging for a later study | M8, R4 |
| **RQ3** | Does a narrative structure analysed and represented this way help an LLM write stories of its own? | Engine-generated stories | A `StoryWriter` interface that consumes lattice + expectations + a target hypothesis and produces beats and prose; the engine then re-ingests and scores its own output | R2 |
| **RQ4** | Can the same machinery analyse real-world events and their media coverage and find narratives that are told for their narrative appeal rather than their factuality? | News articles about the same events from several outlets | A `media` chronicle kind, outlets as sources, every statement as a *claim* beat, external factuality labels on propositions, and comparison of lattices across chronicles | R3 |

Consequences that reach into the v1 core:

- A chronicle has a **kind** — `session`, `literature`, `media` — and all three are first-class from the start. The model name for the container is `Chronicle`; the beat list inside it is "the chronicle" in prose.
- "Players know X" generalises to "the audience knows X". For a session there is one `Player` per human at the table; for literature and media there is exactly one implicit player (`reader` / `public`) created with the chronicle. Scope logic is identical in all three cases.
- Utterances carry **source metadata** (chapter, outlet, author, date, URL). Nothing in v1 reads it, but RQ4 is impossible without it and it is free to record.
- The **claim machinery** (`says(who, prop)` beats and matching inside propositions, §4.1) is not an optional refinement. RQ4 lives entirely inside it: in a media chronicle almost every beat is a claim by an outlet.
- On RQ4, be precise about what the engine can and cannot say. It measures how strongly a body of text instantiates known narrative patterns and how those patterns differ across sources. It does **not** adjudicate truth; factuality enters only as an external label (fact-checker verdict, manual annotation) attached to propositions. The research claim is "this coverage completes a Betrayal schema more fully than the verified facts support", never "this outlet lies". Build and document the feature with that boundary.

---

## 2. Concepts

| Term | Meaning |
|---|---|
| **Chronicle (container)** | One story-world record: a play session, a literary work, or a media corpus about one event. Has a `kind`. |
| **Utterance** | One thing said at the table, one paragraph of a prose story, or one article passage. Has a speaker and source metadata. Raw input. |
| **Beat** | One formal fact about the narrated world, derived from an utterance: a predicate from a closed vocabulary, typed arguments, who knows it. |
| **Entity** | A character, object, place, faction, secret or source referenced by beats. The entity table is a *view* derived from beats. |
| **Proposition** | A beat-shaped structure nested inside a beat, used for claims and beliefs ("the steward *says* he was in the kitchen"; "the Herald *reports* the minister resigned"). |
| **Scope** | For each beat: the set of characters who know it and the set of players (audience members) who know it. Changes to scope are themselves beats (`learns`). |
| **Schema** | A narrative pattern: typed roles, a list of steps, constraints, and a marker for which steps are the payoff. Not made of beats; its steps are *patterns* that beats can fill. |
| **Step** | One slot of a schema: a beat pattern with role variables, a phase, a weight. |
| **Hypothesis** | A partial match of a schema against the chronicle: a (possibly incomplete) role binding plus the beats that fill its steps. The set of hypotheses is the **lattice**. |
| **Voiced hypothesis** | A hypothesis a player stated out loud ("I bet the steward is the traitor"). Stored like any other hypothesis, flagged with the player. These are labels for calibration. |
| **Expectation** | For a live hypothesis and one of its open steps: a probability distribution over which concrete beat (which entities) would fill it next. |
| **Reader model** | The component that turns a chronicle prefix plus a fixed question into a probability distribution over a closed set of answers. Ollama-backed in production, table-backed in tests. |

---

## 3. Pipeline

```
Utterance ──▶ Ingester ──▶ Beat drafts ──▶ Chronicle.append()
             (Ollama)                            │
                              ┌──────────────────┴──────────────────┐
                              ▼                                     ▼
                      Scope materialization              Entity view update
                              │
                              ▼
                         Matcher.step(beat)        (Fill → Seed → Maintain)
                              │
                              ▼
                      Hypothesis lattice (time-indexed)
                              │
                              ▼
                    ReaderModel.readout(...)  ──▶  Expectations  ──▶  GM / writer UI
                       (Ollama)                          │
                                                         ▼
                                              StoryWriter (R2)  ──▶ new utterances ──▶ back to Ingester
```

Each arrow is a function call with a deterministic contract. The Ollama-backed boxes are the only non-deterministic parts and are injected.

Phases of `Matcher.step(beat)`:

- **Fill** — for every live hypothesis, test whether the new beat fills one of its open steps under its current binding (binding may be extended by the match). Also test whether the beat starts a *new* partial match for any schema (seed by trigger step).
- **Seed** (readout) — for every live hypothesis with open steps, build the readout question and candidate list for the next step and ask the reader model. Produces Expectations.
- **Maintain** — apply refutations (beats matching a step's `contradicts` pattern or violating a hard constraint), merge hypotheses that became identical, prune hypotheses below a weight floor, mark completed ones.

---

## 4. Data model (Django)

Apps: `chronicle`, `schemas`, `matching`, `reader`, `llm`, `evaluation`, `gm_ui`.

The sketch below is the intended shape; field names are binding, exact types may be adjusted.

```python
# chronicle/models.py

class Chronicle(models.Model):
    KIND = [("session", "session"), ("literature", "literature"), ("media", "media")]
    kind = models.CharField(max_length=20, choices=KIND)
    title = models.CharField(max_length=200)
    meta = models.JSONField(default=dict)                # provenance, license, event description (media)
    created_at = models.DateTimeField(auto_now_add=True)

class Player(models.Model):
    """One audience member. Sessions: one per human at the table.
    Literature / media: exactly one implicit row ('reader' / 'public'), created with the chronicle."""
    chronicle = models.ForeignKey(Chronicle, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    implicit = models.BooleanField(default=False)

class Utterance(models.Model):
    chronicle = models.ForeignKey(Chronicle, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()               # position in transcript / text / corpus
    speaker_player = models.ForeignKey(Player, null=True, on_delete=models.SET_NULL)  # None = GM / narrator / outlet
    speaker_entity = models.ForeignKey("Entity", null=True, on_delete=models.SET_NULL)  # media: the outlet
    text = models.TextField()
    source = models.JSONField(default=dict)              # {chapter} | {outlet, author, published_at, url}

    class Meta:
        unique_together = [("chronicle", "order")]

class Entity(models.Model):
    KIND = [("character", "character"), ("object", "object"), ("place", "place"),
            ("faction", "faction"), ("secret", "secret"), ("source", "source")]
    chronicle = models.ForeignKey(Chronicle, on_delete=models.CASCADE)
    kind = models.CharField(max_length=20, choices=KIND)
    canonical_name = models.CharField(max_length=200)
    aliases = models.JSONField(default=list)             # ["the steward", "Aldric"]
    introduced_at_t = models.PositiveIntegerField()      # t of first beat mentioning it

class EntityAttribute(models.Model):
    """Derived view: one row per (entity, key), rebuilt from beats. Keeps provenance."""
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    key = models.CharField(max_length=100)               # "mood", "has", "is_at"
    value = models.JSONField()
    source_beat = models.ForeignKey("Beat", on_delete=models.CASCADE)

class Beat(models.Model):
    SOURCE_KIND = [("narration", "narration"), ("action", "action"), ("claim", "claim")]
    chronicle = models.ForeignKey(Chronicle, on_delete=models.CASCADE)
    t = models.PositiveIntegerField()                    # ordinal in the chronicle, unique per chronicle
    pred = models.CharField(max_length=50)               # validated against the vocabulary
    args = models.JSONField()                            # see §4.1
    tags = models.JSONField(default=list)                # ["nervous", "secretly"]
    source_utterance = models.ForeignKey(Utterance, on_delete=models.PROTECT)
    source_kind = models.CharField(max_length=20, choices=SOURCE_KIND)
    text = models.TextField()                            # compressed note, human-readable
    confidence = models.FloatField(default=1.0)          # ingester's confidence in canonicalization

    class Meta:
        unique_together = [("chronicle", "t")]
        ordering = ["t"]

class ScopeGrant(models.Model):
    """Append-only: 'subject knows beat since t'. Current scope = all grants; scope at t = grants with t <= t."""
    beat = models.ForeignKey(Beat, related_name="grants", on_delete=models.CASCADE)
    character = models.ForeignKey(Entity, null=True, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, null=True, on_delete=models.CASCADE)
    t = models.PositiveIntegerField()                    # when the knowledge was gained
    via_beat = models.ForeignKey(Beat, null=True, related_name="+", on_delete=models.SET_NULL)  # the `learns` beat, if any

class FactLabel(models.Model):
    """External factuality label on a beat (usually a claim). Written by annotators / fact-check imports, never by the engine. RQ4."""
    beat = models.ForeignKey(Beat, related_name="fact_labels", on_delete=models.CASCADE)
    verdict = models.CharField(max_length=20)            # verified | false | unverified | misleading
    labeler = models.CharField(max_length=200)
    note = models.TextField(blank=True)
```

### 4.1 `Beat.args` format

`args` is a JSON object keyed by role name. Role names are fixed per predicate (see §5). Each value is one of:

```json
{"entity": 17}
{"literal": "kitchen"}
{"beat": 42}
{"prop": {"pred": "is_at", "args": {"who": {"entity": 17}, "where": {"entity": 23}}}}
```

The `prop` form is the Proposition. It is used by `says`, `believes`, `wants` and similar predicates whose content is itself beat-shaped. The matcher must be able to match patterns *inside* propositions. Two things depend on this: the "Lie" schema (`says(X, P)` plus a player-visible beat establishing `¬P`), and the entire RQ4 track, where an article's statement "the minister resigned" is ingested as `says(who=<Herald>, what={pred: ..., ...})` and schemas are matched against the propositions.

### 4.2 Scope semantics

- When a beat is appended, the ingester supplies its *initial* scope (characters present, players at the table; for literature and media, the implicit player). These become `ScopeGrant` rows with `t = beat.t`.
- A beat with `pred = "learns"` and args `{who: entity, what: beat}` creates a `ScopeGrant(beat=what, character=who, t=learns_beat.t, via_beat=learns_beat)`.
- `Beat.known_by_chars_at(t)` and `Beat.known_by_players_at(t)` filter grants by `t`.
- `Chronicle.visible_to(player, t)` returns the beats a player knew at time `t`. **The reader model is always fed this filtered view, never the full chronicle.**

```python
# schemas/models.py

class Schema(models.Model):
    ORIGIN = [("library", "library"), ("voiced", "voiced")]
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=200)
    roles = models.JSONField()          # {"T": "character", "V": "character", "S": "secret"}
    constraints = models.JSONField(default=list)   # see §6
    payoff_steps = models.JSONField(default=list)  # ["reveal"]
    prior = models.FloatField(default=0.0)         # log-odds base rate
    origin = models.CharField(max_length=20, choices=ORIGIN, default="library")

class Step(models.Model):
    PHASE = [("setup", "setup"), ("development", "development"), ("payoff", "payoff")]
    schema = models.ForeignKey(Schema, related_name="steps", on_delete=models.CASCADE)
    step_id = models.SlugField()
    order = models.PositiveIntegerField()
    phase = models.CharField(max_length=20, choices=PHASE)
    patterns = models.JSONField()       # list of BeatPattern; any one may fill the step
    required = models.BooleanField(default=True)
    repeatable = models.BooleanField(default=False)
    weight = models.FloatField(default=1.0)        # log Bayes factor contributed when filled
    contradicts = models.JSONField(default=list)   # list of BeatPattern; a match refutes the hypothesis
    trigger = models.BooleanField(default=False)   # may a beat matching this step seed a new hypothesis?

    class Meta:
        unique_together = [("schema", "step_id")]
```

```python
# matching/models.py

class Hypothesis(models.Model):
    STATUS = [("live", "live"), ("complete", "complete"), ("refuted", "refuted"), ("pruned", "pruned")]
    chronicle = models.ForeignKey(Chronicle, on_delete=models.CASCADE)
    schema = models.ForeignKey(Schema, on_delete=models.PROTECT)
    binding = models.JSONField()        # {"T": 17, "V": 9, "S": null}  (null = open)
    weight = models.FloatField()        # prior + Σ weights of filled steps (calibration later)
    status = models.CharField(max_length=20, choices=STATUS, default="live")
    created_at_t = models.PositiveIntegerField()
    status_changed_at_t = models.PositiveIntegerField(null=True)
    refuted_by = models.ForeignKey(Beat, null=True, on_delete=models.SET_NULL)
    voiced_by = models.ForeignKey(Player, null=True, on_delete=models.SET_NULL)
    voiced_in = models.ForeignKey(Utterance, null=True, on_delete=models.SET_NULL)
    refines = models.ForeignKey("self", null=True, on_delete=models.SET_NULL)  # more specific binding of a parent

class StepFill(models.Model):
    """Which beat filled which step of which hypothesis. Time-indexed via beat.t."""
    hypothesis = models.ForeignKey(Hypothesis, related_name="fills", on_delete=models.CASCADE)
    step = models.ForeignKey(Step, on_delete=models.PROTECT)
    beat = models.ForeignKey(Beat, on_delete=models.CASCADE)

class Expectation(models.Model):
    hypothesis = models.ForeignKey(Hypothesis, on_delete=models.CASCADE)
    step = models.ForeignKey(Step, on_delete=models.PROTECT)
    computed_at_t = models.PositiveIntegerField()
    for_player = models.ForeignKey(Player, null=True, on_delete=models.SET_NULL)  # None = whole table
    candidates = models.JSONField()     # [{"binding_delta": {"T": 17}, "p": 0.41}, ..., {"null": true, "p": 0.12}]
    llm_call = models.ForeignKey("llm.LLMCall", null=True, on_delete=models.SET_NULL)  # provenance
```

**Replay guarantee:** with `Beat.t`, `ScopeGrant.t`, `Hypothesis.created_at_t`, `Hypothesis.status_changed_at_t` and `StepFill.beat.t`, the full lattice at any `t` is a filter, not a snapshot. `Lattice.at(chronicle, t)` must be implemented and tested in milestone M4. Expectations are additionally stored per `computed_at_t` because they depend on the reader model, which is not re-derivable without the LLM call log (§8.4).

---

## 5. Predicate vocabulary (starter set)

The vocabulary is data (`schemas/vocabulary.yaml`), loaded at startup and used to validate every beat. An unknown predicate does not crash ingest: the beat is stored with `pred = "unknown"` and `tags += ["quarantined"]`, and the matcher ignores it. Growth of the vocabulary is a reviewed change, like a migration. The ingest of media (R3) will put pressure on this vocabulary; resist reacting by adding domain-specific predicates — "resigns", "indicts", "announces" are `breaks`, `harms`, `says` with roles filled.

| Group | Predicates | Roles |
|---|---|---|
| transfer | `gives`, `takes`, `steals` | `who`, `what`, `from`/`to` |
| help/harm | `helps`, `harms`, `protects`, `saves`, `kills` | `who`, `whom`, `how?` |
| social | `trusts`, `distrusts`, `promises`, `breaks`, `allies`, `opposes` | `who`, `whom`, `what?` |
| epistemic | `learns`, `hides`, `reveals`, `says`, `believes` | `who`, `what` (beat or prop), `from`/`to?` |
| state | `has`, `is_at`, `is` | `who`, `what`/`where`/`trait` |
| intention | `wants`, `fears`, `seeks`, `avoids` | `who`, `what` (entity or prop) |

Roles ending in `?` are optional. Every predicate declares its role names and the allowed value kinds per role. Keep the set under ~40 entries in v1; the ingester's job is to map "lends", "hands over", "entrusts" onto `gives`.

---

## 6. Schema file format

Schemas are authored in YAML under `schemas/library/*.yaml` and loaded by a management command. Example:

```yaml
slug: betrayal
name: Betrayal
roles: {T: character, V: character, S: secret}
prior: -2.0
payoff_steps: [reveal]
constraints:
  - {type: distinct, roles: [T, V]}
  - {type: before, steps: [trust, harm]}
  - {type: knows, role: T, step: harm}
  - {type: not_knows, role: V, step: harm}        # until reveal
steps:
  - step_id: trust
    phase: setup
    trigger: true
    patterns:
      - {pred: trusts, args: {who: $V, whom: $T}}
      - {pred: helps, args: {who: $T, whom: $V}}
    repeatable: true
    weight: 0.5
  - step_id: access
    phase: development
    patterns:
      - {pred: learns, args: {who: $T, what: {pred: hides, args: {who: $V, what: $S}}}}
      - {pred: has, args: {who: $T, what: $S}}
    weight: 1.0
  - step_id: harm
    phase: development
    patterns:
      - {pred: harms, args: {who: $T, whom: $V}}
      - {pred: steals, args: {who: $T, what: $S, from: $V}}
    weight: 1.5
    contradicts:
      - {pred: kills, args: {who: "*", whom: $T}}   # T dead before harm → not this betrayal
  - step_id: benefit
    phase: development
    required: false
    patterns:
      - {pred: gives, args: {to: $T, what: "*"}}
    weight: 0.5
  - step_id: reveal
    phase: payoff
    patterns:
      - {pred: learns, args: {who: $V, what: $harm}}   # $harm = the beat that filled step "harm"
    weight: 3.0
```

### 6.1 BeatPattern grammar

- `pred`: exact predicate name.
- `args`: role → value, where value is `$Role` (role variable), `"*"` (wildcard), a literal, a nested pattern (`{pred, args}` matched against a `prop` arg), or `$step_id` (reference to the beat that filled another step of the same hypothesis).
- Omitted roles are wildcards.
- Optional `tags_any: [..]` / `tags_all: [..]` for manner constraints (`nervous`).
- Optional `scope: {players_know: true}` — the beat must be visible to the players (or to a given player when evaluating per-player lattices).
- Optional `claimed_by: $Source` — the pattern matches a proposition inside a `says` beat whose speaker binds `$Source`. This is the hook RQ4 uses to ask "which outlet tells this story".

### 6.2 Constraint types (v1)

`distinct`, `before`, `after`, `knows`, `not_knows`, `same_place`. Constraints are checked in Maintain after every Fill; a violated hard constraint sets `status = refuted`.

---

## 7. Matching semantics

A hypothesis is a schema plus a partial binding plus a set of step fills. Matching a beat against a step pattern under a binding:

1. Predicates must be equal.
2. For each arg in the pattern: `*` matches anything; a literal must equal; `$R` must equal `binding[R]` if bound, else binds `R` to the beat's value (**binding extension**); `$step` must equal the beat id that filled that step; a nested pattern recurses into a `prop` arg.
3. Role kinds must be consistent with the entity kinds.
4. The match result is either *no match* or a (possibly extended) binding.

Rules:

- A beat may fill a step of several hypotheses, and several steps of one hypothesis only if those steps allow it (default: one step per beat per hypothesis).
- Filling a step whose binding extension differs from an existing hypothesis **creates a new hypothesis with `refines` pointing to the parent** rather than mutating the parent. Example: `Betrayal(T=?, V=Mira)` plus a `helps(Aldric, Mira)` beat yields `Betrayal(T=Aldric, V=Mira)` as a child. The parent stays live until pruned. This is what makes the lattice a lattice.
- `repeatable` steps accumulate fills; weight is contributed once per fill up to a cap (config, default 3).
- A beat matching a step's `contradicts` pattern refutes the hypothesis.
- `weight = schema.prior + Σ step.weight over filled steps`. Status becomes `complete` when all required steps are filled.
- Seeding: a beat seeds a new hypothesis for schema S only if it matches a step with `trigger: true` and no live hypothesis of S already has that beat as a fill under a compatible binding.

**Why incremental, and why not a full Rete yet.** The lattice we want *is* the set of partial matches a Rete network keeps in its beta memories. At the scales involved (hundreds of beats, tens of schemas, tens of live hypotheses) the naive incremental join — new beat × open steps of live hypotheses, plus new beat × trigger steps — is fast enough and far easier to test. Implement it behind a `Matcher` interface with the three-phase contract above. If a media corpus (thousands of claims) demands it later, a Rete with NOT nodes slots in behind the same interface; the tests do not change.

**All fuzziness lives in ingest.** The matcher is exact: it compares canonical predicates and entity ids. The ingester is responsible for canonicalization and entity resolution and records its `confidence` on the beat. Graded belief lives in `Hypothesis.weight` and in reader-model readouts, never in the matcher.

---

## 8. LLM infrastructure: Ollama

All model calls go through the `llm` app to an **external Ollama server** with a capable GPU. Nothing else in the codebase imports an LLM client.

### 8.1 Configuration

```python
# settings/base.py — all read from environment, none have defaults in test settings
OLLAMA_BASE_URL   = env("OLLAMA_BASE_URL")           # e.g. http://gpu-box:11434
OLLAMA_READER_MODEL = env("OLLAMA_READER_MODEL")     # model used for readouts / Bayes factors
OLLAMA_INGEST_MODEL = env("OLLAMA_INGEST_MODEL")     # model used for canonicalization (may be the same)
OLLAMA_NUM_CTX    = env.int("OLLAMA_NUM_CTX", 16384) # must cover the longest chronicle prefix you feed in
OLLAMA_KEEP_ALIVE = env("OLLAMA_KEEP_ALIVE", "30m")
OLLAMA_TIMEOUT_S  = env.int("OLLAMA_TIMEOUT_S", 120)
```

Use the official `ollama` Python package and its **native** API (`/api/generate`, `/api/chat`), not the OpenAI-compatible shim: the native API is where structured outputs and logprobs are exposed. Pin the client version in `pyproject.toml`.

### 8.2 Model requirements

- An instruction-tuned model large enough to canonicalize narrative reliably (ingest) and to give meaningful probabilities (readout). Both roles can use the same model; keep the setting split so they can diverge.
- **The reader model must return logprobs.** Ollama exposes `logprobs` / `top_logprobs` on generated tokens from version 0.12 on, and not every model family supports it. Before anything else, run the smoke check below against the actual server and model and commit its output to `docs/llm-smoke.md`.
- `num_ctx` must cover the longest player-visible chronicle prefix plus the question. Long classic stories will exceed any practical window; §9.3 says what to do.

```bash
uv run python -m llm.smoke   # prints: server version, model, logprobs=yes/no, top_logprobs max, json-schema=yes/no, prompt-logprobs=yes/no
```

### 8.3 Reader-model estimators and which Ollama features they need

| Estimator | Needs | Ollama status | Fallback |
|---|---|---|---|
| **Choice readout** — distribution over a closed candidate list | `top_logprobs` on the *first generated token* | Supported (≥ 0.12, model-dependent) | Sampling at temperature 1 with N draws; frequency as probability |
| **Bayes factor** — logprob of the *same* beat text under two hypothesis-conditioned contexts | logprobs of a *forced* multi-token continuation (prompt / echo logprobs) | Verify on the deployed version; historically not exposed | Run a vLLM or llama.cpp server beside Ollama on the same GPU for this estimator only, behind the same interface; or token-by-token forced scoring via `top_logprobs` (one call per token, lossy when a token falls outside top-k) |
| **Structured ingest** — beats as JSON | JSON-schema constrained output (`format`) | Supported | Prompted JSON + repair + validation |

The choice readout is implemented as a multiple-choice prompt: candidates are listed with single-token labels (`A`, `B`, `C`, …, plus a label for "none of these / nothing yet"), the model is asked to answer with the label only, and the distribution is read from `top_logprobs` of the first generated token with `top_logprobs` ≥ the number of candidates. Do **not** use constrained decoding for the readout: masking renormalizes the distribution and hides how much mass the model put outside the candidate set, which is itself a signal. Cap candidate lists at the server's `top_logprobs` maximum and page if needed.

### 8.4 Reproducibility: the call log and cache

```python
# llm/models.py
class LLMCall(models.Model):
    request_hash = models.CharField(max_length=64, unique=True)  # sha256 of (model, endpoint, canonical JSON of params)
    model = models.CharField(max_length=100)
    endpoint = models.CharField(max_length=50)
    request = models.JSONField()
    response = models.JSONField()
    server_version = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
```

Every production call is stored. A repeated identical request is served from the table without touching the server. This makes evaluation runs reproducible, makes re-running a 200-beat story after a matcher bug fix cost zero LLM time, and gives every `Expectation` a provenance link. Store temperature-1 sampling runs too (with the draw index in the hashed params).

### 8.5 Boundaries

- `settings/test.py` sets no `OLLAMA_*` values and binds `ReaderModel → TableReader`, `Ingester → FixtureIngester`. If any test touches the network, it is a bug.
- Integration tests live under `*/tests/integration/`, are marked `@pytest.mark.llm`, are deselected by default, and are run with `uv run pytest --llm`. They skip, not fail, when `OLLAMA_BASE_URL` is unset.
- Concurrency: Ollama serialises requests per model by default. The replay command issues calls sequentially; do not add threading without checking the server's `OLLAMA_NUM_PARALLEL`.

---

## 9. Evaluation against existing stories — requirements for the codebase

The engine will be run over existing stories to check whether the concepts hold up (RQ1), and later over its own output (RQ3) and media corpora (RQ4). The developer must make the following possible from the start; retrofitting them is expensive.

### 9.1 Fixture format

```
fixtures/stories/<story-slug>/
  README.md             # provenance, license (public domain or our own material only), chronicle kind
  transcript.yaml       # list of {order, speaker, text, source}; prose uses speaker: narrator, media uses speaker: <outlet>
  beats.yaml            # canonical beats per utterance (hand-authored for small stories,
                        #   LLM-produced and human-reviewed for larger ones)
  entities.yaml         # entity table with aliases
  ground_truth.yaml     # see below
  schemas/              # optional story-specific schemas
```

`ground_truth.yaml`:

```yaml
reveal_t: 141                     # beat index of the twist
true_hypothesis:
  schema: betrayal
  binding: {T: aldric, V: mira}
dormant_window: [60, 140]         # where a good engine should hold the true hypothesis as live-but-not-dominant
reader_beliefs:                   # optional: annotated belief at checkpoints, used for calibration
  - {t: 80, question: "Who will harm Mira?", answer: {aldric: 0.15, ronan: 0.55, none: 0.30}}
```

### 9.2 Metrics (`evaluation/metrics.py`)

- **Twist recall** — was `true_hypothesis` present as a live hypothesis at `reveal_t - k` for k in {1, 5, 20}?
- **Lead time** — the first `t` at which `true_hypothesis` existed in the lattice.
- **Retrospective fit** — fraction of beats in `dormant_window` whose `bayes_factor(h_true, h_dominant)` exceeds 1. High = the clues were there.
- **Surprise curve** — per-beat change in readout belief toward `true_hypothesis`; the twist should show a spike at `reveal_t`, not before.
- **Calibration** — where `reader_beliefs` exist, Brier score of readouts against annotated beliefs.
- **Voiced-hypothesis agreement** — for play transcripts: does a hypothesis a player voiced at `t` appear in the engine's top-k at `t`?
- **Coverage** (RQ1) — fraction of beats that fill at least one step of any hypothesis, and fraction quarantined. A story the vocabulary cannot express shows up here first.

### 9.3 Consequences for the code

- Everything time-indexed (§4). `Lattice.at(chronicle, t)`, `Chronicle.visible_to(player, t)`, `Expectation` history per `t`.
- A `replay` management command: load a fixture story, run the pipeline beat by beat, store lattice and expectations at every `t`, export `evaluation/runs/<story>/<timestamp>.json`. Uses the LLM call cache, so a second run is free.
- The ingester must accept prose (`speaker: narrator`) and media (`speaker: <outlet>`) transcripts as well as table talk.
- Per-player lattices: the matcher must be runnable with a scope filter (`for_player`) so that a player's private backstory beats can complete a schema only in that player's view.
- **Context windowing for long stories.** The reader model cannot be fed a whole novel. The `ReaderModel` context is built by a `ContextBuilder` (tested, deterministic) that takes the player-visible chronicle prefix and returns a bounded context: the most recent N beats verbatim plus the beats that fill steps of the top-k live hypotheses. Which beats were included is recorded on the `LLMCall`. This is a modelling choice that affects RQ1 results; keep it swappable.
- Reader-model calls are logged with full prompt and candidate set (§8.4).

### 9.4 Evaluation for RQ3 and RQ4 (design now, implement in R2/R3)

- RQ3: a story written by the `StoryWriter` is itself a `literature` chronicle. Re-ingest it and compute the §9.2 metrics on it. Compare stories written with the lattice and target hypothesis in the prompt against stories written from the prose prefix alone. Note the circularity: the same reader model guides and judges; human ratings are required for the headline result, and the harness must export stories in a form a rater can read blind.
- RQ4: a `media` chronicle per event and outlet. Metrics: schema completion per outlet, overlap of filled steps between outlets, and completion *conditioned on factuality labels* — how much of a schema's weight rests on claims labeled `false` or `unverified`. Lattice comparison across chronicles is a new query, not a new model.

---

## 10. Project setup (concrete steps)

```bash
# 1. Project and Python version (uv creates .python-version and pyproject.toml)
uv init --python 3.12 narrative-engine && cd narrative-engine
# in pyproject.toml set:  requires-python = ">=3.12"

# 2. Dependencies
uv add "django>=5.2" "psycopg[binary]" pyyaml ollama httpx django-environ
uv add --dev pytest pytest-django factory-boy ruff mypy django-stubs

# 3. Django project and apps
uv run django-admin startproject narrative_engine .
for app in chronicle schemas matching reader llm evaluation gm_ui; do uv run python manage.py startapp $app; done
```

`pyproject.toml` additions:

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "narrative_engine.settings.test"
python_files = ["test_*.py"]
testpaths = ["chronicle", "schemas", "matching", "reader", "llm", "evaluation", "gm_ui"]
markers = ["llm: integration tests that call the Ollama server (deselected by default)"]
addopts = "-m 'not llm'"

[tool.ruff]
target-version = "py312"
line-length = 110

[tool.mypy]
python_version = "3.12"
plugins = ["mypy_django_plugin.main"]
```

Settings: `narrative_engine/settings/{base,dev,test}.py`. `test.py` uses SQLite in memory and binds `ReaderModel = TableReader`, `Ingester = FixtureIngester`. Dependency injection via a tiny registry (`narrative_engine/di.py`) read from settings — no framework needed.

Python ≥ 3.12 is a floor, not a target: PEP 695 `type` aliases and generic syntax are fine; do not use anything that requires 3.13+.

```bash
# 4. First failing test, then make it pass
mkdir -p gm_ui/tests && cat > gm_ui/tests/test_smoke.py <<'EOF'
import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_healthz(client):
    assert client.get(reverse("healthz")).status_code == 200
EOF
uv run pytest   # red → add the view and url → green

# 5. Pre-commit: ruff + mypy + pytest on changed apps
# 6. Commit uv.lock; CI runs `uv sync --frozen` then `uv run pytest`
```

Fixture helpers: `conftest.py` at the root provides `chronicle`, `players`, `entity_factory`, `beat_factory`, and `load_story(slug)` which populates a chronicle from `fixtures/stories/<slug>/`.

---

## 11. Milestones — tests first

Each milestone lists the tests to write *before* the implementation. A milestone is done when those tests pass and nothing in earlier milestones regresses. M0–M9 are the v1 core; R1–R4 are the research tracks built on it.

**M0 — Skeleton**
- `test_healthz` passes; CI runs `ruff`, `mypy`, `pytest`.
- `load_story("minimal")` loads a 5-beat hand-written story into a `session` chronicle.
- Creating a `literature` or `media` chronicle auto-creates its implicit player.

**M1 — Chronicle**
- Appending beats assigns consecutive `t`; appending with an explicit non-consecutive `t` raises.
- Beats are immutable: `save()` on an existing beat raises.
- `args` validation: unknown role for a predicate raises; wrong value kind raises; `prop` nesting validates recursively.
- Unknown predicate → stored as `unknown` with `quarantined` tag, does not raise.
- Entity view: an `is(trait)` beat creates/updates an `EntityAttribute` with `source_beat` set; rebuilding the view from scratch yields identical rows.
- `Utterance.source` round-trips chapter and outlet metadata.

**M2 — Scope**
- Initial grants are created from the ingester's presence info; for an implicit player, every beat is granted at `t`.
- A `learns(who, what=beat)` beat adds a grant to `what` with `via_beat` set.
- `known_by_chars_at(t)` excludes grants with `t' > t`.
- `visible_to(player, t)` returns exactly the beats with a player grant at or before `t`.
- A player's private backstory beat (granted only to that player) is absent from the table view and present in that player's view.

**M3 — Schema library**
- YAML loader round-trips the `betrayal` example from §6.
- Loader rejects: unknown predicate in a pattern, `$Role` not in `roles`, `$step` referring to a non-existent step, a `payoff_steps` entry that is not a step.
- Constraint objects deserialize to typed classes with `check(hypothesis, chronicle) -> bool`.

**M4 — Matcher**
- Pattern matching unit tests: wildcard, literal, bound var, unbound var (extension), `$step` reference, nested prop, `tags_any`, `scope` filter, `claimed_by`.
- Seeding: a `trusts(Mira, Aldric)` beat creates `Betrayal(T=Aldric, V=Mira)` with `trust` filled; a second identical beat does not create a duplicate (repeatable fill instead).
- Refinement: `Betrayal(T=?, V=Mira)` plus `helps(Aldric, Mira)` creates a child with `refines` set; parent remains live.
- Fill under existing binding: `steals(Aldric, S, from=Mira)` fills `harm` of the bound hypothesis only.
- Refutation: a beat matching `contradicts` sets `refuted`, `refuted_by`, `status_changed_at_t`.
- Constraint violation (`distinct`) refutes at Maintain.
- Weight arithmetic incl. repeatable cap.
- `complete` when all required steps are filled.
- **Replay:** running the `steward` fixture to the end and then calling `Lattice.at(chronicle, 20)` equals running it only to beat 20. This is the single most important test in the project.

**M5 — Voiced hypotheses**
- A player utterance tagged as a theory creates a hypothesis with `voiced_by` and `voiced_in`, bound as stated, even if no step is filled yet.
- A voiced hypothesis that matches an existing engine hypothesis is merged (engine hypothesis gains `voiced_by`), not duplicated.

**M6 — Reader model & expectations**
- Question construction: template per predicate, candidate list = in-scope entities of the role's kind + null; deterministic ordering; label assignment stable across calls.
- `ContextBuilder` returns the bounded context described in §9.3 and reports which beats it included.
- `TableReader` raises on unanticipated (t, question).
- Expectations are stored with `computed_at_t` and `for_player`; a per-player readout is fed only `visible_to(player, t)` (assert on the context passed to the reader).
- `bayes_factor` is called with the identical beat object under both hypotheses (assert).
- `LLMCall` cache: an identical request is served from the table; a changed parameter is not.
- `OllamaChoiceReader` integration test (`--llm`): the distribution over four labels sums to ≈ 1 after renormalization and the "none" label gets non-zero mass on an empty chronicle.

**M7 — Ingester & transcript replay**
- `FixtureIngester` yields the fixture's beats per utterance; a management command `replay <story>` runs the whole pipeline and writes a run file.
- Run file contains lattice and expectations at every `t`, plus the `LLMCall` ids used.
- `OllamaIngester` integration test (`--llm`): a three-sentence utterance yields valid beats that pass `args` validation; an utterance with no narrative content yields zero beats.

**M8 — GM / writer UI**
- Views: chronicle (filterable by player scope), lattice at `t` (default: now), expectations per hypothesis, "what does X know at t", "which hypotheses would this candidate beat strengthen" (dry-run `Matcher.step` on a draft beat without committing).
- Admin registered for all models; `Hypothesis` admin shows fills inline; `LLMCall` admin shows request/response.
- Every view interaction writes a `UsageEvent` (view, chronicle, t, params) — the raw material for RQ2.

**M9 — Evaluation harness**
- `metrics.py` functions unit-tested against a synthetic run file with known answers.
- `evaluate <story>` command computes all §9.2 metrics from a run file and prints a table.
- Two hand-authored stories under `fixtures/stories/` with full `ground_truth.yaml`; metric tests assert the engine reaches twist recall at k=5 on both.

**R1 — Literature and session corpora (RQ1)**
- Importers: plain-text / Gutenberg prose → `literature` chronicle (chapters and paragraphs as utterances); session transcript formats in use → `session` chronicle.
- Three public-domain stories with a known twist and at least one recorded session, with `ground_truth.yaml`, run end to end through `OllamaIngester` with human review of `beats.yaml`.
- Report: §9.2 metrics per story, coverage, and a list of beats the vocabulary could not express.

**R2 — Story generation (RQ3)**
- `StoryWriter` interface: `(chronicle prefix, lattice, target_hypothesis, expectations) -> (next beat draft, prose)`; `OllamaStoryWriter` implementation; `FixtureStoryWriter` for tests.
- `generate` command: write a story toward a target twist for N beats, re-ingest, evaluate.
- Paired comparison harness: with-structure vs. prose-only, same seed story, blind export for raters.

**R3 — Media corpora (RQ4)**
- Importer: article collection → `media` chronicle per event, outlet entities of kind `source`, every statement as a `says` claim beat.
- `FactLabel` import from a fact-checking source or annotation sheet.
- Cross-chronicle lattice comparison and the conditioned-completion metric from §9.4.

**R4 — Study instrumentation (RQ2)**
- Export of `UsageEvent` logs; session-level summaries of which engine outputs a GM/writer actually acted on; consent and anonymisation handling for recorded tables.

---

## 12. Conventions

- Tests live in `<app>/tests/`, one file per concept (`test_scope.py`, `test_matcher_seed.py`). Use factories, not raw fixtures, except for whole-story loads. Integration tests under `<app>/tests/integration/` with the `llm` marker.
- Every bug fix starts with a failing regression test that names the story and `t` where it was observed.
- The matcher, scope logic and metrics are pure functions over querysets or plain data where possible; keep Django ORM calls at the edges so unit tests can run on in-memory objects.
- No LLM call in the default test run, ever. `uv run pytest --llm` opts in; the server URL comes from the environment.
- `uv` only: `uv add` / `uv add --dev` for dependencies, `uv run` for every command, `uv.lock` committed, `uv sync --frozen` in CI. No `pip install`, no `requirements.txt`.
- Python ≥ 3.12 everywhere (`requires-python`, ruff and mypy targets). Fully typed public interfaces; the four injected interfaces (`Ingester`, `ReaderModel`, `StoryWriter`, `ContextBuilder`) are `typing.Protocol`s.
- Schema and vocabulary changes go through PR review; the YAML files are the spec.
- Fixture stories must be public domain or our own material; record provenance and chronicle kind in the fixture README. Media fixtures record the outlet and publication date per utterance and keep only the excerpts needed.
- Every feature PR names the research question it serves.

---

## 13. Deferred decisions (do not block on these)

- Full Rete vs. incremental join (§7) — decide after profiling with a 2000-beat chronicle, most likely the first media corpus.
- Bayes-factor backend — depends on whether the deployed Ollama version exposes forced-continuation logprobs (§8.3). If not, decide between a sidecar vLLM/llama.cpp server and the token-by-token fallback after measuring both on one fixture story.
- Reader model choice — fix one model for all RQ1 runs once the smoke check passes; changing it invalidates comparability.
- Weight calibration — v1 uses hand-set step weights; a logistic fit from engine log-odds to voiced/annotated beliefs comes after M9.
- Reader context format — v1 feeds compressed beat text through `ContextBuilder`; evaluating prose vs. canonical context for readouts is an experiment after R1.
- Pruning policy — v1: fixed weight floor and max live hypotheses per schema; revisit with evaluation data.
- Multi-session campaigns — v1 is one chronicle per session; a campaign is a later aggregation over chronicles.