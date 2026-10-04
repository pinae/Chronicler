import { describe, expect, it } from "vitest";

import type { RiverColumn } from "../api/types";
import { GAP, bandLayouts, glyphs, rowCenter, secretRows } from "./riverLayout";

const PLOT_WIDTH = 100 + GAP;

function thread(id: number, schema: string) {
  return { id, schema_slug: schema, schema_name: schema, binding: [] };
}

function share(threadId: number, value: number, secret = false) {
  return { thread: threadId, share: value, status: "live", secret };
}

const COLUMN: RiverColumn = {
  audience: "all",
  name: "All beats",
  threads: [thread(7, "betrayal"), thread(9, "hidden_crime")],
  moments: [
    { t: 0, shares: [], other: 0 },
    { t: 1, shares: [share(7, 1)], other: 0 },
    { t: 2, shares: [share(7, 0.75), share(9, 0.25, true)], other: 0 },
    { t: 3, shares: [share(9, 0.5, true)], other: 0.5 },
  ],
  events: [
    { t: 2, thread: 9, kind: "filled", step: "crime" },
    { t: 3, thread: 7, kind: "refuted", step: null },
  ],
};

describe("bandLayouts", () => {
  it("fills the width with the shares of a beat, separated by gaps", () => {
    const [betrayal, crime] = bandLayouts(COLUMN, PLOT_WIDTH);

    expect(betrayal?.points[1]).toMatchObject({ t: 2, x0: 0, x1: 75 });
    expect(crime?.points[1]).toMatchObject({ t: 2, x0: 75 + GAP, x1: 100 + GAP });
  });

  it("starts at beat 1 and leaves out the moment before the first beat", () => {
    const [betrayal] = bandLayouts(COLUMN, PLOT_WIDTH);

    expect(betrayal?.points.map((point) => point.t)).toEqual([1, 2, 3]);
  });

  it("pinches a thread to nothing where it is not held", () => {
    const [betrayal, crime] = bandLayouts(COLUMN, PLOT_WIDTH);

    expect(crime?.points[0]).toMatchObject({ t: 1, share: 0 });
    expect(crime?.points[0]?.x1).toBe(crime?.points[0]?.x0);
    expect(betrayal?.points[2]).toMatchObject({ t: 3, share: 0, x0: 0, x1: 0 });
  });

  it("puts the other readings last", () => {
    const bands = bandLayouts(COLUMN, PLOT_WIDTH);

    expect(bands.map((band) => band.key)).toEqual(["7", "9", "other"]);
    expect(bands[2]?.points[2]).toMatchObject({ t: 3, x0: 50 + GAP, x1: 100 + GAP });
  });
});

describe("rowCenter", () => {
  it("is the middle of the beat's row", () => {
    expect(rowCenter(1, 30)).toBe(15);
    expect(rowCenter(3, 30)).toBe(75);
  });
});

describe("secretRows", () => {
  it("lists the beats at which only the game master holds the thread", () => {
    const crime = bandLayouts(COLUMN, PLOT_WIDTH).find((band) => band.key === "9");

    expect(crime && secretRows(crime)).toEqual([2, 3]);
  });
});

describe("glyphs", () => {
  it("sits an event on the middle of its band at its beat", () => {
    const bands = bandLayouts(COLUMN, PLOT_WIDTH);

    const [filled] = glyphs(COLUMN, bands, 30);

    expect(filled).toMatchObject({ t: 2, kind: "filled", threadId: 9, steps: ["crime"] });
    expect(filled?.x).toBe((75 + GAP + 100 + GAP) / 2);
    expect(filled?.y).toBe(45);
  });

  it("marks a refutation where the band was before it ended", () => {
    const bands = bandLayouts(COLUMN, PLOT_WIDTH);

    const refuted = glyphs(COLUMN, bands, 30).find((glyph) => glyph.kind === "refuted");

    expect(refuted).toMatchObject({ t: 3, threadId: 7, x: 75 / 2, y: 75 });
  });
});
