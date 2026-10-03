import { expect, test } from "@playwright/test";

import { seed } from "./seed";

// Scenarios of docs/usage/browse-chronicles.md

test("See all chronicles", async ({ page }) => {
  seed("minimal", "steward");

  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Chronicles" })).toBeVisible();
  await expect(page.getByRole("link", { name: "The Steward of Wend" })).toBeVisible();
  await expect(page.getByText("session · 24 beats")).toBeVisible();
  await expect(page.getByRole("link", { name: "The Minimal Hall" })).toBeVisible();
  await expect(page.getByText("session · 5 beats")).toBeVisible();
});

test("No chronicles yet", async ({ page }) => {
  seed();

  await page.goto("/");

  await expect(page.getByText("No chronicles yet")).toBeVisible();
});

test("The backend cannot be reached", async ({ page }) => {
  await page.route("**/api/chronicles/", (route) => route.abort());

  await page.goto("/");

  await expect(page.getByText("Could not load the chronicles.")).toBeVisible();
});
