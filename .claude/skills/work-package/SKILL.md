---
name: work-package
description: Implement one work package with strict test-driven development. Use whenever starting, continuing or finishing a work package (WP-NNN), or when planning/splitting work into packages.
---

# Implementing a work package

## Planning a split
A good work package:
- delivers one observable behavior (an endpoint, a screen, a rule),
- can be verified by tests alone,
- is small enough to finish in one session,
- lists its dependencies on other packages.

Each package file in `docs/work-packages/WP-NNN-name.md` contains:
`Goal`, `Acceptance criteria` (as testable statements), `Dependencies`,
`Out of scope`, `Status` (open / in progress / done) and, when done, `Summary`.

## The TDD loop
Repeat for each acceptance criterion:

1. **Red** — write the smallest test that expresses the next bit of behavior.
   Run it and confirm it fails *for the expected reason*. Show the failure.
2. **Green** — write the simplest code that makes it pass. No extra features.
3. **Refactor** — with tests green, improve names, remove duplication, simplify.
   Run the full relevant suite again.

Work outside-in where it helps: an API or UI-level test first, then unit tests
for the pieces it needs.

## Definition of done
- [ ] Every acceptance criterion has at least one test
- [ ] Full backend and frontend test suites pass
- [ ] Linters and formatters pass
- [ ] `docs/usage/` updated for user-facing changes (use the `usage-docs` skill)
- [ ] E2E tests added or updated for new usage scenarios
- [ ] Work package file set to done with a 2–4 sentence summary
- [ ] Committed as `WP-NNN: ...`
