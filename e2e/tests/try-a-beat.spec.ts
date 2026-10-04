import { expect, test, type Page } from "@playwright/test";

import { seed } from "./seed";

// Scenarios of docs/usage/try-a-beat.md

test.beforeAll(() => {
  seed("steward");
});

async function openForm(page: Page) {
  await page.goto("/");
  await page.getByRole("link", { name: "The Steward of Wend" }).click();
  await page.getByRole("link", { name: "Try a beat" }).click();
  await expect(page.getByRole("heading", { name: "Try a beat in The Steward of Wend" })).toBeVisible();
}

async function compose(page: Page, predicate: string, roles: Record<string, string>) {
  await page.getByLabel("Predicate").selectOption(predicate);
  for (const [role, value] of Object.entries(roles)) {
    await page.getByRole("combobox", { name: role, exact: true }).selectOption({ label: value });
  }
}

function effect(page: Page, hypothesis: string) {
  return page.getByRole("table", { name: "Effects" }).getByRole("row").filter({ hasText: hypothesis });
}

test("Open the form", async ({ page }) => {
  await openForm(page);

  await expect(page.getByLabel("Predicate")).toBeVisible();
  await expect(page.getByRole("group", { name: "Present" }).getByLabel("Mira")).not.toBeChecked();
  await expect(page.getByRole("group", { name: "Shown to" }).getByLabel("Anna")).toBeChecked();
  await expect(page.getByLabel("Lattice of")).toBeVisible();
  await expect(page.getByRole("button", { name: "Try it" })).toBeVisible();
});

test("A beat that starts a new suspicion", async ({ page }) => {
  await openForm(page);
  await compose(page, "trusts", { who: "Edda", whom: "Mira" });

  await page.getByRole("button", { name: "Try it" }).click();

  await expect(page.getByRole("heading", { name: "If this were beat 25" })).toBeVisible();
  const row = effect(page, "Betrayal: T = Mira, V = Edda, S = ?");
  await expect(row).toContainText("seeded (trust)");
  await expect(row).toContainText("new: -1.5");
});

test("A beat that strengthens a suspicion", async ({ page }) => {
  await openForm(page);
  await compose(page, "helps", { who: "Mira", whom: "Aldric" });

  await page.getByRole("button", { name: "Try it" }).click();

  const row = effect(page, "Betrayal: T = Mira, V = Aldric, S = ?");
  await expect(row).toContainText("filled trust");
  await expect(row).toContainText("-1.5 → -1.0");
});

test("A beat that refutes a suspicion", async ({ page }) => {
  await openForm(page);
  await compose(page, "kills", { who: "The raider", whom: "Mira" });

  await page.getByRole("button", { name: "Try it" }).click();

  await expect(effect(page, "Betrayal: T = Mira, V = Aldric, S = ?")).toContainText("refuted");
});

test("A player's lattice only changes if the player sees the beat", async ({ page }) => {
  await openForm(page);
  await compose(page, "helps", { who: "Mira", whom: "Aldric" });
  const anna = page.getByRole("group", { name: "Shown to" }).getByLabel("Anna");
  await anna.uncheck();
  await page.getByLabel("Lattice of").selectOption({ label: "Anna" });

  await page.getByRole("button", { name: "Try it" }).click();
  await expect(page.getByText("No hypothesis would change.")).toBeVisible();

  await anna.check();
  await page.getByRole("button", { name: "Try it" }).click();
  await expect(effect(page, "Betrayal: T = Mira, V = Aldric, S = ?")).toContainText("filled trust");
});

test("A beat with a missing role", async ({ page }) => {
  await openForm(page);
  await compose(page, "steals", { who: "Aldric" });

  await page.getByRole("button", { name: "Try it" }).click();

  await expect(page.getByRole("alert")).toHaveText("steals: missing role 'from'");
});

test("Nothing you try is kept", async ({ page }) => {
  await openForm(page);
  await compose(page, "kills", { who: "The raider", whom: "Mira" });
  await page.getByRole("button", { name: "Try it" }).click();
  await expect(page.getByRole("table", { name: "Effects" })).toBeVisible();

  await page.getByRole("link", { name: "Beats of The Steward of Wend" }).click();

  await expect(page.getByText("t = 24 of 24")).toBeVisible();
});
