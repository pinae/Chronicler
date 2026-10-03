import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// The Django development server (ADR-007): the Vite dev server forwards API and admin requests to it.
const backend = "http://127.0.0.1:8000";

export default defineConfig(({ command }) => ({
  plugins: [react()],
  // Django serves the build as static files under /static/; the dev server serves from the root.
  base: command === "build" ? "/static/" : "/",
  server: {
    proxy: { "/api": backend, "/admin": backend, "/static/admin": backend },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
  },
}));
