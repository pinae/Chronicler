import { expect, test, type Page } from "@playwright/test";

import { seed } from "./seed";

// Scenarios of docs/usage/knowledge.md

test.beforeAll(() => {
  seed("steward");
});

async function openKnowledge(page: Page) {
  await page.goto("/");
  await page.getByRole("link", { name: "The Steward of Wend" }).click();
  await page.getByRole("link", { name: "Who knows what" }).click();
  await expect(page.getByRole("heading", { name: "Who knows what in The Steward of Wend" })).toBeVisible();
}

function knownBeat(page: Page, text: string) {
  return page.getByRole("table", { name: "Known beats" }).getByRole("row").filter({ hasText: text });
}

test("Open the knowledge screen", async ({ page }) => {
  await openKnowledge(page);

  await expect(page.getByLabel("Who")).toBeVisible();
  await expect(page.getByLabel("Up to beat")).toBeVisible();
  await expect(page.getByText("Choose a character or a player.")).toBeVisible();
});

test("What a character witnessed", async ({ page }) => {
  await openKnowledge(page);

  await page.getByLabel("Who").selectOption({ label: "Mira" });

  await expect(knownBeat(page, "Mira trusts Aldric.").first()).toContainText("present");
});

test("A character learns a secret later", async ({ page }) => {
  await openKnowledge(page);
  await page.getByLabel("Who").selectOption({ label: "Mira" });

  await page.getByLabel("Up to beat").fill("21");
  await expect(knownBeat(page, "Mira is suspicious.")).toBeVisible();
  await expect(knownBeat(page, "Aldric steals the seal from Mira.")).toHaveCount(0);

  await page.getByLabel("Up to beat").fill("22");
  await expect(knownBeat(page, "Aldric steals the seal from Mira.")).toContainText("learned at t = 22");
});

test("What a player was shown", async ({ page }) => {
  await openKnowledge(page);

  await page.getByLabel("Who").selectOption({ label: "Ben" });
  await expect(knownBeat(page, "Aldric learns where Mira hides the seal.")).toContainText("saw it");

  await page.getByLabel("Who").selectOption({ label: "Anna" });
  await expect(knownBeat(page, "Mira holds court in the great hall.")).toBeVisible();
  await expect(knownBeat(page, "Aldric learns where Mira hides the seal.")).toHaveCount(0);
});
