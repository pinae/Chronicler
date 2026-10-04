import { expect, test } from "@playwright/test";

import { seed } from "./seed";

// Scenarios of docs/usage/browse-chronicles.md

test("See all chronicles", async ({ page }) => {
  seed("minimal", "steward");

  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Chronicles" })).toBeVisible();
  await expect(
    page.getByRole("link", { name: "The Steward of Wend" }),
  ).toBeVisible();
  await expect(page.getByText("session · 24 beats")).toBeVisible();
  await expect(
    page.getByRole("link", { name: "The Minimal Hall" }),
  ).toBeVisible();
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

test("Switch between light and dark", async ({ page }) => {
  seed("minimal");
  await page.goto("/");

  await page.getByLabel("Theme").selectOption({ label: "Dark" });

  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.reload();
  await expect(page.getByLabel("Theme")).toHaveValue("dark");
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");

  await page.getByLabel("Theme").selectOption({ label: "System" });

  await expect(page.locator("html")).not.toHaveAttribute("data-theme", /./);
});
