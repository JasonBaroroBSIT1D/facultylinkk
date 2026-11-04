"use strict";

const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
  testDir: ".",
  timeout: 120000,
  retries: 0,
  globalSetup: require.resolve("./global-setup.js"),
  use: {
    baseURL: process.env.WEB_BASE || "http://127.0.0.1:8080",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  reporter: [["list"], ["json", { outputFile: "../../docs/KRA2_CRITERION_B_PLAYWRIGHT_REPORT.json" }]],
});
