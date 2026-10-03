---
name: infra-decision
description: Research and record an infrastructure or architecture decision. Use before choosing a library, framework add-on, build tool, folder structure, auth approach, database setup, testing tool, CI, deployment or any configuration that would be costly to change later.
---

# Making an infrastructure decision

## 1. Frame the question
Write down the decision in one sentence and the constraints that matter
(this stack, monorepo, TDD, readability, small team).

## 2. Research what experienced developers do
Search the web. Prefer, in this order:
1. Official documentation and recommendations (Django, React, the tool itself)
2. Well-known maintainers and practitioners (core contributors, established
   blogs, conference talks, books)
3. Widely used, actively maintained open-source projects with the same stack —
   look at how they actually solved it
4. Experience reports describing problems after real use

Treat SEO listicles, AI-generated content and undated posts with suspicion.
Check that advice is current (release dates, maintenance status, last commit).
Look for at least 2–3 independent sources and note where they disagree.

## 3. Decide
Prefer boring, well-supported, conventional choices. Choose the option a new
developer joining the project would find least surprising.

## 4. Record an ADR
Create `docs/decisions/ADR-NNN-short-name.md`:

- **Context** — the question and constraints
- **Options considered** — 2–4 options, one line each on pros/cons
- **Decision** — what was chosen
- **Reasoning** — why, with links to the sources
- **Consequences** — what this makes easier or harder

For decisions that are hard to reverse, present the ADR to the user and wait
for confirmation before implementing.
