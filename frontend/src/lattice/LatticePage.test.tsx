import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it } from "vitest";

import { fakeApi } from "../test/fakeApi";
import { LatticePage } from "./LatticePage";

const STEWARD = {
  id: 2,
  title: "The Steward of Wend",
  kind: "session",
  last_t: 24,
  players: [{ id: 7, name: "Anna" }],
};

function hypothesis(id: number, binding: [string, string | null][], weight: number, status = "live") {
  return {
    id,
    schema_slug: "betrayal",
    schema_name: "Betrayal",
    binding: binding.map(([role, name], index) => ({
      role,
      entity_id: name ? index + 1 : null,
      entity_name: name,
    })),
    status,
    weight,
    created_at_t: 2,
    status_changed_at_t: status === "live" ? null : 22,
    filled_steps: [
      { step_id: "trust", beat_ts: [2, 8] },
      { step_id: "harm", beat_ts: [13] },
    ],
    open_steps: ["access", "reveal"],
    refines: null,
    voiced: false,
  };
}

const NOW = {
  t: 24,
  hypotheses: [
    hypothesis(
      1,
      [
        ["T", "Aldric"],
        ["V", "Mira"],
        ["S", null],
      ],
      -1.0,
    ),
    hypothesis(
      2,
      [
        ["T", "Aldric"],
        ["V", "Mira"],
        ["S", "The family seal"],
      ],
      2.5,
      "complete",
    ),
  ],
};

function showLattice(path = "/chronicles/2/lattice") {
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/chronicles/:chronicleId/lattice" element={<LatticePage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("LatticePage", () => {
  it("lists the hypotheses of each schema, strongest first", async () => {
    fakeApi({ "/api/chronicles/2": STEWARD, "/api/chronicles/2/lattice?audience=all": NOW });

    showLattice();

    const betrayals = await screen.findByRole("table", { name: "Betrayal" });
    const [, strongest, weakest] = within(betrayals).getAllByRole("row");
    expect(strongest).toHaveTextContent("T = Aldric, V = Mira, S = The family seal");
    expect(strongest).toHaveTextContent("complete");
    expect(strongest).toHaveTextContent("2.50");
    expect(weakest).toHaveTextContent("S = ?");
    expect(weakest).toHaveTextContent("trust (t=2, 8); harm (t=13)");
    expect(weakest).toHaveTextContent("access, reveal");
  });

  it("shows the lattice as it was at an earlier beat", async () => {
    fakeApi({
      "/api/chronicles/2": STEWARD,
      "/api/chronicles/2/lattice?audience=all": NOW,
      "/api/chronicles/2/lattice?audience=all&t=21": {
        t: 21,
        hypotheses: [hypothesis(2, [["T", "Aldric"]], 2.5)],
      },
    });
    showLattice();
    await screen.findByText("complete");

    fireEvent.change(screen.getByLabelText("Up to beat"), { target: { value: "21" } });

    expect(await screen.findByText("t = 21 of 24")).toBeInTheDocument();
    expect(await screen.findByText("live")).toBeInTheDocument();
    expect(screen.queryByText("complete")).not.toBeInTheDocument();
  });

  it("shows a player's own lattice", async () => {
    fakeApi({
      "/api/chronicles/2": STEWARD,
      "/api/chronicles/2/lattice?audience=all": NOW,
      "/api/chronicles/2/lattice?audience=7": { t: 24, hypotheses: [] },
    });
    showLattice();
    await screen.findByText("complete");

    await userEvent.selectOptions(screen.getByLabelText("Seen by"), "Anna");

    expect(await screen.findByText("No hypotheses at this point")).toBeInTheDocument();
  });

  it("offers the game master's view and every player, but not the table", async () => {
    fakeApi({ "/api/chronicles/2": STEWARD, "/api/chronicles/2/lattice?audience=all": NOW });

    showLattice();

    const audiences = await screen.findByLabelText("Seen by");
    expect(
      within(audiences)
        .getAllByRole("option")
        .map((option) => option.textContent),
    ).toEqual(["All beats", "Anna"]);
  });

  it("links back to the chronicle", async () => {
    fakeApi({ "/api/chronicles/2": STEWARD, "/api/chronicles/2/lattice?audience=all": NOW });

    showLattice();

    expect(await screen.findByRole("link", { name: "Beats of The Steward of Wend" })).toHaveAttribute(
      "href",
      "/chronicles/2",
    );
  });
});
