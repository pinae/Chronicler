import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import type { KnowledgeMap, River } from "../api/types";
import { ClueView } from "./ClueView";

const BEATS = [
  { t: 1, pred: "kills", text: "Macbeth kills Duncan.", source_kind: "narration", quarantined: false },
  { t: 2, pred: "says", text: "Macbeth blames the grooms.", source_kind: "narration", quarantined: false },
  { t: 3, pred: "distrusts", text: "Banquo suspects Macbeth.", source_kind: "narration", quarantined: false },
  {
    t: 4,
    pred: "distrusts",
    text: "Macduff suspects Macbeth.",
    source_kind: "narration",
    quarantined: false,
  },
  {
    t: 5,
    pred: "learns",
    text: "The doctor hears the confession.",
    source_kind: "narration",
    quarantined: false,
  },
];

const MURDER = {
  id: 11,
  schema_slug: "hidden_crime",
  schema_name: "Hidden crime",
  binding: [
    { role: "C", entity_id: 1, entity_name: "Macbeth" },
    { role: "V", entity_id: 2, entity_name: "King Duncan" },
  ],
  open_steps: [],
  waiting_since: 1,
  payoff_steps: ["discovery"],
};
const GROOMS = {
  id: 12,
  schema_slug: "hidden_crime",
  schema_name: "Hidden crime",
  binding: [
    { role: "C", entity_id: 3, entity_name: "The grooms" },
    { role: "V", entity_id: 2, entity_name: "King Duncan" },
  ],
  open_steps: ["discovery"],
  waiting_since: 3,
  payoff_steps: ["discovery"],
};
const MURDER_LABEL = "Hidden crime: C = Macbeth, V = King Duncan";
const GROOMS_LABEL = "Hidden crime: C = The grooms, V = King Duncan";

function moment(t: number, murder: number, grooms: number) {
  const shares = [
    { thread: 11, share: murder, status: "live", secret: false },
    { thread: 12, share: grooms, status: "live", secret: false },
  ].filter((share) => share.share > 0);
  return { t, shares, other: 0, surprise: 0, tension: 0 };
}

const RIVER: River = {
  last_t: 5,
  columns: [
    {
      audience: "all",
      name: "All beats",
      threads: [MURDER, GROOMS],
      moments: [
        moment(0, 0, 0),
        moment(1, 1, 0),
        moment(2, 0.5, 0.5),
        moment(3, 0.6, 0.4),
        moment(4, 0.7, 0.3),
        moment(5, 0.8, 0.2),
      ],
      events: [
        { t: 1, thread: 11, kind: "filled", step: "crime" },
        { t: 2, thread: 11, kind: "filled", step: "cover_up" },
        { t: 3, thread: 12, kind: "filled", step: "crime" },
        { t: 3, thread: 11, kind: "filled", step: "suspicion" },
        { t: 4, thread: 11, kind: "filled", step: "suspicion" },
        { t: 5, thread: 11, kind: "filled", step: "discovery" },
      ],
    },
  ],
};

function cell(t: number, knownSinceT: number, learnedViaT: number | null = null) {
  return { t, known_since_t: knownSinceT, learned_via_t: learnedViaT };
}

// Anna was there; Clara saw the cover-up and both suspicions; Dora only the cover-up and Macduff's suspicion.
const KNOWLEDGE_MAP: KnowledgeMap = {
  last_t: 5,
  columns: [
    { player: 5, name: "Anna", known: [cell(1, 1), cell(2, 2), cell(3, 3), cell(4, 4), cell(5, 5)] },
    { player: 6, name: "Clara", known: [cell(1, 5, 5), cell(2, 2), cell(3, 3), cell(4, 4), cell(5, 5)] },
    { player: 7, name: "Dora", known: [cell(1, 5, 5), cell(2, 2), cell(4, 4), cell(5, 5)] },
  ],
};

function rowsOf(table: HTMLElement) {
  return within(table)
    .getAllByRole("row")
    .map((row) => [...row.querySelectorAll("th, td")].map((element) => element.textContent));
}

describe("ClueView", () => {
  it("lists the clues to the strongest reading and how each player came to know them", () => {
    render(<ClueView beats={BEATS} river={RIVER} knowledgeMap={KNOWLEDGE_MAP} />);

    const ledger = screen.getByRole("table", { name: `Clues to ${MURDER_LABEL}` });

    expect(rowsOf(ledger).slice(0, 6)).toEqual([
      ["t", "Beat", "Step", "Anna", "Clara", "Dora"],
      [
        "1",
        "Macbeth kills Duncan.",
        "crime",
        "when it happened",
        "learned at t = 5 via beat 5",
        "learned at t = 5 via beat 5",
      ],
      [
        "2",
        "Macbeth blames the grooms.",
        "cover_up",
        "when it happened",
        "when it happened",
        "when it happened",
      ],
      ["3", "Banquo suspects Macbeth.", "suspicion", "when it happened", "when it happened", "not learned"],
      [
        "4",
        "Macduff suspects Macbeth.",
        "suspicion",
        "when it happened",
        "when it happened",
        "when it happened",
      ],
      [
        "5",
        "The doctor hears the confession.",
        "discovery (payoff)",
        "when it happened",
        "when it happened",
        "when it happened",
      ],
    ]);
  });

  it("counts the clues each player had before the payoff and warns below three", () => {
    render(<ClueView beats={BEATS} river={RIVER} knowledgeMap={KNOWLEDGE_MAP} />);

    const ledger = screen.getByRole("table", { name: `Clues to ${MURDER_LABEL}` });

    expect(rowsOf(ledger).at(-1)).toEqual([
      "Clues before the payoff at t = 5",
      "knew it from the start",
      "3 of 4",
      "2 of 4: fewer than three",
    ]);
  });

  it("counts the clues so far for a reading not yet paid off and names its open steps", async () => {
    render(<ClueView beats={BEATS} river={RIVER} knowledgeMap={KNOWLEDGE_MAP} />);

    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Reading" }), GROOMS_LABEL);

    const ledger = screen.getByRole("table", { name: `Clues to ${GROOMS_LABEL}` });
    expect(rowsOf(ledger).at(-1)).toEqual([
      "Clues so far",
      "knew it from the start",
      "knew it from the start",
      "0 of 1: fewer than three",
    ]);
    expect(screen.getByText("Still open: discovery")).toBeInTheDocument();
  });
});
