import { expect, test, type Page } from "@playwright/test";

import { seed } from "./seed";

// Scenarios of docs/usage/guided-tour.md

const MACBETH = "Macbeth (a session)";
const BROKEN_JUG = "The Broken Jug (an adventure)";
const OPEN_STEPS_COLUMN = 4;

test.beforeAll(() => {
  test.setTimeout(120_000);
  seed("macbeth", "broken-jug");
});

async function openLattice(page: Page, title: string) {
  await page.goto("/");
  await page.getByRole("link", { name: title }).click();
  await page.getByRole("link", { name: "Lattice" }).click();
  await expect(
    page.getByRole("heading", { name: `Lattice of ${title}` }),
  ).toBeVisible();
}

async function openKnowledge(page: Page, title: string) {
  await page.goto("/");
  await page.getByRole("link", { name: title }).click();
  await page.getByRole("link", { name: "Who knows what" }).click();
  await expect(
    page.getByRole("heading", { name: `Who knows what in ${title}` }),
  ).toBeVisible();
}

async function view(page: Page, audience: string, t: string) {
  await page.getByLabel("Seen by").selectOption({ label: audience });
  await page.getByLabel("Up to beat").fill(t);
}

function schemaTable(page: Page, schemaName: string) {
  return page.getByRole("table", { name: schemaName });
}

function row(page: Page, schemaName: string, binding: string) {
  return schemaTable(page, schemaName)
    .getByRole("row")
    .filter({ hasText: binding });
}

function strongest(page: Page, schemaName: string) {
  return schemaTable(page, schemaName).getByRole("row").nth(1);
}

function knownBeat(page: Page, text: string) {
  return page
    .getByRole("table", { name: "Known beats" })
    .getByRole("row")
    .filter({ hasText: text });
}

test("Before you start", async ({ page }) => {
  await page.goto("/");

  await expect(
    page.getByRole("listitem").filter({ hasText: MACBETH }),
  ).toContainText("session · 36 beats");
  await expect(
    page.getByRole("listitem").filter({ hasText: BROKEN_JUG }),
  ).toContainText("session · 32 beats");
});

test("The game master sees the plot lines of the play", async ({ page }) => {
  await openLattice(page, MACBETH);

  await expect(strongest(page, "Usurpation")).toContainText(
    "U = Macbeth, R = King Duncan, P = The crown of Scotland",
  );
  await expect(strongest(page, "Usurpation")).toContainText("complete");
  await expect(strongest(page, "Usurpation")).toContainText("murder (t=17)");
  await expect(strongest(page, "Usurpation")).toContainText("seizure (t=22)");

  await expect(strongest(page, "Prophecy")).toContainText(
    "S = The three witches, H = Macbeth, X = The crown of Scotland",
  );
  await expect(strongest(page, "Prophecy")).toContainText("complete");
  const fleance = row(page, "Prophecy", "H = Fleance");
  await expect(fleance).toContainText("live");
  await expect(fleance.getByRole("cell").nth(OPEN_STEPS_COLUMN)).toContainText(
    "fulfilment",
  );

  await expect(strongest(page, "Hidden crime")).toContainText(
    "C = Macbeth, V = King Duncan, I = Macduff",
  );
  await expect(strongest(page, "Hidden crime")).toContainText("complete");
  await expect(strongest(page, "Hidden crime")).toContainText(
    "cover_up (t=20)",
  );
  await expect(strongest(page, "Hidden crime")).toContainText(
    "discovery (t=33)",
  );
});

test("A dead investigator discovers nothing", async ({ page }) => {
  await openLattice(page, MACBETH);

  await expect(
    row(page, "Hidden crime", "C = Macbeth, V = King Duncan, I = Banquo"),
  ).toContainText("refuted");
});

test("Dora does not know of the murder until the doctor's report", async ({
  page,
}) => {
  await openLattice(page, MACBETH);
  await view(page, "Dora", "31");

  await expect(page.getByText("t = 31 of 36")).toBeVisible();
  const usurpation = row(
    page,
    "Usurpation",
    "U = Macbeth, R = King Duncan, P = The crown of Scotland",
  );
  await expect(usurpation).toContainText("live");
  await expect(usurpation).toContainText("0.00");
  await expect(
    usurpation.getByRole("cell").nth(OPEN_STEPS_COLUMN),
  ).toContainText("murder");
  await expect(
    row(page, "Hidden crime", "C = Macbeth, V = King Duncan"),
  ).toHaveCount(0);

  await page.getByLabel("Up to beat").fill("32");

  await expect(usurpation).toContainText("2.00");
  await expect(usurpation).toContainText("murder (t=17)");
  await expect(
    row(page, "Hidden crime", "C = Macbeth, V = King Duncan, I = The doctor"),
  ).toContainText("complete");
});

test("Clara voices what she suspects", async ({ page }) => {
  await openLattice(page, MACBETH);
  await view(page, "Clara", "23");

  const theory = row(
    page,
    "Hidden crime",
    "C = Macbeth, V = King Duncan, I = ? (voiced)",
  );
  await expect(theory).toContainText("-2.00");

  await page.getByLabel("Up to beat").fill("32");

  await expect(theory).toContainText("crime (t=17)");
  await expect(theory).toContainText("-1.00");
});

test("Who knows what about the murder", async ({ page }) => {
  await openKnowledge(page, MACBETH);
  const murder =
    "Macbeth kills the sleeping Duncan while his wife keeps watch.";

  await page.getByLabel("Who").selectOption({ label: "Dora" });
  await page.getByLabel("Up to beat").fill("31");
  await expect(
    knownBeat(page, "Macbeth has Macduff's family slaughtered."),
  ).toBeVisible();
  await expect(knownBeat(page, murder)).toHaveCount(0);

  await page.getByLabel("Up to beat").fill("32");
  await expect(knownBeat(page, murder)).toContainText("learned at t = 32");

  await page.getByLabel("Who").selectOption({ label: "Ben" });
  await expect(knownBeat(page, murder)).toContainText("saw it");
});

test("The game master knows from the first scene", async ({ page }) => {
  await openLattice(page, BROKEN_JUG);
  await page.getByLabel("Up to beat").fill("3");

  await expect(
    row(page, "Hidden crime", "C = Judge Adam, V = Frau Marthe, I = ?"),
  ).toContainText("crime (t=3)");
  await expect(
    row(page, "Hidden crime", "C = Judge Adam, V = Eve, I = ?"),
  ).toContainText("crime (t=2)");
});

test("The players start with nothing", async ({ page }) => {
  await openLattice(page, BROKEN_JUG);
  await view(page, "Anna", "15");

  await expect(page.getByText("No hypotheses at this point")).toBeVisible();

  await page.getByLabel("Up to beat").fill("16");

  await expect(
    row(page, "Hidden crime", "C = Ruprecht, V = Frau Marthe, I = ? (voiced)"),
  ).toContainText("-2.00");
  await expect(schemaTable(page, "Hidden crime").getByRole("row")).toHaveCount(
    2,
  );
});

test("A suspicion said aside stays with the player who said it", async ({
  page,
}) => {
  await openLattice(page, BROKEN_JUG);
  await view(page, "Ben", "19");

  await expect(
    row(page, "Hidden crime", "C = Judge Adam, V = ?, I = Licht"),
  ).toContainText("suspicion (t=19)");
  await expect(
    row(
      page,
      "Hidden crime",
      "C = Judge Adam, V = Frau Marthe, I = ? (voiced)",
    ),
  ).toHaveCount(1);

  await page.getByLabel("Seen by").selectOption({ label: "Clara" });

  await expect(
    row(page, "Hidden crime", "C = Lebrecht, V = Frau Marthe, I = ? (voiced)"),
  ).toHaveCount(1);
  await expect(schemaTable(page, "Hidden crime").getByRole("row")).toHaveCount(
    2,
  );
});

test("Ask what Ben expects the judge to have done", async ({ page }) => {
  await openLattice(page, BROKEN_JUG);
  await view(page, "Ben", "19");

  await page
    .getByRole("button", {
      name: "Expectations for C = Judge Adam, V = ?, I = Licht",
    })
    .click();

  const panel = page.getByRole("region", {
    name: "Expectations for C = Judge Adam, V = ?, I = Licht",
  });
  await expect(panel.getByText("Next: Judge Adam harms ___.")).toBeVisible();
  await expect(panel.getByText("asked at t = 19")).toBeVisible();
  await expect(panel.getByText("Eve: 13%")).toBeVisible();
  await expect(panel.getByText("Frau Marthe: 13%")).toBeVisible();
  await expect(panel.getByText("nothing like this yet: 13%")).toBeVisible();
});

test("The engine connects the judge's accusation with Walter's suspicion", async ({
  page,
}) => {
  await openLattice(page, BROKEN_JUG);
  await view(page, "Clara", "25");

  const connected = row(
    page,
    "Hidden crime",
    "C = Judge Adam, V = Frau Marthe, I = Walter",
  );
  await expect(connected).toContainText("suspicion (t=21, 24)");
  await expect(connected).toContainText("cover_up (t=25)");
});

test("The confession", async ({ page }) => {
  await openLattice(page, BROKEN_JUG);
  await view(page, "Anna", "25");

  const annasTheory = row(
    page,
    "Hidden crime",
    "C = Judge Adam, V = Frau Marthe, I = Walter (voiced)",
  );
  await expect(annasTheory).toContainText("live");
  await expect(annasTheory.getByRole("cell").nth(3)).toHaveText(
    "cover_up (t=25)",
  );

  await page.getByLabel("Up to beat").fill("26");

  await expect(annasTheory).toContainText("complete");
  await expect(annasTheory).toContainText(
    "crime (t=3); cover_up (t=25); discovery (t=26)",
  );
});

test("Who knows what about the jug", async ({ page }) => {
  await openKnowledge(page, BROKEN_JUG);
  const brokenJug =
    "Adam breaks Frau Marthe's jug as he leaps out of the window.";

  await page.getByLabel("Who").selectOption({ label: "Anna" });
  await page.getByLabel("Up to beat").fill("25");
  await expect(
    knownBeat(page, "Adam sentences Ruprecht for breaking the jug."),
  ).toBeVisible();
  await expect(knownBeat(page, brokenJug)).toHaveCount(0);

  await page.getByLabel("Up to beat").fill("26");
  await expect(knownBeat(page, brokenJug)).toContainText("learned at t = 26");
});
