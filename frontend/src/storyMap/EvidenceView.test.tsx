import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import type { River } from "../api/types";
import { EvidenceView } from "./EvidenceView";

const BEATS = [
  { t: 1, pred: "harms", text: "The jug is broken.", source_kind: "narration", quarantined: false },
  { t: 2, pred: "hides", text: "Adam hides what he did.", source_kind: "narration", quarantined: false },
  { t: 3, pred: "is_at", text: "Walter arrives.", source_kind: "narration", quarantined: false },
  { t: 4, pred: "is_at", text: "Ruprecht was elsewhere.", source_kind: "narration", quarantined: false },
];

function thread(id: number, culprit: string) {
  return {
    id,
    schema_slug: "hidden_crime",
    schema_name: "Hidden crime",
    binding: [{ role: "C", entity_id: id, entity_name: culprit }],
    open_steps: [],
    waiting_since: null,
  };
}

function moment(t: number, shares: [number, number][]) {
  return {
    t,
    shares: shares.map(([threadId, share]) => ({ thread: threadId, share, status: "live", secret: false })),
    other: 0,
    surprise: 0,
    tension: 0,
  };
}

const JUDGE = "Hidden crime: C = Judge Adam";
const RUPRECHT = "Hidden crime: C = Ruprecht";

const RIVER: River = {
  last_t: 4,
  columns: [
    {
      audience: "all",
      name: "All beats",
      threads: [thread(11, "Judge Adam"), thread(12, "Ruprecht")],
      moments: [
        moment(0, []),
        moment(1, [
          [11, 0.5],
          [12, 0.5],
        ]),
        moment(2, [
          [11, 0.3],
          [12, 0.7],
        ]),
        moment(3, [
          [11, 0.4],
          [12, 0.6],
        ]),
        moment(4, [[11, 1]]),
      ],
      events: [
        { t: 1, thread: 11, kind: "filled", step: "crime" },
        { t: 1, thread: 12, kind: "filled", step: "crime" },
        { t: 2, thread: 12, kind: "filled", step: "cover_up" },
        { t: 4, thread: 12, kind: "refuted", step: null },
        { t: 4, thread: 11, kind: "voiced", step: null },
      ],
    },
    {
      audience: "5",
      name: "Anna",
      threads: [thread(12, "Ruprecht")],
      moments: [moment(0, []), moment(1, []), moment(2, []), moment(3, [[12, 1]]), moment(4, [[12, 1]])],
      events: [{ t: 3, thread: 12, kind: "voiced", step: null }],
    },
  ],
};

function rowsOf(table: HTMLElement) {
  return within(table)
    .getAllByRole("row")
    .map((row) => [...row.querySelectorAll("th, td")].map((cell) => cell.textContent));
}

describe("EvidenceView", () => {
  it("sets every beat against the readings held at the last beat, strongest first, and those refuted by then", () => {
    render(<EvidenceView beats={BEATS} river={RIVER} />);

    const matrix = screen.getByRole("table", { name: "Evidence seen by All beats" });

    expect(rowsOf(matrix)).toEqual([
      ["t", "Beat", `${JUDGE} (100%)`, `${RUPRECHT} (refuted)`, "Evidence"],
      ["1", "The jug is broken.", "crime", "crime", "fits every reading"],
      ["2", "Adam hides what he did.", "", "cover_up", "tells them apart"],
      ["3", "Walter arrives.", "", "", "supports none"],
      ["4", "Ruprecht was elsewhere.", "", "refuted", "tells them apart"],
    ]);
  });

  it("shows the evidence up to an earlier beat", async () => {
    render(<EvidenceView beats={BEATS} river={RIVER} />);

    const upTo = screen.getByRole("spinbutton", { name: "Up to beat" });
    await userEvent.clear(upTo);
    await userEvent.type(upTo, "2");

    expect(rowsOf(screen.getByRole("table", { name: "Evidence seen by All beats" }))).toEqual([
      ["t", "Beat", `${RUPRECHT} (70%)`, `${JUDGE} (30%)`, "Evidence"],
      ["1", "The jug is broken.", "crime", "crime", "fits every reading"],
      ["2", "Adam hides what he did.", "cover_up", "", "tells them apart"],
    ]);
  });

  it("shows the evidence a player has seen", async () => {
    render(<EvidenceView beats={BEATS} river={RIVER} />);

    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Seen by" }), "Anna");

    expect(rowsOf(screen.getByRole("table", { name: "Evidence seen by Anna" }))).toEqual([
      ["t", "Beat", `${RUPRECHT} (100%)`, "Evidence"],
      ["1", "The jug is broken.", "", "supports none"],
      ["2", "Adam hides what he did.", "", "supports none"],
      ["3", "Walter arrives.", "", "supports none"],
      ["4", "Ruprecht was elsewhere.", "", "supports none"],
    ]);
  });
});
