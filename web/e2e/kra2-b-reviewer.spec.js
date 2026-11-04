"use strict";

const { test, expect } = require("@playwright/test");
const fs = require("fs");
const path = require("path");

const REPORT = path.join(__dirname, "../../docs/KRA2_CRITERION_B_LIVE_QA_REPORT.json");
const API = process.env.FLASK_API_BASE || "http://127.0.0.1:5000";
const SHOT_DIR = path.join(__dirname, "../../docs/qa-screenshots/kra2-b");

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

test.describe("KRA II Criterion B reviewer web", () => {
  test.beforeAll(() => {
    fs.mkdirSync(SHOT_DIR, { recursive: true });
  });

  test("API: evidence bundle lists all required slots", async ({ request }) => {
    const report = loadReport();
    test.skip(!report, "Run kra2_criterion_b_live_qa.py first");
    const token = await reviewerToken(request);
    test.skip(!token, "Set QA_REVIEWER_EMAIL + QA_REVIEWER_PASSWORD in env or backend/.env");

    const docId = report.families.patent.documentId;
    const res = await request.get(`${API}/api/reviewer/documents/${docId}/kra2/evidence-bundle`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.ok()).toBeTruthy();
    const payload = await res.json();
    const req = payload.requiredEvidenceSlots || [];
    expect(req.length).toBeGreaterThan(0);
    expect(req).toContain("primary_output");
  });

  test("API: preview each family primary/supporting PDF (no login HTML)", async ({ request }) => {
    const report = loadReport();
    test.skip(!report, "Missing QA report");
    const token = await reviewerToken(request);
    test.skip(!token, "Reviewer credentials not configured");

    for (const [family, row] of Object.entries(report.families || {})) {
      if (!row.documentId) continue;
      const res = await request.get(
        `${API}/api/reviewer/documents/${row.documentId}/file?disposition=inline`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      expect(res.status(), `${family} preview`).toBe(200);
      const ctype = (res.headers()["content-type"] || "").toLowerCase();
      expect(ctype).not.toContain("text/html");
    }
  });

  test("UI: login and open KRA II B accomplishment review", async ({ page, request }) => {
    const report = loadReport();
    test.skip(!report, "Missing QA report");
    const email = process.env.QA_REVIEWER_EMAIL;
    const password = process.env.QA_REVIEWER_PASSWORD;
    test.skip(!email || !password, "Reviewer credentials not configured");

    await page.goto("/pages/public/login.html");
    await page.fill('input[type="email"]', email);
    await page.fill('input[type="password"]', password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/dashboard|reviewer|documents/i, { timeout: 15000 }).catch(() => {});

    const docId = report.families.software.documentId || report.families.patent.documentId;
    const facultyId = report.faculty.publicId;
    const url =
      `/pages/reviewer/document-review.html?id=${encodeURIComponent(docId)}` +
      `&faculty=${encodeURIComponent(facultyId)}&kra=kra2&criterion=kra2-b`;
    await page.goto(url);
    await page.waitForTimeout(4000);

    const html = await page.content();
    expect(html.toLowerCase()).not.toContain("sign in to continue");
    await page.screenshot({ path: path.join(SHOT_DIR, "reviewer-document-review.png"), fullPage: true });

    await page.reload();
    await page.waitForTimeout(2000);
    const html2 = await page.content();
    expect(html2.toLowerCase()).not.toContain("sign in to continue");
  });

  test("API: approved QA accomplishments have no approval blockers and persisted points", async ({
    request,
  }) => {
    const report = loadReport();
    test.skip(!report, "Missing QA report");
    const token = await reviewerToken(request);
    test.skip(!token, "Reviewer credentials not configured");

    for (const [family, row] of Object.entries(report.families || {})) {
      if (!row.documentId) continue;
      const res = await request.get(
        `${API}/api/reviewer/documents/${row.documentId}/kra2/evidence-bundle`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      expect(res.ok(), `${family} bundle`).toBeTruthy();
      const body = await res.json();
      const blockers = (body.validation || {}).approvalBlockers || [];
      expect(blockers, `${family} blockers`).toEqual([]);
      const pts =
        body.scoring?.approvedPoints ??
        body.scoring?.assessedPoints ??
        row.approvedPoints;
      expect(Number(pts), `${family} points`).toBeGreaterThan(0);

      const docRes = await request.get(`${API}/api/reviewer/documents/${row.documentId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      expect(docRes.ok()).toBeTruthy();
      const doc = await docRes.json();
      const status = doc.status || doc.document?.status;
      expect(status).toBe("approved");
    }
  });

  test("API: rejected QA accomplishment status persists after reload", async ({ request }) => {
    const report = loadReport();
    test.skip(!report, "Missing QA report");
    const token = await reviewerToken(request);
    test.skip(!token, "Reviewer credentials not configured");
    const rejectDocId = report.edgeCases?.rejectAccomplishmentDocumentId;
    test.skip(!rejectDocId, "Re-run live QA harness to create rejected accomplishment");

    const res = await request.get(`${API}/api/reviewer/documents/${rejectDocId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    const status = body.status || body.document?.status;
    expect(status).toBe("rejected");
    expect(report.edgeCases?.reject_accomplishment_persisted).toBe(true);
  });

  test("API: invalid document id returns 404 (not HTML login page)", async ({ request }) => {
    const token = await reviewerToken(request);
    test.skip(!token, "Reviewer credentials not configured");
    const res = await request.get(`${API}/api/reviewer/documents/doc_invalid000000/file`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.status()).toBe(404);
    const ctype = (res.headers()["content-type"] || "").toLowerCase();
    expect(ctype).not.toContain("text/html");
  });

  test("API: submitted-only accomplishments include QA patent row", async ({ request }) => {
    const report = loadReport();
    test.skip(!report, "Missing QA report");
    const token = await reviewerToken(request);
    test.skip(!token, "Reviewer credentials not configured");

    const facultyId = report.faculty.publicId;
    const res = await request.get(`${API}/api/reviewer/me/faculty/${facultyId}/kra2-b/accomplishments`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    const ids = (body.accomplishments || []).map((r) => r.documentId);
    expect(ids).toContain(report.families.patent.documentId);
  });
});
