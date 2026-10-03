import { defineConfig, devices } from "@playwright/test";

// The scenarios in docs/usage/ run against Django serving the built frontend (ADR-007), with the
// e2e settings: a throwaway SQLite database that each test seeds with fixture stories.
const port = 8001;
const e2eSettings = "--settings=narrative_engine.settings.e2e";

export default defineConfig({
  testDir: "./tests",
  // All tests share one database, so they run one after another.
  fullyParallel: false,
  workers: 1,
  forbidOnly: Boolean(process.env.CI),
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: `http://127.0.0.1:${port}`,
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: [
      "npm --prefix ../frontend run build",
      `cd ../backend && uv run python manage.py migrate ${e2eSettings} --verbosity 0`,
      `uv run python manage.py runserver 127.0.0.1:${port} --noreload ${e2eSettings}`,
    ].join(" && "),
    url: `http://127.0.0.1:${port}/healthz`,
    reuseExistingServer: !process.env.CI,
    timeout: 180_000,
  },
});
