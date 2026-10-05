import { expect, test, type Locator, type Page } from "@playwright/test";

import { seed } from "./seed";

// Scenarios of docs/usage/story-map.md

const JUG = "The Broken Jug (an adventure)";
const JUDGE_HARMED_MARTHE =
  "Hidden crime: C = Judge Adam, V = Frau Marthe, I = ?";
const ROW_HEIGHT = 32;

test.beforeAll(() => {
  test.setTimeout(120_000);
  seed("broken-jug", "macbeth");
});

async function openStoryMap(page: Page, title: string) {
  await page.goto("/");
  await page.getByRole("link", { name: title }).click();
  await page.getByRole("link", { name: "Story map" }).click();
  await expect(
    page.getByRole("heading", { name: `Story map of ${title}` }),
  ).toBeVisible();
}

function river(page: Page, audience: string) {
  return page.getByRole("img", { name: `Story river: ${audience}` });
}

/** The cells of one beat's row of a shares table, by column header. */
async function sharesRow(
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

/** The middle of a river in the row of beat t. */
async function middleOfRow(page: Page, audience: string, t: number) {
  const box = await river(page, audience).boundingBox();
  if (!box) {
    throw new Error(`no river for ${audience}`);
  }
  return { x: box.width / 2, y: (t - 0.5) * ROW_HEIGHT };
}

async function pointAtRow(page: Page, audience: string, t: number) {
  const position = await middleOfRow(page, audience, t);
  await river(page, audience).hover({ position });
}

async function clickRow(page: Page, audience: string, t: number) {
  const position = await middleOfRow(page, audience, t);
  await river(page, audience).click({ position });
}

test("Open the story map", async ({ page }) => {
  await openStoryMap(page, JUG);

  const legend = page.getByRole("list", { name: "Legend" });
  await expect(legend).toContainText("Hidden crime");
  await expect(legend).toContainText("Other readings");
  await expect(legend).toContainText("Only the game master holds it");
  for (const audience of ["All beats", "Anna", "Ben", "Clara"]) {
    await expect(river(page, audience)).toBeVisible();
  }
  await expect(page.getByRole("table", { name: "Beats" })).toContainText(
    "Walter learns from Eve that the judge broke the jug.",
  );
  const screens = page.getByRole("navigation", { name: "Chronicle" });
  await expect(
    screens.getByRole("link", { name: "Story map" }),
  ).toHaveAttribute("aria-current", "page");
});

test("See what only the game master knows", async ({ page }) => {
  await openStoryMap(page, JUG);

  await page.getByRole("button", { name: "Show as table" }).click();

  const shares = page.getByRole("table", { name: "Shares seen by All beats" });
  expect((await sharesRow(shares, 18))[JUDGE_HARMED_MARTHE]).toMatch(
    /% \(secret\)$/,
  );
  expect((await sharesRow(shares, 19))[JUDGE_HARMED_MARTHE]).toMatch(/^\d+%$/);
});

test("Read a band", async ({ page }) => {
  await openStoryMap(page, JUG);

  await pointAtRow(page, "All beats", 20);

  const tooltip = page.getByRole("tooltip");
  await expect(tooltip).toContainText(/\d+% at t = 20/);
  await expect(tooltip).toContainText(JUDGE_HARMED_MARTHE);
  await expect(tooltip).toContainText("live");
  await expect(tooltip).toContainText("This beat: cover_up filled");
});

test("Compare the players", async ({ page }) => {
  await openStoryMap(page, JUG);

  await pointAtRow(page, "All beats", 20);

  const anna = river(page, "Anna");
  await expect(anna.locator('path[data-dimmed="true"]')).toHaveCount(1);
  await expect(
    anna.locator("path[data-testid^=band]:not([data-dimmed])"),
  ).toHaveCount(2);
});

test("See a thread's steps", async ({ page }) => {
  await openStoryMap(page, JUG);

  await clickRow(page, "All beats", 20);

  const arcs = page.getByRole("img", {
    name: `Steps of ${JUDGE_HARMED_MARTHE} (All beats)`,
  });
  for (const step of ["crime", "cover_up", "suspicion", "discovery"]) {
    await expect(arcs.getByText(step, { exact: true }).first()).toBeVisible();
  }

  await page.keyboard.press("Escape");

  await expect(arcs).toHaveCount(0);
  await expect(page.getByText("Click a band to see its steps")).toBeVisible();
});

test("List the open threads", async ({ page }) => {
  const fleance =
    "Prophecy: S = The three witches, H = Fleance, X = The crown of Scotland";
  await openStoryMap(page, "Macbeth (a session)");

  const open = page.getByRole("list", {
    name: "Open threads seen by All beats",
  });
  await expect(open.getByRole("listitem").first()).toHaveText(
    `${fleance} · open: fulfilment · waiting since t = 4`,
  );

  await open.getByRole("button", { name: fleance }).click();

  const arcs = page.getByRole("img", {
    name: `Steps of ${fleance} (All beats)`,
  });
  await expect(arcs.getByText("foretelling", { exact: true })).toBeVisible();
  await expect(arcs.getByText("to come: fulfilment")).toBeVisible();

  await openStoryMap(page, JUG);
  await page
    .getByRole("combobox", { name: "Open threads seen by" })
    .selectOption("Anna");

  await expect(
    page.getByRole("list", { name: "Open threads seen by Anna" }),
  ).toContainText(
    "Hidden crime: C = Ruprecht, V = Frau Marthe, I = ? · open: crime, discovery · no beat supports it yet",
  );
});

test("Show the river as a table", async ({ page }) => {
  await openStoryMap(page, JUG);

  await page.getByRole("button", { name: "Show as table" }).click();

  for (const audience of ["All beats", "Anna", "Ben", "Clara"]) {
    await expect(
      page.getByRole("table", { name: `Shares seen by ${audience}` }),
    ).toBeVisible();
  }

  await page.getByRole("button", { name: "Show as river" }).click();

  await expect(river(page, "All beats")).toBeVisible();
});

test("Watch a twist reach a player", async ({ page }) => {
  await openStoryMap(page, "Macbeth (a session)");

  await page.getByRole("button", { name: "Show as table" }).click();

  const dora = page.getByRole("table", { name: "Shares seen by Dora" });
  const murder = "Hidden crime: C = Macbeth, V = King Duncan, I = ?";
  expect((await sharesRow(dora, 31))[murder]).toBe("");
  expect((await sharesRow(dora, 32))[murder]).toMatch(/^\d+%$/);
});
