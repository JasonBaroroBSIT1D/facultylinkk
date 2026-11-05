"use strict";

const { test, expect } = require("@playwright/test");
const fs = require("fs");
const path = require("path");

const REPORT = path.join(__dirname, "../../docs/KRA4_LIVE_QA_REPORT.json");
const API = process.env.FLASK_API_BASE || "http://127.0.0.1:5000";
const WEB = process.env.WEB_PUBLIC_URL || "http://127.0.0.1:8080";
const SHOT_DIR = path.join(__dirname, "../../docs/qa-screenshots/kra4");

function loadReport() {
  if (!fs.existsSync(REPORT)) return null;
  return JSON.parse(fs.readFileSync(REPORT, "utf8"));
}

async function reviewerToken(request) {
  if (process.env.QA_REVIEWER_TOKEN) return process.env.QA_REVIEWER_TOKEN;
  const email = process.env.QA_REVIEWER_EMAIL;
  const password = process.env.QA_REVIEWER_PASSWORD;
  if (!email || !password) return null;
  const res = await request.post(`${API}/api/auth/login`, {
    data: { email, password, client: "web" },
  });
  if (!res.ok()) return null;
  const body = await res.json();
  return body.accessToken || body.access_token || null;
}

test.describe("KRA IV reviewer web", () => {
  test.beforeAll(() => {
    fs.mkdirSync(SHOT_DIR, { recursive: true });
  });

  test("API: faculty roster + KRA IV criteria summaries", async ({ request }) => {
    const report = loadReport();
    test.skip(!report, "Run backend/scripts/kra4_live_qa.py first");
    const token = await reviewerToken(request);
    test.skip(!token, "Set QA_REVIEWER_EMAIL + QA_REVIEWER_PASSWORD");

    const facultyId = report.facultyPublicId;
    test.skip(!facultyId, "Missing facultyPublicId in QA report");

    const roster = await request.get(`${API}/api/reviewer/me/faculty`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(roster.ok()).toBeTruthy();
    const rosterBody = await roster.json();
    const ids = (rosterBody.faculty || rosterBody.items || rosterBody || []).map((f) => f.publicId || f.id);
    expect(ids).toContain(facultyId);

    for (const crit of ["kra4-a", "kra4-b", "kra4-c", "kra4-d"]) {
      const sumRes = await request.get(`${API}/api/reviewer/me/faculty/${facultyId}/${crit}/summary`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      expect(sumRes.ok(), crit).toBeTruthy();
      const accRes = await request.get(`${API}/api/reviewer/me/faculty/${facultyId}/${crit}/accomplishments`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      expect(accRes.ok(), crit).toBeTruthy();
    }
  });

  test("API: evidence bundle + PDF inline for QA doc", async ({ request }) => {
    const report = loadReport();
    test.skip(!report, "Missing QA report");
    const token = await reviewerToken(request);
    test.skip(!token, "Reviewer credentials not configured");

    const entry = report.indicators["kra4-a-member:approve"];
    test.skip(!entry?.documentId, "Missing kra4-a-member QA document");

    const bundleRes = await request.get(
      `${API}/api/reviewer/documents/${entry.documentId}/kra4/evidence-bundle`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    expect(bundleRes.ok()).toBeTruthy();
    const payload = await bundleRes.json();
    const bundle = payload.bundle || payload.kra4EvidenceBundle || payload;
    expect(
      payload.indicatorId ||
        bundle.indicatorId ||
        payload.indicator?.id ||
        (payload.requiredEvidenceSlots || bundle.requiredEvidenceSlots || []).length
    ).toBeTruthy();

    const fileRes = await request.get(`${API}/api/reviewer/documents/${entry.documentId}/file?disposition=inline`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(fileRes.status()).toBe(200);
    const ctype = (fileRes.headers()["content-type"] || "").toLowerCase();
    expect(ctype).not.toContain("text/html");
  });

  test("Browser: open KRA IV document review workspace", async ({ page, request }) => {
    const report = loadReport();
    test.skip(!report, "Missing QA report");
    const token = await reviewerToken(request);
    test.skip(!token, "Set QA_REVIEWER_EMAIL + QA_REVIEWER_PASSWORD");

    const entry = report.indicators["kra4-a-member:approve"];
    test.skip(!entry?.documentId, "Missing QA document");

    const loginRes = await request.post(`${API}/api/auth/login`, {
      data: {
        email: process.env.QA_REVIEWER_EMAIL,
        password: process.env.QA_REVIEWER_PASSWORD,
        client: "web",
      },
    });
    const auth = await loginRes.json();
    const apiBase = API.replace(/\/$/, "");
    await page.addInitScript((payload) => {
      window.FL_API_BASE = payload.apiBase;
      sessionStorage.setItem("facultylink.accessToken", payload.accessToken);
      if (payload.refreshToken) sessionStorage.setItem("facultylink.refreshToken", payload.refreshToken);
      if (payload.user) sessionStorage.setItem("facultylink.user", JSON.stringify(payload.user));
      if (payload.session) sessionStorage.setItem("facultylink.session", JSON.stringify(payload.session));
    }, {
      apiBase,
      accessToken: auth.accessToken || auth.access_token || token,
      refreshToken: auth.refreshToken || auth.refresh_token,
      user: auth.user,
      session: auth.session,
    });

    const docUrl = `${WEB}/pages/reviewer/document-review.html?documentId=${encodeURIComponent(entry.documentId)}`;
    await page.goto(docUrl);
    await expect(page.locator("body")).toContainText(/KRA IV|Professional Development|Evidence/i, { timeout: 25000 });
    await page.screenshot({ path: path.join(SHOT_DIR, "kra4-document-review.png"), fullPage: true });
  });
});
