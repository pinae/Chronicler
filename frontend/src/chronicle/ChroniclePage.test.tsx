import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it } from "vitest";

import { fakeApi } from "../test/fakeApi";
import { ChroniclePage } from "./ChroniclePage";

const STEWARD = {
  id: 2,
  title: "The Steward of Wend",
  kind: "session",
  last_t: 3,
  players: [
    { id: 7, name: "Anna" },
    { id: 8, name: "Ben" },
  ],
};

function beat(t: number, pred: string, text: string, quarantined = false) {
  return { t, pred, text, source_kind: "narration", quarantined };
}

const ALL_BEATS = [
  beat(1, "trusts", "Mira trusts Aldric."),
  beat(2, "hides", "Mira hides the seal (GM only)."),
  beat(3, "resigns", "Aldric resigns.", true),
];

function showChronicle(path = "/chronicles/2") {
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/chronicles/:chronicleId" element={<ChroniclePage />} />
      </Routes>
    </MemoryRouter>,
  );
}

function beatRows() {
  const table = screen.getByRole("table", { name: "Beats" });
  return within(table)
    .getAllByRole("row")
    .slice(1)
    .map((row) => row.textContent);
}

describe("ChroniclePage", () => {
  it("shows the chronicle's title and every beat by default", async () => {
    fakeApi({ "/api/chronicles/2": STEWARD, "/api/chronicles/2/beats?audience=all": ALL_BEATS });

    showChronicle();

    expect(await screen.findByRole("heading", { name: "The Steward of Wend" })).toBeInTheDocument();
    expect(await screen.findByText("Mira hides the seal (GM only).")).toBeInTheDocument();
    expect(beatRows()).toEqual([
      "1trustsMira trusts Aldric.",
      "2hidesMira hides the seal (GM only).",
      "3resigns (quarantined)Aldric resigns.",
    ]);
  });

  it("shows only what the table saw when the table is chosen", async () => {
    fakeApi({
      "/api/chronicles/2": STEWARD,
      "/api/chronicles/2/beats?audience=all": ALL_BEATS,
      "/api/chronicles/2/beats?audience=table": [ALL_BEATS[0]],
    });
    showChronicle();
    await screen.findByText("Mira hides the seal (GM only).");

    await userEvent.selectOptions(screen.getByLabelText("Seen by"), "The table");

    expect(await screen.findByText("Mira trusts Aldric.")).toBeInTheDocument();
    expect(screen.queryByText("Mira hides the seal (GM only).")).not.toBeInTheDocument();
  });

  it("offers every player as an audience", async () => {
    fakeApi({ "/api/chronicles/2": STEWARD, "/api/chronicles/2/beats?audience=all": ALL_BEATS });

    showChronicle();

    const audiences = await screen.findByLabelText("Seen by");
    expect(
      within(audiences)
        .getAllByRole("option")
        .map((option) => option.textContent),
    ).toEqual(["All beats", "The table", "Anna", "Ben"]);
  });

  it("goes back in time with the beat slider", async () => {
    fakeApi({
      "/api/chronicles/2": STEWARD,
      "/api/chronicles/2/beats?audience=all": ALL_BEATS,
      "/api/chronicles/2/beats?audience=all&t=1": [ALL_BEATS[0]],
    });
    showChronicle();
    await screen.findByText("Aldric resigns.");

    fireEvent.change(screen.getByLabelText("Up to beat"), { target: { value: "1" } });

    expect(await screen.findByText("t = 1 of 3")).toBeInTheDocument();
    expect(screen.queryByText("Aldric resigns.")).not.toBeInTheDocument();
  });

  it("reads audience and time from the address", async () => {
    fakeApi({ "/api/chronicles/2": STEWARD, "/api/chronicles/2/beats?audience=8&t=1": [ALL_BEATS[0]] });

    showChronicle("/chronicles/2?audience=8&t=1");

    expect(await screen.findByText("Mira trusts Aldric.")).toBeInTheDocument();
    expect(screen.getByLabelText("Seen by")).toHaveValue("8");
  });

  it("says so when the chronicle does not exist", async () => {
    fakeApi({});

    showChronicle("/chronicles/999");

    expect(await screen.findByText("Chronicle not found")).toBeInTheDocument();
  });
});
