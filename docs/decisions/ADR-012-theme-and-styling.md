# ADR-012: A steampunk theme with design tokens, CSS Modules and self-hosted fonts

**Status:** accepted (2026-10-04) · **Work package:** WP-066

## Context
The project owner asked for a nice interface in a steampunk fantasy theme, fitting a tool for
roleplaying games. The frontend has no styling yet. The theme has to stay readable for long
sessions, work in light and dark, keep every accessible name the tests and usage docs rely on, and
carry the chart palette of ADR-011.

## Options considered
- **Tailwind CSS 4**: the most common choice in new React projects, tokens as CSS variables; but a
  theme of ornamental frames, textures and pseudo-elements turns into long utility strings or
  custom CSS anyway, and markup reads worse.
- **CSS Modules with CSS custom properties**: built into Vite, no dependency, class names that say
  what an element is; consistency comes from using the tokens, not from a framework.
- **CSS-in-JS** (styled-components, vanilla-extract): runtime cost or a build plugin, for little gain.

## Decision
- **Design tokens as CSS custom properties** in `src/theme/tokens.css`: surfaces (parchment, panel,
  sunken), inks (ink, muted), brass, copper and iron for ornament, accent and link, the five schema
  colours, spacing, radii and fonts. A light theme ("parchment and brass") and a dark one ("night
  workshop"), chosen by `prefers-color-scheme` and overridable with `data-theme` on `<html>`.
- **CSS Modules** (`Component.module.css`) next to each component, using only tokens for colours,
  spacing and fonts; global styles (`src/theme/global.css`) only for elements and the page.
- **Fonts self-hosted with Fontsource**: *Cinzel* (Roman capitals, for headings and the brand) and
  *Crimson Pro* (a readable book face, for text and tables, with lining tabular figures in tables).
  No request to a font CDN, so the app works offline and leaks nothing.
- Ornament stays out of the way of reading: brass frames, rivets and gear motifs on headers, panels
  and buttons, never behind text; motion respects `prefers-reduced-motion`.
- Text colours meet WCAG AA (4.5:1) on both surfaces; measured: ink 12.5–15.0, muted 6.7–9.7,
  accent 5.4–8.5, link 7.2–10.1.

## Reasoning
- Vite supports CSS Modules out of the box; tokens in custom properties work with any approach and
  are what Tailwind 4 itself compiles to
  ([PkgPulse: CSS Modules vs Tailwind 2026](https://www.pkgpulse.com/guides/css-modules-vs-tailwind-2026),
  [Design tokens vs CSS variables vs Tailwind](https://adamarant.com/en/blog/design-tokens-vs-css-variables-vs-tailwind-what-each-one-solves)).
- Self-hosting fonts avoids third-party requests (privacy, offline use at the gaming table);
  Fontsource packages them as npm dependencies.

## Consequences
- Discipline instead of enforcement: a colour written in a module instead of a token is a review
  finding.
- Changing the look means editing tokens and modules, not markup.
