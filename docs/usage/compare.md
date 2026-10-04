# Comparing writers and exporting stories for raters

`compare` asks whether the engine's structure helps a language model write a twist (RQ3). Two
writers continue the same seed story toward the same target with the same settings: one sees the
engine's readings, the audience's expectations and the target (`with structure`), the other sees
only the story so far (`prose only`). Both stories are measured against the target and exported for
human raters who must not know which writer wrote which. Because the same reader model guides and
judges, the raters' verdict carries the headline result (concept §9.4).

## Before you start
- Everything `docs/usage/generate.md` needs, including `OLLAMA_WRITER_MODEL`.

## Compare the two writers
1. In `backend/`, run
   `uv run python manage.py compare ferryman --target "betrayal T=bram V=oskar" --beats 6 --export-dir ~/rq3/ferryman-bram`.

**Result:** the command prints `Compared 2 writers continuing ferryman toward betrayal (T = bram, V = oskar)`,
then a table with one row per metric of `docs/usage/evaluate.md` and the columns **with structure**
and **prose only**, and finally where the stories for raters and the key were written. The run
files are `evaluation/runs/ferryman-with-structure/…` and `evaluation/runs/ferryman-prose-only/…`.

## Hand the stories to raters
1. Open `~/rq3/ferryman-bram/for-raters/`.

**Result:** two Markdown files named by random ids (e.g. `3fa94c1e.md`), each the whole story with
its title and one paragraph per utterance. Nothing in them says which writer wrote it.

2. Keep `~/rq3/ferryman-bram/condition-key.json` to yourself.

**Result:** it maps each id to its writer (`with-structure` or `prose-only`); share only the
`for-raters` folder.
