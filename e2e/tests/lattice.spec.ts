import { expect, test, type Page } from "@playwright/test";

import { seed } from "./seed";

// Scenarios of docs/usage/lattice.md

test.beforeAll(() => {
  seed("steward");
});

async function openLattice(page: Page) {
  await page.goto("/");
  await page.getByRole("link", { name: "The Steward of Wend" }).click();
  await page.getByRole("link", { name: "Lattice" }).click();
  await expect(page.getByRole("heading", { name: "Lattice of The Steward of Wend" })).toBeVisible();
}

function row(page: Page, binding: string) {
  return page.getByRole("table", { name: "Betrayal" }).getByRole("row").filter({ hasText: binding });
}

test("See which stories the chronicle supports", async ({ page }) => {
  await openLattice(page);

  await expect(page.getByRole("heading", { name: "Betrayal" })).toBeVisible();
  const strongest = page.getByRole("table", { name: "Betrayal" }).getByRole("row").nth(1);
  await expect(strongest).toContainText("T = Aldric, V = Mira, S = The family seal");
  await expect(strongest).toContainText("complete");
  await expect(strongest).toContainText("harm (t=13)");
  await expect(strongest).toContainText("reveal (t=22)");
});

test("See the lattice before the twist", async ({ page }) => {
  await openLattice(page);

  await page.getByLabel("Up to beat").fill("21");

  await expect(page.getByText("t = 21 of 24")).toBeVisible();
  const sealBetrayal = row(page, "T = Aldric, V = Mira, S = The family seal");
  await expect(sealBetrayal).toContainText("live");
  await expect(sealBetrayal.getByRole("cell").last()).toContainText("reveal");
});

test("See a player's lattice", async ({ page }) => {
  await openLattice(page);

  await page.getByLabel("Seen by").selectOption({ label: "Anna" });

  await expect(page.getByText("T = Aldric, V = Mira, S = ?").first()).toBeVisible();
  await expect(page.getByText("S = The family seal")).toHaveCount(0);
});

test("Spot a theory a player voiced", async ({ page }) => {
  await openLattice(page);

  await page.getByLabel("Up to beat").fill("10");

  await expect(row(page, "T = Aldric, V = ?, S = ? (voiced)")).toHaveCount(1);
});
