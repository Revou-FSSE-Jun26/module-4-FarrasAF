import path from "node:path";
import { defineConfig, devices } from "@playwright/test";

const isCI = Boolean(process.env.CI);
const isWindows = process.platform === "win32";

const BACKEND_PORT = 5000;
const FRONTEND_PORT = 3000;
const BACKEND_URL = `http://localhost:${BACKEND_PORT}`;
// Set E2E_BASE_URL to run against an already deployed frontend (for example the
// Vercel URL). No local servers are started in that case.
const REMOTE_URL = process.env.E2E_BASE_URL?.replace(/\/+$/, "");
const FRONTEND_URL = REMOTE_URL ?? `http://localhost:${FRONTEND_PORT}`;

// Dedicated E2E database: never the dev or production database.
const E2E_DATABASE_URL =
  process.env.E2E_DATABASE_URL ??
  "postgresql+psycopg://taskapp:your_password@localhost:5432/taskmgmt_e2e";

const backendDir = path.resolve(__dirname, "..", "backend");
const venvPython = isWindows
  ? path.join(backendDir, "venv", "Scripts", "python.exe")
  : path.join(backendDir, "venv", "bin", "python");

export default defineConfig({
  testDir: "./e2e",
  // The route warm-up is only needed for `next dev`.
  globalSetup: REMOTE_URL ? undefined : "./e2e/global-setup.ts",
  fullyParallel: true,
  forbidOnly: isCI,
  retries: isCI || REMOTE_URL ? 2 : 0,
  // The free-tier backend may be asleep; allow slower first requests remotely.
  timeout: REMOTE_URL ? 60_000 : 30_000,
  workers: REMOTE_URL ? 2 : undefined,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: FRONTEND_URL,
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: REMOTE_URL
    ? undefined
    : [
    {
      command: `"${venvPython}" -m flask --app flask_app.app run --port ${BACKEND_PORT}`,
      cwd: backendDir,
      url: `${BACKEND_URL}/api/health`,
      reuseExistingServer: !isCI,
      env: {
        DATABASE_URL: E2E_DATABASE_URL,
        JWT_SECRET_KEY: "e2e-test-secret-key-not-for-production",
        COOKIE_SECURE: "false",
      },
    },
    {
      command: "npm run dev",
      cwd: __dirname,
      url: FRONTEND_URL,
      reuseExistingServer: !isCI,
      env: { API_URL: BACKEND_URL },
    },
  ],
});
