"use strict";

const { test, expect } = require("@playwright/test");
const fs = require("fs");
const path = require("path");

const REPORT = path.join(__dirname, "../../docs/KRA3_LIVE_QA_REPORT.json");
const API = process.env.FLASK_API_BASE || "http://127.0.0.1:5000";
const SHOT_DIR = path.join(__dirname, "../../docs/qa-screenshots/kra3");

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

test.describe("KRA III reviewer web", () => {
  test.beforeAll(() => {
    fs.mkdirSync(SHOT_DIR, { recursive: true });
  });

  test("API: KRA III evidence bundle + criterion lists", async ({ request }) => {
    const report = loadReport();
    test.skip(!report, "Run backend/scripts/kra3_live_qa.py with FACULTYLINK_KRA3_QA_RUN=1 first");
    const token = await reviewerToken(request);
    test.skip(!token, "Set QA_REVIEWER_EMAIL + QA_REVIEWER_PASSWORD");

    const linkage = report.indicators["kra3-a-linkage"];
    test.skip(!linkage?.documentId, "Missing linkage QA document");

    const bundleRes = await request.get(
      `${API}/api/reviewer/documents/${linkage.documentId}/kra3/evidence-bundle`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    expect(bundleRes.ok()).toBeTruthy();
    const payload = await bundleRes.json();
    expect((payload.requiredEvidenceSlots || []).length).toBeGreaterThan(0);

    const facultyId = report.facultyPublicId;
    for (const crit of ["kra3-a", "kra3-b", "kra3-c", "kra3-d"]) {
      const sumRes = await request.get(
        `${API}/api/reviewer/me/faculty/${facultyId}/${crit}/summary`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      expect(sumRes.ok(), crit).toBeTruthy();
      const accRes = await request.get(
        `${API}/api/reviewer/me/faculty/${facultyId}/${crit}/accomplishments`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      expect(accRes.ok(), crit).toBeTruthy();
    }
  });

  test("API: inline PDF preview for QA accomplishment", async ({ request }) => {
    const report = loadReport();
    test.skip(!report, "Missing QA report");
    const token = await reviewerToken(request);
    test.skip(!token, "Reviewer credentials not configured");

    const docId = report.indicators["kra3-a-linkage"]?.documentId;
    test.skip(!docId, "No QA document");
    const res = await request.get(`${API}/api/reviewer/documents/${docId}/file?disposition=inline`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.status()).toBe(200);
    const ctype = (res.headers()["content-type"] || "").toLowerCase();
    expect(ctype).not.toContain("text/html");
  });
});
