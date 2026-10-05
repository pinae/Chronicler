import { expect, test, type Locator, type Page } from "@playwright/test";

import { seed } from "./seed";

// Scenarios of docs/usage/knowledge-map.md

const JUG = "The Broken Jug (an adventure)";
const PLAYERS = ["Anna", "Ben", "Clara"];
const ROW_HEIGHT = 32;

test.beforeAll(() => {
  test.setTimeout(120_000);
  seed("broken-jug");
});

async function openKnowledgeMap(page: Page) {
  await page.goto("/");
  await page.getByRole("link", { name: JUG }).click();
  await page.getByRole("link", { name: "Story map" }).click();
  await page
    .getByRole("navigation", { name: "Story map views" })
    .getByRole("link", { name: "Knowledge map" })
    .click();
}

function knowledgeOf(page: Page, player: string) {
  return page.getByRole("img", { name: `Knowledge of ${player}` });
}

/** The row (beat t) at the centre of a mark. */
async function rowOf(chart: Locator, mark: Locator) {
  const chartBox = await chart.boundingBox();
  const markBox = await mark.boundingBox();
  if (!chartBox || !markBox) {
    throw new Error("mark not drawn");
  }
  const centre = markBox.y + markBox.height / 2 - chartBox.y;
  return Math.floor(centre / ROW_HEIGHT) + 1;
}

/** The rows of a fuse's hollow square (where the beat happened) and of its spark (where it was
 * learned). */
async function fuseRows(chart: Locator, t: number) {
  const fuse = chart.getByTestId(`fuse-${t}`);
  return {
    happened: await rowOf(chart, fuse.locator("rect")),
    learned: await rowOf(chart, fuse.locator("circle")),
  };
}

/** The cells of one beat's row of the table, by column header. */
async function tableRow(
  table: Locator,
  t: number,
): Promise<Record<string, string>> {
  const headers = await table.getByRole("columnheader").allTextContents();
  const cells = await table
    .getByRole("row")
    .filter({
      has: table.page().getByRole("cell", { name: String(t), exact: true }),
    })
    .first()
    .getByRole("cell")
    .allTextContents();
  return Object.fromEntries(
    headers.map((header, index) => [header, cells[index] ?? ""]),
  );
}

test("Open the knowledge map", async ({ page }) => {
  await openKnowledgeMap(page);

  const views = page.getByRole("navigation", { name: "Story map views" });
  await expect(
    views.getByRole("link", { name: "Knowledge map" }),
  ).toHaveAttribute("aria-current", "page");
  const legend = page.getByRole("list", { name: "Legend" });
  await expect(legend).toContainText("Knew it when it happened");
  await expect(legend).toContainText("Learned it later, where the fuse ends");
  await expect(legend).toContainText("Never learned it");
  for (const player of PLAYERS) {
    await expect(knowledgeOf(page, player)).toBeVisible();
  }
});

test("Watch the game master's notes reach the players", async ({ page }) => {
  await openKnowledgeMap(page);

  for (const player of PLAYERS) {
    const chart = knowledgeOf(page, player);
    expect(await fuseRows(chart, 3)).toEqual({ happened: 3, learned: 26 });
    expect(await fuseRows(chart, 2)).toEqual({ happened: 2, learned: 30 });
    await expect(chart.getByText(/^Beat 1,/)).toHaveCount(0);
  }
});

test("See who missed a scene", async ({ page }) => {
  await openKnowledgeMap(page);

  for (const player of PLAYERS) {
    const chart = knowledgeOf(page, player);
    await expect(chart.getByText(/^Beat 19,/)).toHaveCount(
      player === "Ben" ? 1 : 0,
    );
    await expect(chart.getByText(/^Beat 20,/)).toHaveCount(0);
  }
});

test("Show who knew what as a table", async ({ page }) => {
  await openKnowledgeMap(page);

  await page.getByRole("button", { name: "Show as table" }).click();

  const table = page.getByRole("table", { name: "Who knew what" });
  const expected: Record<number, string> = {
    3: "learned at t = 26 via beat 26",
    1: "not learned",
    5: "when it happened",
  };
  for (const [t, cell] of Object.entries(expected)) {
    const row = await tableRow(table, Number(t));
    for (const player of PLAYERS) {
      expect(row[player]).toBe(cell);
    }
  }

  await page.getByRole("button", { name: "Show as map" }).click();

  await expect(knowledgeOf(page, "Anna")).toBeVisible();
});
