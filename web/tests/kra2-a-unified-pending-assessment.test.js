"use strict";

var fs = require("fs");
var path = require("path");
var vm = require("vm");
var test = require("node:test");
var assert = require("node:assert/strict");

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

test("unified pending assessment shows readonly assessed points for fixed scoring", function () {
  var state = {
    canDecide: true,
    remarks: "",
    doc: { criterionId: "kra3-b", indicatorId: "kra3-b-train-local" },
    bundle: {
      submittedForReviewAt: "2026-01-01T00:00:00Z",
      reviewStatus: "pending",
      reviewerAssessment: { reviewStatus: "pending" }
    },
    scoring: {
      systemCalculatedPoints: 2,
      eligiblePoints: 2,
      allowsPointAdjustment: false,
      numericScoringBlocked: false,
      reviewerAssessedPoints: null
    },
    validation: { approvalBlockers: ["Verify supporting evidence: Training certificate."] },
    payload: { slotLabels: { cert: "Training certificate" } }
  };
  var html = ui.decisionSectionHtml(state);
  assert.match(html, /id="kra2-assessed-points"/);
  assert.match(html, /id="kra2-assessed-points"/);
  assert.doesNotMatch(html, /readonly="readonly"/);
  assert.match(html, /id="kra2-save-assessment"/);
  assert.match(html, /id="kra2-remarks"/);
  assert.match(html, /id="kra2-score-adjustment-reason"/);
  assert.match(html, /System-calculated eligible points/);
});

test("criterion D pending shows numeric scoring blocker banner", function () {
  var state = {
    canDecide: true,
    remarks: "",
    doc: { criterionId: "kra3-d", indicatorId: "kra3-d-dean" },
    bundle: {
      submittedForReviewAt: "2026-01-01T00:00:00Z",
      reviewStatus: "pending"
    },
    scoring: {
      systemCalculatedPoints: null,
      eligiblePoints: null,
      allowsPointAdjustment: false,
      numericScoringBlocked: true,
      numericScoringBlockerMessage: "Designation points unverified."
    },
    validation: { reviewerBlockers: ["Designation points unverified."] },
    payload: {}
  };
  var html = ui.decisionSectionHtml(state);
  assert.match(html, /kra2-scoring-blocker-banner/);
  assert.match(html, /Designation points unverified/);
  assert.match(html, /id="kra2-save-assessment"/);
});
