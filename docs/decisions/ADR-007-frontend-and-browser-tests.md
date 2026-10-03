# ADR-007: Frontend toolchain, serving and browser tests

**Status:** accepted (2026-10-03) · **Work package:** WP-034

## Context
The GM/writer screens are a React app in `frontend/` (ADR-001) on top of the JSON API (ADR-006). We
need a build tool, a component test stack that tests the way a user works (by role, label and text),
linting and formatting, browser tests derived from `docs/usage/`, a way for the frontend to reach the
API in development, and a way to serve it in production. Strict TypeScript; small team.

## Options considered
- **Build:** Vite (the React team's recommended build tool for apps without a framework, after
  deprecating Create React App) vs. a framework such as Next.js (server rendering we do not need;
  Django already is the server).
- **Component tests:** Vitest + Testing Library (shares Vite's configuration) vs. Jest (separate
  transform setup).
- **Lint/format:** ESLint + typescript-eslint + react-hooks plugin + Prettier vs. Biome (much faster,
  one tool, but it does not yet cover the React hooks rules).
- **Browser tests:** Playwright vs. Cypress. Playwright is the common choice for new projects and
  is pre-installed in our development containers.
- **Serving:** two origins with CORS vs. one origin: Vite's dev proxy in development, Django serving
  the build in production and in browser tests.

## Decision
- Vite 8, React 19, React Router 8, TypeScript 5.9 (strict, `noUncheckedIndexedAccess`). TypeScript 6/7
  wait until typescript-eslint and openapi-typescript support them.
- Vitest 5 with jsdom 29, Testing Library and user-event; components are tested by role, label and text.
- ESLint 10 with typescript-eslint (strict) and eslint-plugin-react-hooks, Prettier for formatting
  (line length 110, as in Python).
- API types are generated from the backend's OpenAPI schema with openapi-typescript
  (`npm run generate:api-types`); CI fails when they are out of date.
- Development: `npm run dev` proxies `/api` and `/admin` to Django on port 8000.
- Production and browser tests: Vite builds with base `/static/`; Django serves `frontend/dist/` as
  static files through WhiteNoise and returns its `index.html` for every path it does not answer
  itself (`gm_ui.views.frontend_app`). One origin, no CORS.
- Playwright 1.56.1, Chromium only, in `e2e/`. It is pinned to the browser build pre-installed in our
  development containers; CI installs the same build. Each scenario of `docs/usage/` is one test, named
  after the scenario. Tests seed a throwaway SQLite database (`settings.e2e`) through
  `manage.py seed_e2e`, which refuses to run with any other settings.

## Reasoning
- React's documentation points to Vite for single-page apps since Create React App was deprecated
  ([PkgPulse: stop using CRA](https://www.pkgpulse.com/guides/stop-using-create-react-app-2026),
  [Build5Nines: CRA deprecated](https://build5nines.com/create-react-app-is-now-deprecated-time-to-migrate-to-vite-or-next-js/),
  [patterns.dev: React stack 2026](https://www.patterns.dev/react/react-2026/)).
- Biome is recommended for speed but does not yet replace eslint-plugin-react-hooks
  ([Biome vs ESLint 2026](https://reintech.io/blog/typescript-biome-vs-eslint-linting-formatting-comparison-2026),
  [PkgPulse: Biome vs ESLint vs Oxlint](https://www.pkgpulse.com/guides/biome-vs-eslint-vs-oxlint-2026)).
  The hooks rules catch real bugs, so we keep ESLint.
- Serving the built SPA from Django keeps one origin for the API, admin and app, avoiding CORS and a
  split deployment; the Vite proxy gives the same paths in development
  ([single-origin Vite SPA from Django](https://github.com/sean7084/FinanceAnalysis/issues/18),
  [reverse proxy pattern for Vite](https://docs.sadeeminfo.com/blog/reverse-proxy-vite-pattern/)).
- Versions checked on the npm registry on 2026-10-03; jsdom 29 because jsdom 30 needs Node 22.22.2.

## Consequences
- Running the app outside development needs `npm run build` first (Django answers 503 with that hint).
- Browser tests are slower than unit tests and run in their own CI job.
- Changing an API schema means regenerating the frontend types in the same commit.
