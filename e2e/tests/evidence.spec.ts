import { expect, test, type Locator, type Page } from "@playwright/test";

import { seed } from "./seed";

// Scenarios of docs/usage/evidence.md

const JUG = "The Broken Jug (an adventure)";
const JUDGE_HARMED_MARTHE =
  "Hidden crime: C = Judge Adam, V = Frau Marthe, I = ?";
const JUDGE_HARMED_EVE = "Hidden crime: C = Judge Adam, V = Eve, I = ?";
const RUPRECHT = "Hidden crime: C = Ruprecht, V = Frau Marthe, I = ?";
const LEBRECHT = "Hidden crime: C = Lebrecht, V = Frau Marthe, I = ?";

test.beforeAll(() => {
  test.setTimeout(120_000);
  seed("broken-jug", "macbeth");
});

async function openEvidence(page: Page, title: string) {
  await page.goto("/");
  await page.getByRole("link", { name: title }).click();
  await page.getByRole("link", { name: "Story map" }).click();
  await page
    .getByRole("navigation", { name: "Story map views" })
    .getByRole("link", { name: "Evidence" })
    .click();
}

/** The cells of one beat's row, by column header without the share. */
async function evidenceRow(
  table: Locator,
  t: number,
): Promise<Record<string, string>> {
  await table.waitFor();
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
      header.replace(/ \((\d+%|refuted)\)$/, ""),
      cells[index] ?? "",
    ]),
  );
}

test("Open the evidence matrix", async ({ page }) => {
  await openEvidence(page, JUG);

  await expect(
    page
      .getByRole("navigation", { name: "Story map views" })
      .getByRole("link", { name: "Evidence" }),
  ).toHaveAttribute("aria-current", "page");
  await expect(page.getByRole("combobox", { name: "Seen by" })).toHaveValue(
    "all",
  );
  await expect(
    page.getByRole("spinbutton", { name: "Up to beat" }),
  ).toHaveValue("32");
  const headers = await page
    .getByRole("table", { name: "Evidence seen by All beats" })
    .getByRole("columnheader")
    .allTextContents();
  expect(headers).toEqual([
    "t",
    "Beat",
    `${JUDGE_HARMED_MARTHE} (90%)`,
    `${JUDGE_HARMED_EVE} (10%)`,
    `${RUPRECHT} (0%)`,
    `${LEBRECHT} (0%)`,
    "Evidence",
  ]);
});

test("Find the beats that carry the plot", async ({ page }) => {
  await openEvidence(page, JUG);

  const matrix = page.getByRole("table", {
    name: "Evidence seen by All beats",
  });
  const confession = await evidenceRow(matrix, 26);
  expect(confession[JUDGE_HARMED_MARTHE]).toBe("discovery");
  expect(confession.Evidence).toBe("tells them apart");
  const suspicion = await evidenceRow(matrix, 19);
  expect([
    suspicion[JUDGE_HARMED_MARTHE],
    suspicion[JUDGE_HARMED_EVE],
    suspicion[RUPRECHT],
    suspicion[LEBRECHT],
    suspicion.Evidence,
  ]).toEqual(["suspicion", "suspicion", "", "", "tells them apart"]);
  expect((await evidenceRow(matrix, 14)).Evidence).toBe("supports none");
  for (let t = 1; t <= 32; t += 1) {
    const row = await evidenceRow(matrix, t);
    expect([row[RUPRECHT], row[LEBRECHT]]).toEqual(["", ""]);
  }
});

test("Look back to an earlier beat", async ({ page }) => {
  await openEvidence(page, JUG);

  const upTo = page.getByRole("spinbutton", { name: "Up to beat" });
  await upTo.fill("20");

  const matrix = page.getByRole("table", {
    name: "Evidence seen by All beats",
  });
  await expect(matrix.getByRole("row")).toHaveCount(21);
  const headers = await matrix.getByRole("columnheader").allTextContents();
  expect(headers.slice(2, 4)).toEqual([
    `${JUDGE_HARMED_MARTHE} (68%)`,
    `${JUDGE_HARMED_EVE} (25%)`,
  ]);
});

test("Weigh a player's evidence", async ({ page }) => {
  await openEvidence(page, "Macbeth (a session)");

  await page.getByRole("combobox", { name: "Seen by" }).selectOption("Dora");

  const matrix = page.getByRole("table", { name: "Evidence seen by Dora" });
  expect(
    (await evidenceRow(matrix, 29))[
      "Hidden crime: C = Macbeth, V = The grooms, I = ?"
    ],
  ).toBe("suspicion, refuted");
  expect(
    (await evidenceRow(matrix, 32))[
      "Hidden crime: C = Macbeth, V = King Duncan, I = ?"
    ],
  ).toBe("crime, discovery");
});
