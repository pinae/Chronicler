import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it } from "vitest";

import { fakeApi } from "../test/fakeApi";
import { ROW_HEIGHT } from "./BeatRows";
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
  payoff_steps: ["discovery"],
};
const RUPRECHT = {
  id: 12,
  schema_slug: "hidden_crime",
  schema_name: "Hidden crime",
  binding: binding(["C", "Ruprecht"], ["V", "Frau Marthe"], ["I", null]),
  open_steps: ["crime", "discovery"],
  waiting_since: null,
  payoff_steps: ["discovery"],
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
        { t: 0, shares: [], other: 0, surprise: 0, tension: 0 },
        { t: 1, shares: [], other: 0, surprise: 0, tension: 0 },
        {
          t: 2,
          shares: [{ thread: 11, share: 0.75, status: "live", secret: true }],
          other: 0.25,
          surprise: 0,
          tension: 0,
        },
        {
          t: 3,
          shares: [{ thread: 11, share: 1, status: "live", secret: false }],
          other: 0,
          surprise: 0.25,
          tension: 1,
        },
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
        { t: 0, shares: [], other: 0, surprise: 0, tension: 0 },
        { t: 1, shares: [], other: 0, surprise: 0, tension: 0 },
        { t: 2, shares: [], other: 0, surprise: 0, tension: 0 },
        {
          t: 3,
          shares: [{ thread: 12, share: 1, status: "live", secret: false }],
          other: 0,
          surprise: 0,
          tension: 0,
        },
      ],
      events: [{ t: 3, thread: 12, kind: "voiced", step: null }],
    },
  ],
};

// Anna learns at t = 3 that Adam came to Eve's room, sees Marthe accuse Ruprecht and never learns of the jug.
const KNOWLEDGE_MAP = {
  last_t: 3,
  columns: [
    {
      player: 5,
      name: "Anna",
      known: [
        { t: 1, known_since_t: 3, learned_via_t: 3 },
        { t: 3, known_since_t: 3, learned_via_t: null },
      ],
    },
  ],
};

function showStoryMap(path = "/chronicles/3/map", knowledgeMap: unknown = KNOWLEDGE_MAP) {
  fakeApi({
    "/api/chronicles/3": JUG,
    "/api/chronicles/3/beats?audience=all": BEATS,
    "/api/chronicles/3/river": RIVER,
    "/api/chronicles/3/knowledge_map": knowledgeMap,
  });
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/chronicles/:chronicleId/map" element={<StoryMapPage />} />
        <Route path="/chronicles/:chronicleId/map/knowledge" element={<StoryMapPage view="knowledge" />} />
        <Route path="/chronicles/:chronicleId/map/pacing" element={<StoryMapPage view="pacing" />} />
        <Route path="/chronicles/:chronicleId/map/evidence" element={<StoryMapPage view="evidence" />} />
        <Route path="/chronicles/:chronicleId/map/clues" element={<StoryMapPage view="clues" />} />
      </Routes>
    </MemoryRouter>,
  );
}

function showPacing() {
  showStoryMap("/chronicles/3/map/pacing");
}

function showKnowledgeMap(knowledgeMap: unknown = KNOWLEDGE_MAP) {
  showStoryMap("/chronicles/3/map/knowledge", knowledgeMap);
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

  it("switches between the story river and the knowledge map", async () => {
    showStoryMap();
    const views = await screen.findByRole("navigation", { name: "Story map views" });

    await userEvent.click(within(views).getByRole("link", { name: "Knowledge map" }));

    expect(await screen.findByRole("img", { name: "Knowledge of Anna" })).toBeInTheDocument();
    expect(within(views).getByRole("link", { name: "Knowledge map" })).toHaveAttribute(
      "aria-current",
      "page",
    );

    await userEvent.click(within(views).getByRole("link", { name: "Story river" }));

    expect(await screen.findByRole("img", { name: "Story river: Anna" })).toBeInTheDocument();
  });

  it("marks the beats a player knew when they happened and burns a fuse down to where one was learned", async () => {
    showKnowledgeMap();

    const anna = await screen.findByRole("img", { name: "Knowledge of Anna" });

    // Each mark's tooltip
    expect(within(anna).getByText("Beat 3, Anna: when it happened")).toBeInTheDocument();
    expect(within(anna).getByText("Beat 1, Anna: learned at t = 3 via beat 3")).toBeInTheDocument();
    expect(within(anna).getByTestId("fuse-1")).toBeInTheDocument();
    expect(within(anna).queryByText(/^Beat 2,/)).not.toBeInTheDocument();
  });

  it("names the knowledge marks in a legend", async () => {
    showKnowledgeMap();

    const legend = await screen.findByRole("list", { name: "Legend" });
    const entries = within(legend)
      .getAllByRole("listitem")
      .map((item) => item.textContent);
    expect(entries).toEqual([
      "Knew it when it happened",
      "Learned it later, where the fuse ends",
      "Never learned it",
    ]);
  });

  it("shows who knew what as a table", async () => {
    showKnowledgeMap();

    await userEvent.click(await screen.findByRole("button", { name: "Show as table" }));

    const table = screen.getByRole("table", { name: "Who knew what" });
    const rows = within(table)
      .getAllByRole("row")
      .map((row) => [...row.querySelectorAll("th, td")].map((cell) => cell.textContent));
    expect(rows).toEqual([
      ["t", "Beat", "Anna"],
      ["1", "Adam comes to Eve's room.", "learned at t = 3 via beat 3"],
      ["2", "Adam breaks the jug.", "not learned"],
      ["3", "Marthe accuses Ruprecht.", "when it happened"],
    ]);

    await userEvent.click(screen.getByRole("button", { name: "Show as map" }));

    expect(screen.getByRole("img", { name: "Knowledge of Anna" })).toBeInTheDocument();
  });

  it("says so when nobody plays at the table", async () => {
    showKnowledgeMap({ last_t: 3, columns: [] });

    expect(
      await screen.findByText("Nobody plays at this table, so there is no knowledge to map."),
    ).toBeInTheDocument();
  });

  it("switches to the pacing of the story", async () => {
    showStoryMap();
    const views = await screen.findByRole("navigation", { name: "Story map views" });

    await userEvent.click(within(views).getByRole("link", { name: "Pacing" }));

    expect(await screen.findByRole("img", { name: "Pacing: All beats" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Pacing: Anna" })).toBeInTheDocument();
  });

  it("shows every beat's surprise and tension for each audience", async () => {
    showPacing();

    const gameMaster = await screen.findByRole("img", { name: "Pacing: All beats" });

    // Each row's tooltip
    expect(within(gameMaster).getByText("t = 3, All beats: surprise 25%, tension 100%")).toBeInTheDocument();
    expect(within(gameMaster).getByText("t = 2, All beats: surprise 0%, tension 0%")).toBeInTheDocument();
  });

  it("explains surprise and tension in a legend", async () => {
    showPacing();

    const legend = await screen.findByRole("list", { name: "Legend" });
    const entries = within(legend)
      .getAllByRole("listitem")
      .map((item) => item.textContent);
    expect(entries).toEqual([
      "Tension: belief in stories building towards a payoff",
      "Surprise: how much belief moved at this beat",
    ]);
  });

  it("shows the pacing as a table", async () => {
    showPacing();

    await userEvent.click(await screen.findByRole("button", { name: "Show as table" }));

    const table = screen.getByRole("table", { name: "Pacing" });
    const rows = within(table)
      .getAllByRole("row")
      .map((row) => [...row.querySelectorAll("th, td")].map((cell) => cell.textContent));
    expect(rows).toEqual([
      ["t", "All beats: surprise", "All beats: tension", "Anna: surprise", "Anna: tension"],
      ["1", "0%", "0%", "0%", "0%"],
      ["2", "0%", "0%", "0%", "0%"],
      ["3", "25%", "100%", "0%", "0%"],
    ]);

    await userEvent.click(screen.getByRole("button", { name: "Show as chart" }));

    expect(screen.getByRole("img", { name: "Pacing: All beats" })).toBeInTheDocument();
  });

  it("switches to the evidence matrix", async () => {
    showStoryMap();
    const views = await screen.findByRole("navigation", { name: "Story map views" });

    await userEvent.click(within(views).getByRole("link", { name: "Evidence" }));

    const matrix = await screen.findByRole("table", { name: "Evidence seen by All beats" });
    expect(within(matrix).getByRole("row", { name: /Adam breaks the jug\. crime/ })).toBeInTheDocument();
  });

  it("switches to the clue ledger of the strongest reading", async () => {
    showStoryMap();
    const views = await screen.findByRole("navigation", { name: "Story map views" });

    await userEvent.click(within(views).getByRole("link", { name: "Clues" }));

    const ledger = await screen.findByRole("table", { name: `Clues to ${JUDGE_LABEL}` });
    expect(
      within(ledger).getByRole("row", { name: /Adam breaks the jug\. crime not learned/ }),
    ).toBeInTheDocument();
  });
});
