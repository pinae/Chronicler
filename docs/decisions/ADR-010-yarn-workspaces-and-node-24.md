# ADR-010: Yarn 4 workspaces and Node 24

**Status:** accepted (2026-10-04) · **Work package:** WP-064 · Supersedes the package manager and
the versions of ADR-007; serving, testing approach and tools stand.

## Context
The project owner asked to switch from npm to Yarn and to bring the frontend stack up to date. The
JavaScript side has two packages, `frontend/` (the React app) and `e2e/` (Playwright), each with its
own `package-lock.json`, installed and cached separately in CI.

## Options considered
- **Yarn version:** Yarn 1 (Classic, frozen) vs. Yarn 4 (Berry, maintained). Only Yarn 4 is
  developed further.
- **Getting Yarn:** Corepack with the `packageManager` field (the Yarn documentation's way) vs. a
  `yarnPath` binary committed to `.yarn/releases/`. Corepack is no longer bundled from Node 25 on,
  but installs with `npm install -g corepack`.
- **Linker:** Plug'n'Play (Yarn's default, no `node_modules`) vs. `nodeLinker: node-modules`.
- **Layout:** two independent Yarn projects vs. one root with `frontend` and `e2e` as workspaces.
- **Node:** stay on 22 (maintenance LTS) vs. 24 (active LTS).

## Decision
- **Yarn 4.18.1** through **Corepack**: `"packageManager": "yarn@4.18.1"` in the root
  `package.json`; developers run `corepack enable` once.
- **Workspaces** `frontend` and `e2e` under one root `package.json` and one `yarn.lock`;
  `yarn install` in the root installs both, `yarn workspace chronicler-frontend build` builds the
  app from anywhere.
- **`nodeLinker: node-modules`** in `.yarnrc.yml`, telemetry off. Yarn's default minimum release
  age (packages younger than one day are quarantined) stays on.
- **Node 24 LTS** in `.node-version` (CI reads it); `engines` allows `^22.22.2 || ^24.15.0 || >=26`,
  the range of the strictest dependency (jsdom 30).
- **Versions** (registry, 2026-10-04): TypeScript 6.0.3, jsdom 30.1.1, Playwright 1.63.0,
  @types/node 24; React 19.3, React Router 8.4, Vite 8.3, Vitest 5.0, ESLint 10.12 and
  typescript-eslint 8.71 were already the latest. `@testing-library/dom` is now a direct dependency:
  npm installed peer dependencies automatically, Yarn does not.
- CI runs `corepack enable` before `actions/setup-node` (with `cache: yarn`) and installs with
  `yarn install --immutable`.
- Playwright no longer has to match the Chromium build pre-installed in development containers:
  `CHROMIUM_EXECUTABLE` points it to that browser; CI installs the matching one.

## Reasoning
- Yarn recommends Corepack and the `packageManager` field so that the package manager version is
  locked like the dependencies ([Yarn: installation](https://yarnpkg.com/getting-started/install),
  [Yarn: Corepack](https://yarnpkg.com/corepack)); from Node 25 on, Corepack is installed with npm
  ([nodejs/corepack](https://github.com/nodejs/corepack),
  [Trevor Lasn: Corepack](https://www.trevorlasn.com/blog/corepack-nodejs)).
- Plug'n'Play does not work with Vite 8's Rolldown bundler, and switching to `node-modules` fixes it
  ([yarnpkg/berry#7071](https://github.com/yarnpkg/berry/issues/7071)); experience reports call
  `node-modules` the safer choice with Vite, Vitest, Playwright and ESLint
  ([PkgPulse: package managers 2026](https://www.pkgpulse.com/guides/pnpm-vs-npm-vs-yarn-package-managers-2026),
  [Better Stack: pnpm vs Bun vs Yarn Berry](https://betterstack.com/community/guides/scaling-nodejs/pnpm-vs-bun-install-vs-yarn/)).
- `actions/setup-node` with `cache: yarn` fails for a `packageManager` Yarn unless Corepack is
  enabled first ([actions/setup-node#1027](https://github.com/actions/setup-node/issues/1027),
  [Yarn Modern and GitHub Actions](https://blog.dylants.com/posts/20240129/yarn-modern-2-and-git-hub-actions)).
- TypeScript 7 waits: typescript-eslint supports `>=4.8.4 <6.1.0`. openapi-typescript declares
  TypeScript `^5` as a peer but generates the identical schema file with 6.0.3; Yarn reports this
  as a peer warning (YN0060), which `packageExtensions` cannot silence because it only adds peers.

## Consequences
- One install for both workspaces and one lock file to review.
- Contributors need Corepack (`corepack enable`; on Node 25+ `npm install -g corepack` first).
- `yarn install` prints the openapi-typescript peer warning until it accepts TypeScript 6.
- A package published within the last day cannot be added until it is a day old.
