import { area, curveMonotoneY } from "d3-shape";

import type { RiverColumn } from "../api/types";

/** The surface gap between neighbouring bands (dataviz: 2px). */
export const GAP = 2;
export const OTHER = "other";

export type BandPoint = {
  t: number;
  x0: number;
  x1: number;
  share: number;
  secret: boolean;
  status: string | null;
};

/** One thread's band through the beats, or the band of all other readings. */
export type Band = {
  key: string;
  threadId: number | null;
  schemaSlug: string | null;
  points: BandPoint[];
};

export type Glyph = {
  t: number;
  x: number;
  y: number;
  kind: string;
  threadId: number;
  steps: string[];
};

export function rowCenter(t: number, rowHeight: number): number {
  return (t - 1) * rowHeight + rowHeight / 2;
}

/** At every beat from t = 1, the bands of the column side by side, each as wide as its share of
 * `width` (less the gaps); a band not held at a beat pinches to nothing where it would be. */
export function bandLayouts(column: RiverColumn, width: number): Band[] {
  const bands: Band[] = [
    ...column.threads.map((thread) => ({
      key: String(thread.id),
      threadId: thread.id,
      schemaSlug: thread.schema_slug,
      points: [],
    })),
    { key: OTHER, threadId: null, schemaSlug: null, points: [] },
  ];
  for (const moment of column.moments.filter((moment) => moment.t > 0)) {
    const shares = new Map(moment.shares.map((share) => [String(share.thread), share]));
    const entryOf = (band: Band) =>
      band.key === OTHER ? { share: moment.other, secret: false, status: null } : shares.get(band.key);
    const present = bands.filter((band) => (entryOf(band)?.share ?? 0) > 0);
    const available = width - GAP * Math.max(0, present.length - 1);
    let x = 0;
    for (const band of bands) {
      const entry = entryOf(band);
      const share = entry?.share ?? 0;
      const bandWidth = share * available;
      band.points.push({
        t: moment.t,
        x0: x,
        x1: x + bandWidth,
        share,
        secret: share > 0 && Boolean(entry?.secret),
        status: share > 0 ? (entry?.status ?? null) : null,
      });
      if (share > 0) {
        x += bandWidth + GAP;
      }
    }
  }
  return bands.filter((band) => band.points.some((point) => point.share > 0));
}

/** The beats at which only the game master holds the band's thread. */
export function secretRows(band: Band): number[] {
  return band.points.filter((point) => point.secret).map((point) => point.t);
}

/** One glyph per thread, beat and kind of event, on the middle of the band; a refuted thread's band
 * has ended at its refutation, so its cross sits where the band was before. */
export function glyphs(column: RiverColumn, bands: Band[], rowHeight: number): Glyph[] {
  const grouped = new Map<string, Glyph>();
  for (const event of column.events.filter((event) => event.t > 0)) {
    const band = bands.find((candidate) => candidate.threadId === event.thread);
    const center = band && centerAt(band, event.t);
    if (center === undefined) {
      continue;
    }
    const key = `${event.thread}:${event.t}:${event.kind}`;
    const glyph = grouped.get(key) ?? {
      t: event.t,
      x: center,
      y: rowCenter(event.t, rowHeight),
      kind: event.kind,
      threadId: event.thread,
      steps: [],
    };
    if (event.step) {
      glyph.steps.push(event.step);
    }
    grouped.set(key, glyph);
  }
  return [...grouped.values()];
}

function centerAt(band: Band, t: number): number | undefined {
  const visible = band.points.filter((point) => point.t <= t && point.share > 0);
  const point = visible.at(-1);
  return point && (point.x0 + point.x1) / 2;
}

/** The band as an SVG path, flowing smoothly from row to row and filling the first and last rows. */
export function bandPath(band: Band, rowHeight: number): string {
  const first = band.points[0];
  const last = band.points.at(-1);
  if (!first || !last) {
    return "";
  }
  const points = [
    { ...first, y: 0 },
    ...band.points.map((point) => ({ ...point, y: rowCenter(point.t, rowHeight) })),
    { ...last, y: last.t * rowHeight },
  ];
  const shape = area<(typeof points)[number]>()
    .y((point) => point.y)
    .x0((point) => point.x0)
    .x1((point) => point.x1)
    .curve(curveMonotoneY);
  return shape(points) ?? "";
}
