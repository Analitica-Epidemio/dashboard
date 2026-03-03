import { defineConfig } from "@playwright/test";
import "dotenv/config";

const BASE_URL = process.env.BASE_URL ?? "http://localhost:3000";

export default defineConfig({
  testDir: "src/tests",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: "html",
  timeout: 30_000,

  use: {
    baseURL: BASE_URL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },

  projects: [
    {
      name: "chromium",
      use: { browserName: "chromium" },
    },
  ],

  // El servidor ya está corriendo manualmente.
  // Descomenta esto si querés que Playwright lo levante automáticamente:
  // webServer: {
  //   command: "cd ../frontend && pnpm dev",
  //   url: BASE_URL,
  //   reuseExistingServer: true,
  //   timeout: 120_000,
  // },
});
