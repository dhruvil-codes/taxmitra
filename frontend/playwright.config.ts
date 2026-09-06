import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  retries: 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: "http://127.0.0.1:4173",
    browserName: "chromium",
    launchOptions: { executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" },
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: [
    { command: "npm.cmd run dev -- --host 127.0.0.1 --port 4173", cwd: ".", url: "http://127.0.0.1:4173", reuseExistingServer: true, timeout: 120_000, gracefulShutdown: { signal: "SIGINT", timeout: 1_000 } },
    { command: "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000", cwd: "../backend", url: "http://127.0.0.1:8000/api/health", reuseExistingServer: true, timeout: 120_000, gracefulShutdown: { signal: "SIGINT", timeout: 1_000 } },
  ],
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile", use: { ...devices["iPhone 13"] } },
  ],
});
