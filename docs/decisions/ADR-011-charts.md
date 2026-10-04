# ADR-011: Charts drawn by React with d3's geometry, in a validated schema palette

**Status:** accepted (2026-10-04) · **Work package:** WP-065

## Context
The story map (docs/research/visualizations.md) needs charts no chart library ships: a vertical
river of readings aligned row by row with an HTML beat list, hatched regions for what only the game
master knows, event glyphs on the bands, arcs between beats. They must be testable the way the rest
of the frontend is (by role, label and text), keyboard- and screen-reader-accessible, and readable
for people with colour-vision deficiency, in a light and a dark theme.

## Options considered
- **A chart library** (Recharts, Observable Plot): fast for standard charts; a vertical stream
  aligned with table rows, hatching per region and arcs would fight the library.
- **visx** (Airbnb): React components over d3's math; capable, but one more abstraction and a set
  of packages for what three d3 modules and plain SVG elements do.
- **d3-scale and d3-shape for the math, React for the SVG**: the commonly recommended split (both
  libraries want to own the DOM; only one should), small dependencies, plain SVG that tests can query.

## Decision
- **d3-scale** and **d3-shape** compute positions and paths; **React renders the SVG**. No d3
  selections, no d3-managed DOM.
- The layout (which bands, how wide, where events sit) is computed in **pure functions** with unit
  tests; components only draw.
- **Colour means schema**, from one categorical palette in the theme tokens (ADR-012), assigned by a
  fixed map so a schema keeps its colour everywhere:

  | Schema | Light (surface `#f8f1e1`) | Dark (surface `#2a231c`) |
  |---|---|---|
  | Betrayal (oxblood) | `#8b3b3b` | `#bb584d` |
  | Usurpation (brass) | `#95761a` | `#b38c15` |
  | Blame (verdigris) | `#0f9b89` | `#29a895` |
  | Hidden crime (cobalt) | `#5283e0` | `#3e96ea` |
  | Prophecy (plum) | `#82439d` | `#9760af` |

  Validated with the data-visualization skill's validator in both modes with **all pairs**
  compared (any two schemas can end up side by side in the river): lightness band, chroma floor,
  colour-vision separation (worst ΔE 12.3 light, 9.5 dark; target 8), normal-vision floor (15.4 and
  15.1; floor 15) and 3:1 contrast all pass. A sixth schema gets the neutral "other" colour and its
  name until the palette is re-validated with it; colours are never generated.
- **Texture means secret**: a 45° hatching marks what only the game master holds, so the fact does
  not rest on colour.
- Every chart has a **table view** with the same numbers, a **tooltip** on every mark, an
  accessible name (`role="img"` with a label, or a labelled table), and a legend.

## Reasoning
- "Let React own the DOM and let D3 own math, scales and layout" is the prevailing advice for
  combining them ([SitePoint: D3 and React](https://www.sitepoint.com/d3-js-react-interactive-data-visualizations/),
  [React + D3: balancing performance and developer experience](https://medium.com/@tibotiber/react-d3-js-balancing-performance-developer-experience-4da35f912484));
  visx packages are themselves this split behind a component API
  ([Introducing visx](https://medium.com/airbnb-engineering/introducing-visx-from-airbnb-fd6155ac4658)).
- d3-scale 4 and d3-shape 3 are stable and complete; their age is maturity, not neglect.
- Palette method and checks: the data-visualization skill (fixed order, lightness band, chroma
  floor, CVD separation under Machado et al. simulation, normal-vision floor, contrast).

## Consequences
- Each new view is a small amount of SVG code plus a pure layout function; no chart library
  upgrades to follow.
- Charts need their own tooltip and table components (shared across views).
