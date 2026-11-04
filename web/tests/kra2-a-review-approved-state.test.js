"use strict";

var fs = require("fs");
var path = require("path");
var vm = require("vm");

var root = path.join(__dirname, "..", "js");

var ctx = {
  window: {},
  FL: {
    esc: function (s) {
      return String(s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/"/g, "&quot;");
    },
    documents: {
      kvRow: function (label, value) {
        return "<dt>" + label + "</dt><dd>" + value + "</dd>";
      }
    }
  },
  document: { getElementById: function () { return null; } },
  console: console
};
ctx.window.FL = ctx.FL;

vm.runInContext(fs.readFileSync(path.join(root, "kra2-a-workspace-ui.js"), "utf8"), vm.createContext(ctx));

var ui = ctx.FL.kra2AWorkspaceUi;

function assert(cond, msg) {
  if (!cond) throw new Error(msg || "assertion failed");
}

assert(ui.normalizeReviewStatus({ bundle: { reviewStatus: "approved" } }) === "approved", "bundle reviewStatus");
assert(
  ui.normalizeReviewStatus({
    bundle: { reviewerAssessment: { reviewStatus: "approved" } }
  }) === "approved",
  "reviewerAssessment reviewStatus"
);

var pendingState = {
  canDecide: true,
  bundle: { reviewStatus: "pending", submittedForReviewAt: "2026-01-01" },
  validation: { reviewStatus: "pending", approvalBlockers: ["Verify slot"] },
  scoring: { systemCalculatedPoints: 2, allowsPointAdjustment: false },
  remarks: "Pending review remarks here",
  doc: { criterionId: "kra3-a", id: "doc-1" },
  payload: { scoringVersion: 5 }
};

var pendingHtml = ui.decisionSectionHtml(pendingState);
assert(pendingHtml.indexOf('id="kra2-approve"') >= 0, "pending shows approve");
assert(pendingHtml.indexOf('id="kra2-save-assessment"') >= 0, "pending shows save assessment");
assert(pendingHtml.indexOf("System-calculated eligible points") >= 0, "system eligible label");
assert(pendingHtml.indexOf("Ready to approve") === -1, "hint rendered separately");

var adjustablePending = Object.assign({}, pendingState, {
  scoring: {
    systemCalculatedPoints: 4,
    allowsPointAdjustment: true,
    reviewerAssessedPoints: 4,
    scoreAdjustmentReason: ""
  }
});
var adjustableHtml = ui.decisionSectionHtml(adjustablePending);
assert(adjustableHtml.indexOf('id="kra2-assessed-points"') >= 0, "editable assessed points");

var approvedState = {
  canDecide: true,
  reassessmentCapabilities: {
    canRequestReassessment: true,
    canFinalizeReassessment: false,
    actionLabel: "Request Reassessment",
    requiresAdministratorToFinalize: true
  },
  bundle: {
    reviewStatus: "approved",
    reviewerRemarks: "KRA3 QA approval kra3-a-income automated",
    reviewerAssessment: {
      reviewStatus: "approved",
      assessedPoints: 2,
      approvedPoints: 2,
      remarks: "KRA3 QA approval kra3-a-income automated",
      assessedAt: "2026-11-04T06:00:00Z",
      reviewerDisplayName: "QA Reviewer"
    },
    submittedForReviewAt: "2026-01-01"
  },
  validation: { reviewStatus: "pending", readyForApproval: true },
  scoring: {
    systemCalculatedPoints: 2,
    reviewerAssessedPoints: 2,
    scoringConfigurationVersion: 5
  },
  remarks: "KRA3 QA approval kra3-a-income automated",
  doc: { criterionId: "kra3-a", id: "doc-1" },
  payload: { scoringVersion: 5 }
};

var approvedHtml = ui.decisionSectionHtml(approvedState);
assert(approvedHtml.indexOf('id="kra2-approve"') === -1, "approved hides approve");
assert(approvedHtml.indexOf('id="kra2-reject"') === -1, "approved hides reject");
assert(approvedHtml.indexOf('id="kra2-save-assessment"') >= 0, "approved keeps save assessment");
assert(approvedHtml.indexOf('id="kra2-assessed-points"') >= 0, "approved keeps assessed points field");
assert(approvedHtml.indexOf("Current approved points") >= 0, "shows approved points");
assert(approvedHtml.indexOf("KRA3 QA approval") >= 0, "shows remarks");
assert(approvedHtml.indexOf('id="kra2-start-reassessment"') >= 0, "shows reassessment action");
assert(approvedHtml.indexOf("Request Reassessment") >= 0, "reassessment label");
assert(
  approvedHtml.indexOf("do not change approved points") >= 0,
  "explains finalized score protection"
);
assert(ui.computeApprovalBlockers(approvedState, "").length === 0, "no blockers when approved");

var evidenceHtml = ui.evidenceCardsHtml(
  Object.assign({}, approvedState, {
    evidenceItems: [
      {
        slotId: "primary_output",
        label: "Primary",
        fileName: "a.pdf",
        documentId: "doc-1",
        status: "verified"
      }
    ]
  })
);
assert(evidenceHtml.indexOf("kra2-slot-") === -1, "no slot editor when approved");

var rejectedState = {
  canDecide: true,
  bundle: {
    reviewStatus: "rejected",
    reviewerRemarks: "Please upload signed attendance sheet.",
    submittedForReviewAt: "2026-01-01"
  },
  validation: { reviewStatus: "rejected" },
  scoring: { systemCalculatedPoints: 4 },
  doc: { criterionId: "kra3-b", id: "doc-2" }
};
var rejectedHtml = ui.decisionSectionHtml(rejectedState);
assert(rejectedHtml.indexOf('id="kra2-approve"') === -1, "rejected hides approve");
assert(rejectedHtml.indexOf('id="kra2-save-assessment"') >= 0, "rejected keeps save assessment");
assert(rejectedHtml.indexOf("Rejected") >= 0, "rejected status label");

console.log("kra2-a-review-approved-state.test.js: all passed");
