"use strict";

var fs = require("fs");
var path = require("path");
var global = globalThis;
global.window = global;
global.FL = {
  store: { documents: [] },
  rules: { findIndicator: function () { return null; }, classification: [] }
};

eval(fs.readFileSync(path.join(__dirname, "../js/validation.js"), "utf8"));

var assert = function (cond, msg) {
  if (!cond) throw new Error(msg || "Assertion failed");
};

function baseParent(overrides) {
  return Object.assign({
    id: "doc-1",
    criterionId: "kra1-a",
    indicatorId: "kra1-a-teaching-evidence",
    status: "pending-review",
    documentWorkflowStatus: "pending-review",
    ocr: { status: "completed" },
    extractedInfo: {},
    setSefParentContext: {
      allChildValidationSummary: {
        total: 12,
        validated: 12,
        pending: 0,
        incomplete: 0,
        needsRevision: 0,
        rejected: 0
      }
    },
    teachingEvaluationSummary: {
      count: 12,
      childValidationSummary: {
        total: 12,
        validated: 12,
        pending: 0
      }
    }
  }, overrides || {});
}

(function testTwelveOfTwelveValidatedPendingPdf() {
  var doc = baseParent({});
  var v = FL.validation.evaluate(doc);
  assert(v.setSefParent === true);
  assert(v.overall === "valid");
  assert(v.semesterEvaluationsComplete === true);
  assert(v.pdfWorkflowPending === true);
  assert(v.evidenceStatus === "complete");
  assert(v.classification.status === "classified");
})();

(function testIncompleteSemestersBlock() {
  var doc = baseParent({
    setSefParentContext: {
      allChildValidationSummary: { total: 12, validated: 6, pending: 6, incomplete: 0, needsRevision: 0, rejected: 0 }
    }
  });
  var v = FL.validation.evaluate(doc);
  assert(v.overall === "reviewer-required");
})();

(function testNameMismatchBlocks() {
  var doc = baseParent({
    documentInformation: { nameVerificationLabel: "Name Mismatch" }
  });
  var v = FL.validation.evaluate(doc);
  assert(v.overall === "invalid" || v.overall === "reviewer-required");
})();

(function testApprovalGateSemestersComplete() {
  var doc = baseParent({});
  var gate = FL.validation.approvalGate(doc);
  assert(gate.ok === true);
})();

console.log("validation-set-sef-parent.test.js: all passed");
