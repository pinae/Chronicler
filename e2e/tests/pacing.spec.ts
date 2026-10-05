import { expect, test, type Locator, type Page } from "@playwright/test";

import { seed } from "./seed";

// Scenarios of docs/usage/pacing.md

const JUG = "The Broken Jug (an adventure)";
const PLAYERS = ["Anna", "Ben", "Clara"];

test.beforeAll(() => {
  test.setTimeout(120_000);
  seed("broken-jug", "macbeth");
});

async function openPacing(page: Page, title: string) {
  await page.goto("/");
  await page.getByRole("link", { name: title }).click();
  await page.getByRole("link", { name: "Story map" }).click();
  await page
    .getByRole("navigation", { name: "Story map views" })
    .getByRole("link", { name: "Pacing" })
    .click();
}

/** The cells of one beat's row of the table, by column header, as fractions. */
async function pacingRow(
  table: Locator,
  t: number,
): Promise<Record<string, number>> {
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
    headers.map((header, index) => [
      header,
      Number.parseInt(cells[index] ?? "", 10) / 100,
    ]),
  );
}

test("Open the pacing", async ({ page }) => {
  await openPacing(page, JUG);

  const views = page.getByRole("navigation", { name: "Story map views" });
  await expect(views.getByRole("link", { name: "Pacing" })).toHaveAttribute(
    "aria-current",
    "page",
  );
  const legend = page.getByRole("list", { name: "Legend" });
  await expect(legend).toContainText(
    "Tension: belief in stories building towards a payoff",
  );
  await expect(legend).toContainText(
    "Surprise: how much belief moved at this beat",
  );
  for (const audience of ["All beats", ...PLAYERS]) {
    await expect(
      page.getByRole("img", { name: `Pacing: ${audience}` }),
    ).toBeVisible();
  }
});

test("Feel the confession", async ({ page }) => {
  await openPacing(page, JUG);

  await page.getByRole("button", { name: "Show as table" }).click();

  const table = page.getByRole("table", { name: "Pacing" });
  const before = await pacingRow(table, 25);
  const confession = await pacingRow(table, 26);
  for (const player of PLAYERS) {
    expect(before[`${player}: tension`]).toBeGreaterThan(0.8);
    expect(confession[`${player}: tension`]).toBeLessThan(0.1);
    expect(confession[`${player}: surprise`]).toBeGreaterThan(0.3);
  }
  expect(before["Ben: tension"]).toBe(1);
});

test("See a twist reach one player", async ({ page }) => {
  await openPacing(page, "Macbeth (a session)");

  await page.getByRole("button", { name: "Show as table" }).click();

  const report = await pacingRow(
    page.getByRole("table", { name: "Pacing" }),
    32,
  );
  expect(report["Dora: surprise"]).toBeGreaterThan(0.3);
  expect(report["All beats: surprise"]).toBeLessThan(0.1);
});

test("Show the pacing as a chart again", async ({ page }) => {
  await openPacing(page, JUG);
  await page.getByRole("button", { name: "Show as table" }).click();

  await page.getByRole("button", { name: "Show as chart" }).click();

  await expect(
    page.getByRole("img", { name: "Pacing: All beats" }),
  ).toBeVisible();
});
