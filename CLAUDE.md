# Project instructions for Claude

You are developing a web application: a Django backend and a React frontend in one
monorepo. Read `docs/narrative-engine-concept.md` before starting any session. It 
describes the product and most of the planned work packages.

## Working principles (in priority order)

1. **Readable code over clever code.** Code is read far more often than written.
   Choose clear names, small functions, shallow nesting and obvious data flow.
   If a reader needs a comment to understand *what* code does, rewrite the code;
   use comments only to explain *why*.
2. **Test-driven development, always.** No production code without a failing test
   that demands it. Follow red → green → refactor strictly (see the `work-package` skill).
3. **Small, testable work packages.** Never work on more than one work package at a
   time. Each one ends in a green test suite, updated docs and a single focused commit.
4. **Researched infrastructure decisions.** Before choosing a library, tool, structure
   or configuration approach, research what experienced developers recommend
   (see the `infra-decision` skill) and record the decision as an ADR.
5. **Documentation is part of "done".** Every user-facing feature gets usage
   documentation written so that it can drive browser tests (see the `usage-docs` skill).

## Repository layout

- `backend/` — Django project (Python). Tests live next to the app they test.
- `frontend/` — React app. Component and unit tests live next to the components.
- `e2e/` — end-to-end browser tests, derived from `docs/usage/`.
- `docs/idea.md` — product description (owned by the human; propose edits, don't rewrite).
- `docs/work-packages/` — one file per work package, `WP-NNN-short-name.md`.
- `docs/decisions/` — architecture decision records, `ADR-NNN-short-name.md`.
- `docs/usage/` — user documentation, one file per feature or workflow.
- `.claude/skills/` — the workflows referenced in this file.

If the layout does not exist yet, the first work package is creating it.

## Session workflow

1. Read `docs/idea.md`, `docs/work-packages/` and the latest ADRs.
2. If the work packages are not yet split into files, do that first: propose the
   split, ordered by dependency, and wait for confirmation before coding.
3. Pick the next open work package (or the one the user names). State which one
   you are working on and its acceptance criteria before writing any code.
4. Implement it using the `work-package` skill.
5. Finish with: all tests green, linters clean, usage docs updated, work package
   file marked done with a short summary, one commit with a descriptive message.

Stop and ask the user when: acceptance criteria are ambiguous, a decision would
contradict an existing ADR, or a work package turns out to be much bigger than
planned (propose a split instead of pushing through).

## Code style

- Python: follow PEP 8, type hints on public functions, format with the formatter
  chosen in the ADRs. Prefer Django's conventions over custom abstractions.
- TypeScript/React: strict TypeScript, function components and hooks, one
  component per file, keep components small and presentational where possible.
- Names describe intent (`overdue_invoices`, not `data2`). No abbreviations
  that a newcomer would have to look up.
- Functions do one thing. If you need "and" to describe a function, split it.
- Prefer early returns over deep nesting. Avoid premature generalization:
  three similar cases come before an abstraction, not one.
- Delete dead code instead of commenting it out.
- Refactoring is part of every red-green-refactor cycle, not a later task.

## Testing

- Backend: unit tests for models/services, API tests for endpoints.
- Frontend: tests that exercise components the way a user would
  (by role, label and text, not implementation details).
- E2E: browser tests for every scenario listed in `docs/usage/`.
- Tests are documentation too: descriptive names that read as behavior
  (`test_user_cannot_see_other_users_projects`).
- Never weaken, skip or delete a failing test to make the suite pass. If a test
  is wrong, say so and explain why before changing it.

## Commits

- One work package per commit (or a few commits if the package is large, each green).
- Message format: `WP-NNN: imperative summary` plus a short body explaining why.
