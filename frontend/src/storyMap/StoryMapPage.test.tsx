import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it } from "vitest";

import { fakeApi } from "../test/fakeApi";
import { ROW_HEIGHT } from "./StoryMap";
import { StoryMapPage } from "./StoryMapPage";

const JUG = {
  id: 3,
  title: "The Broken Jug",
  kind: "session",
  last_t: 3,
  players: [{ id: 5, name: "Anna" }],
};

const BEATS = [
  { t: 1, pred: "is_at", text: "Adam comes to Eve's room.", source_kind: "narration", quarantined: false },
  { t: 2, pred: "harms", text: "Adam breaks the jug.", source_kind: "action", quarantined: false },
  { t: 3, pred: "says", text: "Marthe accuses Ruprecht.", source_kind: "claim", quarantined: false },
];

const ENTITY_IDS: Record<string, number> = { "Judge Adam": 1, "Frau Marthe": 2, Ruprecht: 3 };

function binding(...entries: [string, string | null][]) {
  return entries.map(([role, name]) => ({
    role,
    entity_id: name ? (ENTITY_IDS[name] ?? null) : null,
    entity_name: name,
  }));
}

const JUDGE = {
  id: 11,
  schema_slug: "hidden_crime",
  schema_name: "Hidden crime",
  binding: binding(["C", "Judge Adam"], ["V", "Frau Marthe"], ["I", null]),
  open_steps: ["discovery"],
  waiting_since: 2,
};
const RUPRECHT = {
  id: 12,
  schema_slug: "hidden_crime",
  schema_name: "Hidden crime",
  binding: binding(["C", "Ruprecht"], ["V", "Frau Marthe"], ["I", null]),
  open_steps: ["crime", "discovery"],
  waiting_since: null,
};

const JUDGE_LABEL = "Hidden crime: C = Judge Adam, V = Frau Marthe, I = ?";

const RIVER = {
  last_t: 3,
  columns: [
    {
      audience: "all",
      name: "All beats",
      threads: [JUDGE],
      moments: [
        { t: 0, shares: [], other: 0 },
        { t: 1, shares: [], other: 0 },
        { t: 2, shares: [{ thread: 11, share: 0.75, status: "live", secret: true }], other: 0.25 },
        { t: 3, shares: [{ thread: 11, share: 1, status: "live", secret: false }], other: 0 },
      ],
      events: [
        { t: 2, thread: 11, kind: "filled", step: "crime" },
        { t: 3, thread: 11, kind: "filled", step: "cover_up" },
      ],
    },
    {
      audience: "5",
      name: "Anna",
      threads: [RUPRECHT],
      moments: [
        { t: 0, shares: [], other: 0 },
        { t: 1, shares: [], other: 0 },
        { t: 2, shares: [], other: 0 },
        { t: 3, shares: [{ thread: 12, share: 1, status: "live", secret: false }], other: 0 },
      ],
      events: [{ t: 3, thread: 12, kind: "voiced", step: null }],
    },
  ],
};

function showStoryMap() {
  fakeApi({
    "/api/chronicles/3": JUG,
    "/api/chronicles/3/beats?audience=all": BEATS,
    "/api/chronicles/3/river": RIVER,
  });
  render(
    <MemoryRouter initialEntries={["/chronicles/3/map"]}>
      <Routes>
        <Route path="/chronicles/:chronicleId/map" element={<StoryMapPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("StoryMapPage", () => {
  it("is the story map screen of the chronicle", async () => {
    showStoryMap();

    expect(await screen.findByRole("heading", { name: "Story map of The Broken Jug" })).toBeInTheDocument();
    const nav = screen.getByRole("navigation", { name: "Chronicle" });
    expect(within(nav).getByRole("link", { name: "Story map" })).toHaveAttribute("aria-current", "page");
  });

  it("lists the beats beside a river for the game master and for each player", async () => {
    showStoryMap();

    const beats = await screen.findByRole("table", { name: "Beats" });
    expect(within(beats).getByText("Adam breaks the jug.")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Story river: All beats" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Story river: Anna" })).toBeInTheDocument();
  });

  it("names the schemas, the other readings, the secret hatching and the events in a legend", async () => {
    showStoryMap();

    const legend = await screen.findByRole("list", { name: "Legend" });
    const entries = within(legend)
      .getAllByRole("listitem")
      .map((item) => item.textContent);
    expect(entries).toEqual([
      "Hidden crime",
      "Other readings",
      "Only the game master holds it",
      "A step filled",
      "Completed",
      "Refuted",
      "Voiced by a player",
    ]);
  });

  it("shows a band's reading, share and secrecy at the beat under the pointer", async () => {
    showStoryMap();
    const river = await screen.findByRole("img", { name: "Story river: All beats" });

    fireEvent.pointerMove(within(river).getByTestId("band-11"), { clientY: ROW_HEIGHT * 1.5 });

    const tooltip = screen.getByRole("tooltip");
    expect(tooltip).toHaveTextContent("75% at t = 2");
    expect(tooltip).toHaveTextContent("Hidden crime: C = Judge Adam, V = Frau Marthe, I = ?");
    expect(tooltip).toHaveTextContent("live · only the game master holds it");
    expect(tooltip).toHaveTextContent("This beat: crime filled");
  });

  it("draws the steps of a band clicked on as arcs between the beats that filled them", async () => {
    showStoryMap();
    const river = await screen.findByRole("img", { name: "Story river: All beats" });

    await userEvent.click(within(river).getByTestId("band-11"));

    const arcs = screen.getByRole("img", { name: `Steps of ${JUDGE_LABEL} (All beats)` });
    expect(within(arcs).getByText("crime")).toBeInTheDocument();
    expect(within(arcs).getByText("cover_up")).toBeInTheDocument();
    expect(within(arcs).getByText("to come: discovery")).toBeInTheDocument();

    await userEvent.keyboard("{Escape}");

    expect(screen.queryByRole("img", { name: /^Steps of/ })).not.toBeInTheDocument();
  });

  it("lists the open threads of an audience, the longest waiting first", async () => {
    showStoryMap();

    const open = await screen.findByRole("list", { name: "Open threads seen by All beats" });
    expect(within(open).getByRole("listitem")).toHaveTextContent(
      `${JUDGE_LABEL} · open: discovery · waiting since t = 2`,
    );

    await userEvent.selectOptions(screen.getByLabelText("Open threads seen by"), "Anna");

    expect(screen.getByRole("list", { name: "Open threads seen by Anna" })).toHaveTextContent(
      "Hidden crime: C = Ruprecht, V = Frau Marthe, I = ? · open: crime, discovery · no beat supports it yet",
    );
  });

  it("brings out the compatible readings in every column while a band is pointed at", async () => {
    showStoryMap();
    const gameMaster = await screen.findByRole("img", { name: "Story river: All beats" });
    const anna = screen.getByRole("img", { name: "Story river: Anna" });

    fireEvent.pointerMove(within(gameMaster).getByTestId("band-11"), { clientY: ROW_HEIGHT * 2.5 });

    expect(within(gameMaster).getByTestId("band-11")).not.toHaveAttribute("data-dimmed");
    expect(within(anna).getByTestId("band-12")).toHaveAttribute("data-dimmed", "true");

    fireEvent.pointerLeave(gameMaster);

    expect(within(anna).getByTestId("band-12")).not.toHaveAttribute("data-dimmed");
  });

  it("shows the same numbers as tables", async () => {
    showStoryMap();

    await userEvent.click(await screen.findByRole("button", { name: "Show as table" }));

    const shares = screen.getByRole("table", { name: "Shares seen by All beats" });
    const rows = within(shares)
      .getAllByRole("row")
      .map((row) => [...row.querySelectorAll("th, td")].map((cell) => cell.textContent));
    expect(rows).toEqual([
      ["t", "Hidden crime: C = Judge Adam, V = Frau Marthe, I = ?", "Other readings"],
      ["1", "", ""],
      ["2", "75% (secret)", "25%"],
      ["3", "100%", ""],
    ]);
    expect(screen.getByRole("button", { name: "Show as river" })).toBeInTheDocument();
  });
});
