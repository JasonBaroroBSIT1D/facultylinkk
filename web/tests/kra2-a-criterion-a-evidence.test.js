"use strict";

var fs = require("fs");
var path = require("path");
var vm = require("vm");

var rulesSrc = fs.readFileSync(path.join(__dirname, "../js/rules.js"), "utf8");
var uiSrc = fs.readFileSync(path.join(__dirname, "../js/kra2-a-workspace-ui.js"), "utf8");

var ctx = {
  window: {},
  FL: {
    esc: function (s) {
      return String(s);
    },
    documents: { kvRow: function () { return ""; } },
    rules: { kras: [] }
  }
};
ctx.window.FL = ctx.FL;
vm.runInContext(rulesSrc, vm.createContext(ctx));
vm.runInContext(uiSrc, vm.createContext(ctx));

var ui = ctx.FL.kra2AWorkspaceUi;

var slots = ui.requiredSlotIds({}, { requiredEvidenceSlots: ["primary_output", "peer_review_evidence"] });
if (slots.length !== 2 || slots[1] !== "peer_review_evidence") {
  throw new Error("requiredSlotIds must honor API requiredEvidenceSlots");
}

var bookSlots = ui.criterionARequiredSlots("kra2-a-book-sole");
if (!bookSlots || bookSlots.indexOf("peer_review_evidence") < 0) {
  throw new Error("book sole must require peer_review_evidence");
}

var label = ui.indicatorLabel("kra2-a-book-sole", {});
if (label.indexOf("Journal") >= 0) {
  throw new Error("book sole must not show journal fallback label: " + label);
}
if (label.indexOf("book") < 0 && label.indexOf("Book") < 0) {
  throw new Error("expected academic book label, got " + label);
}

var blockers = ui.computeApprovalBlockers(
  {
    canDecide: true,
    remarks: "long enough remarks",
    bundle: { indicatorId: "kra2-a-book-sole" },
    validation: {
      approvalBlockers: ["Verify supporting evidence: Peer review and reputable academic press evidence."],
      checklistSummary: { primary_output: "verified", peer_review_evidence: "reviewer_required" }
    }
  },
  "long enough remarks"
);
if (blockers.length !== 1) {
  throw new Error("duplicate slot blockers must not appear: " + JSON.stringify(blockers));
}

console.log("kra2-a-criterion-a-evidence.test.js OK");
