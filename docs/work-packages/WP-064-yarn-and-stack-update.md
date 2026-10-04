# WP-064: Yarn 4 workspaces and an updated frontend stack

**Milestone:** M8 (follow-up) · **Serves:** maintenance

## Goal
The JavaScript side uses Yarn instead of npm, as the project owner asked, with the frontend stack
at its current versions.

## Acceptance criteria
- A root `package.json` declares Yarn 4 (`packageManager`) and the workspaces `frontend` and `e2e`;
  one `yarn.lock` replaces both `package-lock.json` files.
- Lint, format check, type check, component tests, the API type check and all browser tests pass
  with Yarn on Node 24.
- CI, the pre-commit hooks, the README, the usage docs and the backend's "build the frontend first"
  message use Yarn.
- ADR-010 records the choices.

## Dependencies
WP-034.

## Out of scope
The new interface (WP-066 and later).

## Status
done

## Summary
Yarn 4.18.1 through Corepack with `nodeLinker: node-modules` (Plug'n'Play breaks Vite 8), Node 24
LTS, TypeScript 6.0.3, jsdom 30.1.1, Playwright 1.63.0; the rest was already current.
`@testing-library/dom` became an explicit dependency because Yarn does not install peers. Playwright
can drive a pre-installed Chromium of another build through `CHROMIUM_EXECUTABLE`.
