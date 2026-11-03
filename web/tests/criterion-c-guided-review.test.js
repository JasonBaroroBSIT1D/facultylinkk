"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("fs");
const path = require("path");
const vm = require("vm");

function loadModules() {
  const root = path.join(__dirname, "..", "js");
  const ctx = { window: {}, console };
  ctx.window.FL = {
    esc: function (s) {
      return String(s || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;");
    },
    ui: {
      statusBadge: function (k) {
        return "[" + k + "]";
      },
      empty: function (t, m) {
        return t + ":" + m;
      }
    },
    documents: {
      kvRow: function (label, value) {
        return "<div class=\"kv\"><dt>" + label + "</dt><dd>" + value + "</dd></div>";
      },
      ocrStatusLabel: function () {
        return "completed";
      }
    },
    store: { documentById: function () { return null; } }
  };
  ctx.FL = ctx.window.FL;
  vm.createContext(ctx);
  vm.runInContext(fs.readFileSync(path.join(root, "criterion-c-workspace-ui.js"), "utf8"), ctx);
  vm.runInContext(fs.readFileSync(path.join(root, "criterion-c-review.js"), "utf8"), ctx);
  return ctx.window.FL;
}

test("review steps banner lists three guided steps", () => {
  const FL = loadModules();
  const html = FL.criterionCWorkspaceUi.reviewStepsBanner("evidence");
  assert.match(html, /Accomplishment details/);
  assert.match(html, /Supporting evidence/);
  assert.match(html, /Final assessment/);
  assert.match(html, /is-active/);
});

test("research details card prefills student names from OCR", () => {
  const FL = loadModules();
  const html = FL.criterionCWorkspaceUi.researchDetailsCardHtml({
    bundle: { serviceCategory: "research", studentNames: "" },
    canDecide: true,
    ocrStatus: "completed",
    payload: {
      ocrReviewFlags: ["student_names_ocr_needs_review"],
      ocrExtraction: {
        fields: {
          studentNames: { value: "Lee, Kim", confidence: "medium", status: "needs_review" }
        },
        structured: { students: ["Lee, Kim"], advisers: [], panelMembers: [] }
      }
    },
    ocrExtraction: {
      fields: {
        studentNames: { value: "Lee, Kim", confidence: "medium", status: "needs_review" }
      },
      structured: { students: ["Lee, Kim"], advisers: [], panelMembers: [] }
    },
    ocrReviewFlags: ["student_names_ocr_needs_review"]
  });
  assert.match(html, /id="cc-reviewer-student-names"/);
  assert.match(html, /Lee, Kim/);
  assert.match(html, /cc-inline-warn/);
  assert.match(html, /View OCR details/);
  assert.match(html, /id="cc-reviewer-academic-year"/);
  assert.match(html, /Save details/);
});

test("compact review page merges layout into single flow", () => {
  const FL = loadModules();
  const html = FL.criterionCWorkspaceUi.compactReviewPageHtml({
    facultyName: "Jason Baroro",
    backHref: "#",
    backLabel: "Back",
    canDecide: true,
    showGroupEditor: false,
    bundle: {
      projectTitle: "AI-Assisted Campus Help Desk",
      serviceCategory: "research",
      researchType: "sp_cp",
      role: "adviser",
      studentNames: ""
    },
    doc: { indicatorId: "kra1-c-adviser-sp" },
    payload: { ocrExtraction: { fields: {} }, ocrReviewFlags: [] },
    evidenceItems: [
      {
        slotId: "approval_sheet",
        label: "Signed approval sheet",
        status: "verified",
        entry: { documentId: "d1" },
        fileDoc: { fileUrl: "/f" }
      }
    ],
    validation: { readyForReviewer: false, blockers: ["Student name(s) are required."], flags: [] },
    scoring: { estimatedPoints: 3 },
    remarks: "",
    assessedPoints: "3"
  });
  assert.match(html, /AI-Assisted Campus Help Desk/);
  assert.match(html, /Research details/);
  assert.match(html, /Evidence checklist/);
  assert.match(html, /Review decision/);
  assert.doesNotMatch(html, /Accomplishment details/);
  assert.doesNotMatch(html, /cb-review-steps/);
});

test("approval gate exposes first blocker beside approve control", () => {
  const FL = loadModules();
  const gate = FL.criterionCWorkspaceUi.reviewApprovalGate(
    { readyForReviewer: false, blockers: ["Student name(s) are required for research-related services."], flags: [] },
    true
  );
  assert.equal(gate.canApprove, false);
  assert.match(gate.blockerHint, /Student name/);
});

test("approval gate respects blockers and policy flags", () => {
  const FL = loadModules();
  const ui = FL.criterionCWorkspaceUi;
  assert.equal(
    ui.reviewApprovalGate({ readyForReviewer: true, blockers: [], flags: [] }, true).canApprove,
    true
  );
  assert.equal(
    ui.reviewApprovalGate(
      { readyForReviewer: true, blockers: ["Missing verification"], flags: [] },
      true
    ).canApprove,
    false
  );
  assert.equal(
    ui.reviewApprovalGate(
      { readyForReviewer: true, blockers: [], flags: ["adviser_panel_same_thesis_review"] },
      true
    ).policyBlock,
    true
  );
});

test("validation messages humanize flags", () => {
  const FL = loadModules();
  const msgs = FL.criterionCWorkspaceUi.validationMessagesHtml({
    flags: ["duplicate_service_suspected"],
    blockers: ["All evidence must be verified"]
  });
  assert.match(msgs.flagHtml, /duplicate/i);
  assert.match(msgs.blockerHtml, /verified/);
  assert.equal(msgs.hasBlockers, true);
});

test("compact page disables approve and shows blocker hint", () => {
  const FL = loadModules();
  const html = FL.criterionCWorkspaceUi.compactReviewPageHtml({
    facultyName: "Faculty",
    backHref: "#",
    backLabel: "Back",
    canDecide: true,
    bundle: { projectTitle: "T", serviceCategory: "research", role: "adviser", researchType: "sp_cp" },
    doc: { indicatorId: "kra1-c-adviser-sp" },
    payload: {},
    evidenceItems: [],
    validation: { readyForReviewer: false, blockers: ["Student name(s) are required."], flags: [] },
    scoring: { estimatedPoints: 3 },
    remarks: "",
    assessedPoints: "3"
  });
  assert.match(html, /id="cc-approve" disabled/);
  assert.match(html, /Student name/);
  assert.match(html, /cc-approve-blocker/);
});
