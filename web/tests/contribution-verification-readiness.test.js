"use strict";

/**
 * Criterion B contribution confirmation readiness row (co-author).
 * Run: node web/tests/contribution-verification-readiness.test.js
 */

var fs = require("fs");
var path = require("path");
var global = globalThis;
global.window = global;
global.FL = global.FL || {};

eval(fs.readFileSync(path.join(__dirname, "../js/criterion-b-workspace-ui.js"), "utf8"));

var state = {
  items: [],
  bundle: { authorship: "co", materialType: "textbook" },
  contributionVerification: {
    confirmationStatus: "not_confirmed",
    recordedContributionPercent: 50,
    matchStatusLabel: "Not Confirmed"
  },
  specializationAligned: true
};
var rows = FL.criterionBWorkspaceUi.buildReviewReadinessRows(state);
var contrib = rows.find(function (r) { return r.label.indexOf("Annex C") >= 0; });
if (!contrib || contrib.ok) throw new Error("Expected contribution row to block scoring");
state.contributionVerification.confirmationStatus = "confirmed";
var rows2 = FL.criterionBWorkspaceUi.buildReviewReadinessRows(state);
var okRow = rows2.find(function (r) { return r.label.indexOf("Annex C") >= 0; });
if (!okRow || !okRow.ok) throw new Error("Expected confirmed contribution to pass readiness");
console.log("contribution-verification-readiness.test.js: all passed");
