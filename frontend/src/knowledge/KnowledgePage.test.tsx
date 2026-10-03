import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it } from "vitest";

import { fakeApi } from "../test/fakeApi";
import { KnowledgePage } from "./KnowledgePage";

const STEWARD = {
  id: 2,
  title: "The Steward of Wend",
  kind: "session",
  last_t: 24,
  players: [{ id: 8, name: "Ben" }],
};
const CHARACTERS = [
  { id: 11, name: "Mira", kind: "character", introduced_at_t: 1 },
  { id: 12, name: "Aldric", kind: "character", introduced_at_t: 1 },
];
const API = {
  "/api/chronicles/2": STEWARD,
  "/api/chronicles/2/entities?kind=character": CHARACTERS,
};

function known(t: number, text: string, knownSince: number, via: number | null) {
  return { t, pred: "x", text, known_since_t: knownSince, learned_via_t: via };
}

function showKnowledge(path = "/chronicles/2/knowledge") {
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/chronicles/:chronicleId/knowledge" element={<KnowledgePage />} />
      </Routes>
    </MemoryRouter>,
  );
}

function rows() {
  const table = screen.getByRole("table", { name: "Known beats" });
  return within(table)
    .getAllByRole("row")
    .slice(1)
    .map((row) =>
      within(row)
        .getAllByRole("cell")
        .map((cell) => cell.textContent),
    );
}

describe("KnowledgePage", () => {
  it("asks whose knowledge to show", async () => {
    fakeApi(API);

    showKnowledge();

    expect(await screen.findByText("Choose a character or a player.")).toBeInTheDocument();
  });

  it("lists what a character knows and how they came to know it", async () => {
    fakeApi({
      ...API,
      "/api/chronicles/2/knowledge?character=11": [
        known(2, "Mira trusts Aldric.", 2, null),
        known(13, "Aldric steals the seal from Mira.", 22, 22),
      ],
    });
    showKnowledge();

    await userEvent.selectOptions(await screen.findByLabelText("Who"), "Mira");

    await screen.findByText("Aldric steals the seal from Mira.");
    expect(rows()).toEqual([
      ["2", "Mira trusts Aldric.", "present"],
      ["13", "Aldric steals the seal from Mira.", "learned at t = 22"],
    ]);
  });

  it("lists what a player saw", async () => {
    fakeApi({
      ...API,
      "/api/chronicles/2/knowledge?player=8": [known(7, "Aldric learns where Mira hides the seal.", 7, null)],
    });
    showKnowledge();

    await userEvent.selectOptions(await screen.findByLabelText("Who"), "Ben");

    await screen.findByText("Aldric learns where Mira hides the seal.");
    expect(rows()).toEqual([["7", "Aldric learns where Mira hides the seal.", "saw it"]]);
  });

  it("shows what was known at an earlier beat", async () => {
    fakeApi({
      ...API,
      "/api/chronicles/2/knowledge?character=11": [known(13, "Aldric steals the seal from Mira.", 22, 22)],
      "/api/chronicles/2/knowledge?character=11&t=21": [],
    });
    showKnowledge("/chronicles/2/knowledge?knower=character-11");
    await screen.findByText("Aldric steals the seal from Mira.");

    fireEvent.change(screen.getByLabelText("Up to beat"), { target: { value: "21" } });

    expect(await screen.findByText("Nothing known yet")).toBeInTheDocument();
  });
});
