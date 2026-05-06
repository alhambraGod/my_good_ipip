import { defineConfig, devices } from "@playwright/test";

const PORT = Number(process.env.E2E_PORT ?? 3100);
const BASE_URL = process.env.E2E_BASE_URL ?? `http://localhost:${PORT}`;

export default defineConfig({
  testDir: "./e2e",
  testMatch: /.*\.spec\.ts$/,
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: process.env.CI ? "github" : [["list"]],
  timeout: 60_000,
  expect: { timeout: 8_000 },
  use: {
    baseURL: BASE_URL,
    trace: process.env.CI ? "on-first-retry" : "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    actionTimeout: 8_000,
    navigationTimeout: 30_000,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: process.env.E2E_NO_WEBSERVER
    ? undefined
    : {
        // Build once, then `next start` is faster + closer to prod than next dev,
        // and avoids the React dev-server console noise polluting traces.
        command: `npm run build && npm run start -- --port ${PORT}`,
        port: PORT,
        reuseExistingServer: !process.env.CI,
        stdout: "pipe",
        stderr: "pipe",
        timeout: 240_000,
        env: {
          // Point the frontend at a deliberately-unreachable backend so server
          // components fall back to their empty states gracefully. The smoke
          // suite tests the chrome (header, hero, FAQ, archetypes empty,
          // language toggle, 404, robots/sitemap), not data flow.
          NEXT_PUBLIC_API_URL: process.env.E2E_API_URL ?? "http://127.0.0.1:1",
          NEXT_PUBLIC_SITE_URL: BASE_URL,
        },
      },
});
