import path from "node:path";
import { defineConfig, devices } from "@playwright/test";

const isCI = Boolean(process.env.CI);
const isWindows = process.platform === "win32";

const BACKEND_PORT = 5000;
const FRONTEND_PORT = 3000;
const BACKEND_URL = `http://localhost:${BACKEND_PORT}`;
const FRONTEND_URL = `http://localhost:${FRONTEND_PORT}`;

// Dedicated E2E database: never the dev or production database.
const E2E_DATABASE_URL =
  process.env.E2E_DATABASE_URL ??
  "postgresql+psycopg://postgres:root@localhost:5432/taskmgmt_e2e";

const backendDir = path.resolve(__dirname, "..", "backend");
const venvPython = isWindows
  ? path.join(backendDir, "venv", "Scripts", "python.exe")
  : path.join(backendDir, "venv", "bin", "python");

export default defineConfig({
  testDir: "./e2e",
  globalSetup: "./e2e/global-setup.ts",
  fullyParallel: true,
  forbidOnly: isCI,
  retries: isCI ? 2 : 0,
  reporter: "list",
  use: {
    baseURL: FRONTEND_URL,
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
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
