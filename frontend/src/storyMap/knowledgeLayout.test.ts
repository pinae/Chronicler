import { describe, expect, it } from "vitest";

import { fuses, howKnown } from "./knowledgeLayout";

function column(...known: [number, number, number | null][]) {
  return {
    player: 5,
    name: "Anna",
    known: known.map(([t, known_since_t, learned_via_t]) => ({ t, known_since_t, learned_via_t })),
  };
}

describe("fuses", () => {
  it("runs a fuse from each beat learned later down to the beat at which it was learned", () => {
    const anna = column([1, 1, null], [2, 30, 30], [27, 27, null]);

    expect(fuses(anna)).toEqual([{ t: 2, knownSinceT: 30, lane: 0 }]);
  });

  it("nests a fuse that starts while another burns inside it, so that no fuse crosses another", () => {
    const anna = column([2, 30, 30], [3, 26, 26], [28, 31, 31], [32, 33, null]);

    expect(fuses(anna)).toEqual([
      { t: 2, knownSinceT: 30, lane: 1 },
      { t: 3, knownSinceT: 26, lane: 0 },
      { t: 28, knownSinceT: 31, lane: 0 },
      { t: 32, knownSinceT: 33, lane: 0 },
    ]);
  });

  it("keeps a fuse that starts where another ends clear of its spark", () => {
    const anna = column([2, 26, 26], [26, 30, 30]);

    expect(fuses(anna)).toEqual([
      { t: 2, knownSinceT: 26, lane: 1 },
      { t: 26, knownSinceT: 30, lane: 0 },
    ]);
  });
});

describe("howKnown", () => {
  it("says whether a player knew a beat when it happened, learned or was shown it later, or not at all", () => {
    expect(howKnown({ t: 3, known_since_t: 3, learned_via_t: null })).toBe("when it happened");
    expect(howKnown({ t: 3, known_since_t: 26, learned_via_t: 26 })).toBe("learned at t = 26 via beat 26");
    expect(howKnown({ t: 3, known_since_t: 8, learned_via_t: null })).toBe("shown at t = 8");
    expect(howKnown(undefined)).toBe("not learned");
  });
});
