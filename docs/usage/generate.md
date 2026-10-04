# Generating a story toward a twist

`generate` lets a language model continue a seed story toward a target twist, one paragraph at a
time, and evaluates the result (concept §9.4, RQ3). The model sees the story so far, the engine's
strongest readings of it, what the audience expects next and the twist to write toward. Each
paragraph is then read back by the ingester like any other text, so the evaluation measures what the
prose conveys, not what the model meant.

## Before you start
- The backend is installed and migrated, the schemas are loaded (`uv run python manage.py load_schemas`).
- The Ollama settings are configured (`docs/usage/ollama-smoke-check.md`), including the writing
  model: `OLLAMA_WRITER_MODEL=qwen3:32b` in `backend/.env` or the environment.

## Continue a story toward a twist
1. In `backend/`, run `uv run python manage.py generate steward --target "betrayal T=edda V=mira" --beats 6`.

**Result:** the command prints `Generated 6 continuations of steward toward betrayal (T = edda, V = mira); run file: …/evaluation/runs/steward-generated/<timestamp>.json`
and the metric table of `docs/usage/evaluate.md`, measured against the target: it counts as revealed
at the last beat, and the beats generated before it are the dormant window.

The generated story is a `literature` chronicle: the seed story followed by one narrator
utterance per paragraph. Each generated utterance records the writer (`source.generated_by`) and
the beat the model meant the paragraph to convey (`source.intended`), next to the beats the ingester
actually read from it. Running the command again with the same settings reproduces the story from
the LLM call log without asking the model.

## Readouts with the uniform reader
1. Run the same command with `--reader uniform`.

**Result:** the same story; the expectations the writer sees, and the reader-based metrics, come from
the know-nothing baseline instead of the language model.

## A target that does not fit the seed story
1. Run `uv run python manage.py generate steward --target "betrayal T=nobody" --beats 6`.

**Result:** the command stops with `--target: unknown entity 'nobody'`. A target without roles
(`--target betrayal`) stops with `a target is a schema and its binding, e.g. 'betrayal T=aldric V=mira'`.
