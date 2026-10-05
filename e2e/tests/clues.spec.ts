import { expect, test, type Locator, type Page } from "@playwright/test";

import { seed } from "./seed";

// Scenarios of docs/usage/clues.md

const JUDGE_HARMED_MARTHE =
  "Hidden crime: C = Judge Adam, V = Frau Marthe, I = ?";
const MURDER = "Hidden crime: C = Macbeth, V = King Duncan, I = ?";

test.beforeAll(() => {
  test.setTimeout(120_000);
  seed("broken-jug", "macbeth");
});

async function openClues(page: Page, title: string) {
  await page.goto("/");
  await page.getByRole("link", { name: title }).click();
  await page.getByRole("link", { name: "Story map" }).click();
  await page
    .getByRole("navigation", { name: "Story map views" })
    .getByRole("link", { name: "Clues" })
    .click();
}

/** The footer of a ledger: its label, then one verdict per player, by player. */
async function footer(ledger: Locator): Promise<Record<string, string>> {
  await ledger.waitFor();
  const headers = await ledger.getByRole("columnheader").allTextContents();
  const players = headers.slice(3);
  const label = await ledger.getByRole("rowheader").textContent();
  const verdicts = await ledger
    .getByRole("row")
    .last()
    .getByRole("cell")
    .allTextContents();
  return {
    label: label ?? "",
    ...Object.fromEntries(
      players.map((player, index) => [player, verdicts[index] ?? ""]),
    ),
  };
}

test("Open the clue ledger", async ({ page }) => {
  await openClues(page, "The Broken Jug (an adventure)");

  await expect(
    page
      .getByRole("navigation", { name: "Story map views" })
      .getByRole("link", { name: "Clues" }),
  ).toHaveAttribute("aria-current", "page");
  const reading = page.getByRole("combobox", { name: "Reading" });
  await expect(reading.locator("option:checked")).toHaveText(
    JUDGE_HARMED_MARTHE,
  );
  const ledger = page.getByRole("table", {
    name: `Clues to ${JUDGE_HARMED_MARTHE}`,
  });
  await expect(ledger.getByRole("row").nth(1)).toHaveText(
    /^3.*crime.*learned at t = 26 via beat 26/,
  );
  await expect(
    ledger.getByRole("row").filter({ hasText: "discovery (payoff)" }),
  ).toHaveCount(4);
});

test("See whether the players were prepared", async ({ page }) => {
  await openClues(page, "The Broken Jug (an adventure)");

  expect(
    await footer(
      page.getByRole("table", { name: `Clues to ${JUDGE_HARMED_MARTHE}` }),
    ),
  ).toEqual({
    label: "Clues before the payoff at t = 26",
    Anna: "4 of 7",
    Ben: "5 of 7",
    Clara: "4 of 7",
  });
});

test("Find a player who was not", async ({ page }) => {
  await openClues(page, "Macbeth (a session)");

  await page
    .getByRole("combobox", { name: "Reading" })
    .selectOption({ label: MURDER });

  expect(
    await footer(page.getByRole("table", { name: `Clues to ${MURDER}` })),
  ).toEqual({
    label: "Clues before the payoff at t = 32",
    Anna: "knew it from the start",
    Ben: "knew it from the start",
    Clara: "2 of 4: fewer than three",
    Dora: "2 of 4: fewer than three",
  });
});
