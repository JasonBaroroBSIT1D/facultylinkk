"use strict";

const { test, expect } = require("@playwright/test");

const API = process.env.FLASK_API_BASE || "http://127.0.0.1:5000";
const WEB = process.env.WEB_PUBLIC_URL || "http://127.0.0.1:8080";

async function adminToken(request) {
  if (process.env.QA_ADMIN_TOKEN) return process.env.QA_ADMIN_TOKEN;
  const email = process.env.QA_ADMIN_EMAIL;
  const password = process.env.QA_ADMIN_PASSWORD;
  if (!email || !password) return null;
  const res = await request.post(`${API}/api/auth/login`, {
    data: { email, password, client: "web" },
  });
  if (!res.ok()) return null;
  const body = await res.json();
  return body.accessToken || body.access_token || null;
}

function kra4IndicatorIds(kraSettings) {
  const indicators = (kraSettings && kraSettings.indicators) || {};
  return Object.keys(indicators).filter((id) => id.startsWith("kra4-"));
}

test.describe("KRA IV admin scoring configuration", () => {
  test("API: draft lists 19 KRA IV indicators", async ({ request }) => {
    const token = await adminToken(request);
    test.skip(!token, "Set QA_ADMIN_EMAIL + QA_ADMIN_PASSWORD (QA DB admin only)");

    const draftRes = await request.get(`${API}/api/admin/kra-configuration/draft`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(draftRes.ok()).toBeTruthy();
    const draft = await draftRes.json();
    const settings = (draft.draft && draft.draft.kraSettings) || draft.kraSettings;
    const ids = kra4IndicatorIds(settings);
    expect(ids.length).toBe(19);
  });

  test("Browser: KRA IV section visible on admin configuration page", async ({ page }) => {
    const email = process.env.QA_ADMIN_EMAIL;
    const password = process.env.QA_ADMIN_PASSWORD;
    test.skip(!email || !password, "Admin QA credentials not configured");

    const apiBase = API.replace(/\/$/, "");
    await page.addInitScript((base) => {
      window.FL_API_BASE = base;
    }, apiBase);

    await page.goto(`${WEB}/pages/public/login.html`);
    await page.fill("#identity", email);
    await page.fill("#password", password);
    await page.click("#sign-in");
    await expect(page.locator("#login-success")).toBeVisible({ timeout: 15000 });
    await page.waitForURL(/\/pages\/admin\//, { timeout: 30000 });

    await page.goto(`${WEB}/pages/admin/kra-configuration.html`);
    await expect(page.locator("body")).toContainText(/KRA IV|Professional Development/i, { timeout: 25000 });
    await expect(page.locator("body")).toContainText(/kra4-a-member|Membership/i, { timeout: 25000 });
  });
});
