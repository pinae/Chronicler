import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const backendDir = fileURLToPath(new URL("../../backend", import.meta.url));

/** Replaces all data in the e2e database with the given fixture stories (none: an empty database). */
export function seed(...stories: string[]): void {
  execFileSync(
    "uv",
    [
      "run",
      "python",
      "manage.py",
      "seed_e2e",
      ...stories,
      "--settings=narrative_engine.settings.e2e",
    ],
    { cwd: backendDir, stdio: "pipe" },
  );
}
