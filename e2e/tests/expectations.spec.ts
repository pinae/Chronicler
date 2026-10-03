import { expect, test, type Page } from "@playwright/test";

import { seed } from "./seed";

// Scenarios of docs/usage/expectations.md

test.beforeAll(() => {
  seed("steward");
});

async function openLattice(page: Page) {
  await page.goto("/");
  await page.getByRole("link", { name: "The Steward of Wend" }).click();
  await page.getByRole("link", { name: "Lattice" }).click();
  await expect(page.getByRole("heading", { name: "Lattice of The Steward of Wend" })).toBeVisible();
}

test("See what the audience expects next", async ({ page }) => {
  await openLattice(page);
  await page.getByLabel("Up to beat").fill("10");

  await page.getByRole("button", { name: "Expectations for T = Aldric, V = ?, S = ?" }).click();

  const panel = page.getByRole("region", { name: "Expectations for T = Aldric, V = ?, S = ?" });
  await expect(panel.getByText("Next: ___ trusts Aldric.")).toBeVisible();
  await expect(panel.getByText("asked at t = 10")).toBeVisible();
  await expect(panel.getByText("Mira: 17%")).toBeVisible();
  await expect(panel.getByText("nothing like this yet: 17%")).toBeVisible();
});

test("A hypothesis nobody was asked about", async ({ page }) => {
  await openLattice(page);

  await page.getByRole("button", { name: "Expectations for T = Aldric, V = Mira, S = The family seal" }).click();

  const panel = page.getByRole("region", { name: "Expectations for T = Aldric, V = Mira, S = The family seal" });
  await expect(panel.getByText("No expectations yet")).toBeVisible();
});
