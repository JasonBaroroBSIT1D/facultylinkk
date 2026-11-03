const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");

function loadUi() {
  const root = path.join(__dirname, "..", "js");
  const ctx = { window: {}, console };
  ctx.window.FL = {
    esc: function (s) {
      return String(s || "");
    },
    documents: {
      kvRow: function (label, value) {
        return "<div class=\"kv\"><dt>" + label + "</dt><dd>" + value + "</dd></div>";
      },
    },
  };
  ctx.FL = ctx.window.FL;
  vm.createContext(ctx);
  vm.runInContext(
    fs.readFileSync(path.join(root, "criterion-c-workspace-ui.js"), "utf8"),
    ctx,
  );
  return ctx.window.FL.criterionCWorkspaceUi;
}

test("rejects filename-like approval sheet headings as titles", () => {
  const ui = loadUi();
  assert.equal(ui.isUnreliableResearchTitle("01 Signed Approval Sheet SAMPLE"), true);
  assert.equal(ui.isUnreliableResearchTitle("IoT Campus Monitoring System"), false);
});

test("displayProjectTitle prefers confirmed bundle title over document name", () => {
  const ui = loadUi();
  const bundle = {
    projectTitle: "Smart Irrigation Controller for Small Farms",
    metadataConfirmed: { projectTitle: true },
  };
  assert.equal(
    ui.displayProjectTitle(bundle),
    "Smart Irrigation Controller for Small Farms",
  );
  assert.equal(
    ui.accomplishmentTitle(bundle, { title: "01 Signed Approval Sheet SAMPLE.pdf" }),
    "Smart Irrigation Controller for Small Farms",
  );
});

test("ocr research panel flags missing fields", () => {
  const ui = loadUi();
  const html = ui.ocrResearchPanelHtml({
    ocrStatus: "completed",
    ocrExtraction: {
      fields: {
        projectTitle: { value: "Sample Thesis", confidence: "high", status: "extracted" },
        studentNames: { value: "", confidence: "none", status: "missing" },
      },
    },
    bundle: { projectTitle: "Sample Thesis" },
  });
  assert.match(html, /OCR-extracted research metadata/);
  assert.match(html, /Missing/);
});

test("metadataConfirmationLabel reflects faculty confirm flags", () => {
  const ui = loadUi();
  assert.match(ui.metadataConfirmationLabel({}), /Not confirmed/);
  assert.match(
    ui.metadataConfirmationLabel({
      metadataConfirmed: {
        projectTitle: true,
        studentNames: true,
        completionDate: true,
      },
      metadataFacultyConfirmedAt: "2026-01-01T00:00:00Z",
    }),
    /Confirmed by faculty/,
  );
});
