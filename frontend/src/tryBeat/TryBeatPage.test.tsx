import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it } from "vitest";

import { fakeApi } from "../test/fakeApi";
import { TryBeatPage } from "./TryBeatPage";

const STEWARD = {
  id: 2,
  title: "The Steward of Wend",
  kind: "session",
  last_t: 11,
  players: [
    { id: 7, name: "Anna" },
    { id: 8, name: "Ben" },
  ],
};
const ENTITIES = [
  { id: 11, name: "Mira", kind: "character", introduced_at_t: 1 },
  { id: 12, name: "Aldric", kind: "character", introduced_at_t: 1 },
  { id: 16, name: "The family seal", kind: "secret", introduced_at_t: 5 },
];
const VOCABULARY = [
  {
    name: "steals",
    roles: [
      { name: "who", kinds: ["entity"], optional: false },
      { name: "what", kinds: ["entity", "literal"], optional: false },
      { name: "from", kinds: ["entity"], optional: false },
    ],
  },
  {
    name: "learns",
    roles: [
      { name: "who", kinds: ["entity"], optional: false },
      { name: "what", kinds: ["beat", "prop"], optional: false },
      { name: "from", kinds: ["entity"], optional: true },
    ],
  },
  {
    name: "is",
    roles: [
      { name: "who", kinds: ["entity"], optional: false },
      { name: "trait", kinds: ["literal"], optional: false },
    ],
  },
];
const API = {
  "/api/chronicles/2": STEWARD,
  "/api/chronicles/2/entities": ENTITIES,
  "/api/vocabulary": VOCABULARY,
};
const DRY_RUN = "/api/chronicles/2/dry-run";

function effect(overrides: object) {
  return {
    hypothesis_id: 5,
    schema_slug: "betrayal",
    schema_name: "Betrayal",
    binding: [
      { role: "T", entity_id: 12, entity_name: "Aldric" },
      { role: "V", entity_id: 11, entity_name: "Mira" },
      { role: "S", entity_id: 16, entity_name: "The family seal" },
    ],
    changes: ["filled"],
    status: "live",
    filled_step: "harm",
    weight_before: 0,
    weight_after: 1.5,
    refines: null,
    ...overrides,
  };
}

function showTryBeat() {
  render(
    <MemoryRouter initialEntries={["/chronicles/2/try"]}>
      <Routes>
        <Route path="/chronicles/:chronicleId/try" element={<TryBeatPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

async function composeTheft(user: ReturnType<typeof userEvent.setup>) {
  await user.selectOptions(await screen.findByLabelText("Predicate"), "steals");
  await user.selectOptions(screen.getByLabelText("who"), "Aldric");
  await user.selectOptions(screen.getByLabelText("what"), "The family seal");
  await user.selectOptions(screen.getByLabelText("from"), "Mira");
  await user.click(within(screen.getByRole("group", { name: "Present" })).getByLabelText("Aldric"));
  await user.click(within(screen.getByRole("group", { name: "Shown to" })).getByLabelText("Anna"));
  await user.click(within(screen.getByRole("group", { name: "Shown to" })).getByLabelText("Ben"));
}

function effectRows() {
  const table = screen.getByRole("table", { name: "Effects" });
  return within(table)
    .getAllByRole("row")
    .slice(1)
    .map((row) =>
      within(row)
        .getAllByRole("cell")
        .map((cell) => cell.textContent),
    );
}

describe("TryBeatPage", () => {
  it("tries a beat composed from the vocabulary and the chronicle's entities", async () => {
    const sent: unknown[] = [];
    fakeApi(API, {
      [DRY_RUN]: (body) => {
        sent.push(body);
        return { status: 200, body: { t: 12, effects: [effect({})] } };
      },
    });
    const user = userEvent.setup();
    showTryBeat();

    await composeTheft(user);
    await user.click(screen.getByRole("button", { name: "Try it" }));

    expect(await screen.findByRole("heading", { name: "If this were beat 12" })).toBeInTheDocument();
    expect(effectRows()).toEqual([
      ["Betrayal: T = Aldric, V = Mira, S = The family seal", "filled harm", "0.0 → 1.5"],
    ]);
    expect(sent).toEqual([
      {
        pred: "steals",
        args: { who: { entity: 12 }, what: { entity: 16 }, from: { entity: 11 } },
        characters_present: [12],
        players_present: [],
        audience: "all",
      },
    ]);
  });

  it("shows hypotheses the beat would create and the changes of their status", async () => {
    const seeded = effect({
      hypothesis_id: null,
      changes: ["seeded"],
      filled_step: "trust",
      weight_before: null,
      weight_after: -1.5,
    });
    const completed = effect({ changes: ["filled", "completed"], filled_step: "reveal", weight_after: 5.5 });
    const refuted = effect({ changes: ["refuted"], filled_step: null, weight_before: -1, weight_after: -1 });
    fakeApi(API, {
      [DRY_RUN]: () => ({ status: 200, body: { t: 12, effects: [seeded, completed, refuted] } }),
    });
    const user = userEvent.setup();
    showTryBeat();

    await composeTheft(user);
    await user.click(screen.getByRole("button", { name: "Try it" }));

    await screen.findByRole("table", { name: "Effects" });
    expect(effectRows().map(([, change, weight]) => [change, weight])).toEqual([
      ["seeded (trust)", "new: -1.5"],
      ["filled reveal, completed", "0.0 → 5.5"],
      ["refuted", "-1.0 → -1.0"],
    ]);
  });

  it("says when no hypothesis would change", async () => {
    fakeApi(API, { [DRY_RUN]: () => ({ status: 200, body: { t: 12, effects: [] } }) });
    const user = userEvent.setup();
    showTryBeat();

    await composeTheft(user);
    await user.click(screen.getByRole("button", { name: "Try it" }));

    expect(await screen.findByText("No hypothesis would change.")).toBeInTheDocument();
  });

  it("shows why the backend rejected the beat", async () => {
    fakeApi(API, { [DRY_RUN]: () => ({ status: 422, body: { detail: "steals: missing role 'from'" } }) });
    const user = userEvent.setup();
    showTryBeat();

    await user.selectOptions(await screen.findByLabelText("Predicate"), "steals");
    await user.click(screen.getByRole("button", { name: "Try it" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("steals: missing role 'from'");
  });

  it("offers each role of the chosen predicate in the way it can be filled", async () => {
    fakeApi(API);
    const user = userEvent.setup();
    showTryBeat();

    await user.selectOptions(await screen.findByLabelText("Predicate"), "learns");
    expect(screen.getByLabelText("what (beat t)")).toHaveAttribute("type", "number");
    expect(screen.getByLabelText("from (optional)")).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText("Predicate"), "is");
    expect(screen.getByLabelText("trait")).toHaveAttribute("type", "text");
  });

  it("sends beat references and plain values as such", async () => {
    const sent: unknown[] = [];
    fakeApi(API, {
      [DRY_RUN]: (body) => {
        sent.push(body);
        return { status: 200, body: { t: 12, effects: [] } };
      },
    });
    const user = userEvent.setup();
    showTryBeat();

    await user.selectOptions(await screen.findByLabelText("Predicate"), "learns");
    await user.selectOptions(screen.getByLabelText("who"), "Mira");
    await user.type(screen.getByLabelText("what (beat t)"), "13");
    await user.selectOptions(screen.getByLabelText("Lattice of"), "Ben");
    await user.click(screen.getByRole("button", { name: "Try it" }));
    await screen.findByText("No hypothesis would change.");

    expect(sent).toEqual([
      {
        pred: "learns",
        args: { who: { entity: 11 }, what: { beat: 13 } },
        characters_present: [],
        players_present: [7, 8],
        audience: "8",
      },
    ]);
  });
});
