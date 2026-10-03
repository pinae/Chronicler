import { expect, test } from "@playwright/test";

import { seed } from "./seed";

// Scenarios of docs/usage/chronicle.md

test.beforeAll(() => {
  seed("steward");
});

async function openSteward(page: import("@playwright/test").Page) {
  await page.goto("/");
  await page.getByRole("link", { name: "The Steward of Wend" }).click();
  await expect(page.getByRole("heading", { name: "The Steward of Wend" })).toBeVisible();
}

test("Read a chronicle", async ({ page }) => {
  await openSteward(page);

  await expect(page.getByText("session", { exact: true })).toBeVisible();
  const beats = page.getByRole("table", { name: "Beats" });
  await expect(beats.getByRole("row")).toHaveCount(25);
  await expect(beats.getByText("Aldric steals the seal from Mira.")).toBeVisible();
  await expect(page.getByText("t = 24 of 24")).toBeVisible();
  await expect(page.getByLabel("Seen by")).toHaveValue("all");
});

test("See what the table saw", async ({ page }) => {
  await openSteward(page);

  await page.getByLabel("Seen by").selectOption({ label: "The table" });

  await expect(page.getByText("Mira trusts Aldric.")).toBeVisible();
  await expect(page.getByText("Aldric steals the seal from Mira.")).toHaveCount(0);
  await expect(page.getByText("Aldric learns where Mira hides the seal.")).toHaveCount(0);
});

test("See one player's view", async ({ page }) => {
  await openSteward(page);

  await page.getByLabel("Seen by").selectOption({ label: "Ben" });

  await expect(page.getByText("Aldric learns where Mira hides the seal.")).toBeVisible();
  await expect(page.getByText("Mira hides the seal in the cellar.")).toHaveCount(0);
});

test("Go back in time", async ({ page }) => {
  await openSteward(page);

  await page.getByLabel("Up to beat").fill("10");

  await expect(page.getByText("t = 10 of 24")).toBeVisible();
  await expect(page.getByText("The raider kills Ronan at the gate.")).toBeVisible();
  await expect(page.getByText("Aldric steals the seal from Mira.")).toHaveCount(0);
});

test("A chronicle that does not exist", async ({ page }) => {
  await page.goto("/chronicles/999");

  await expect(page.getByText("Chronicle not found")).toBeVisible();
});
