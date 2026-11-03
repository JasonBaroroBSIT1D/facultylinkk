"use strict";

/**
 * Reviewer readiness: distinct complete-set document vs faculty declaration labels.
 * Run: node web/tests/complete-set-readiness-labels.test.js
 */

var fs = require("fs");
var path = require("path");
var global = globalThis;
global.window = global;
global.FL = global.FL || {};

eval(fs.readFileSync(path.join(__dirname, "../js/criterion-b-workspace-ui.js"), "utf8"));

var state = {
  items: [
    {
      slotId: "complete_set_attestation",
      label: "Complete Set Supporting Document",
      entry: { documentId: "doc_attest", status: "verified" },
      fileDoc: { name: "attestation.pdf" }
    }
  ],
  bundle: {
    materialType: "module",
    completeSetDeclared: false,
    authorship: "sole"
  },
  specializationAligned: true
};

var rows = FL.criterionBWorkspaceUi.buildReviewReadinessRows(state);
var docRow = rows.find(function (r) { return r.slotId === "complete_set_attestation"; });
var facultyRow = rows.find(function (r) { return r.slotId === "faculty_completeness_confirmation"; });

if (!docRow || docRow.label !== "Complete Set Supporting Document") {
  throw new Error("Expected supporting document row label");
}
if (docRow.review !== "Verified") {
  throw new Error("Verified upload must not imply faculty confirmation");
}
if (!facultyRow || facultyRow.label !== "Faculty Completeness Confirmation") {
  throw new Error("Expected faculty confirmation row");
}
if (facultyRow.review !== "Not yet confirmed" || facultyRow.ok) {
  throw new Error("Faculty row should block when not confirmed");
}

state.bundle.completeSetDeclared = true;
var rows2 = FL.criterionBWorkspaceUi.buildReviewReadinessRows(state);
var facultyOk = rows2.find(function (r) { return r.slotId === "faculty_completeness_confirmation"; });
if (!facultyOk || !facultyOk.ok || facultyOk.review !== "Confirmed") {
  throw new Error("Faculty confirmation should show Confirmed when declared");
}

var titles = rows.map(function (r) { return r.label; });
if (titles.filter(function (t) { return t === "Complete set attestation"; }).length) {
  throw new Error("Duplicate legacy title must not appear");
}

console.log("complete-set-readiness-labels.test.js: all passed");
