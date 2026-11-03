/**
 * Phase C7 — scoring configuration loader unit checks (Node).
 * Run: node web/tests/scoring-configuration.test.js
 */
/* eslint-disable no-console */
"use strict";

global.window = global;
global.FL = {
  store: {
    usesLiveReviewerApi: function () { return true; },
    usesRealAdminApi: function () { return false; }
  },
  esc: function (s) { return String(s); },
  apiClient: {
    adminRequest: function () {
      return Promise.reject(new Error("network"));
    }
  },
  rules: { applySettings: function () {} },
  criterionCWorkspaceUi: {
    RESEARCH_TYPE_LABELS: { sp_cp: "SP/CP", ut: "UT", mt: "MT", dd: "DD" }
  }
};

require("../js/scoring-configuration.js");

const sc = FL.scoringConfiguration;
let failed = 0;

function assert(cond, msg) {
  if (!cond) {
    console.error("FAIL:", msg);
    failed += 1;
  }
}

const fixture = {
  configuration: { id: 3, guidelineLabel: "JC 01" },
  kraSettings: {
    criteria: { "kra1-c": { maxPoints: 10 } },
    indicators: { "kra1-c-adviser-ut": { points: 5 } }
  },
  metadata: { version: 2, effectiveFrom: "2023-08-01", provenance: "applicable_as_of" }
};

const norm = sc.normalizePayload(fixture, "applicable");
assert(norm.configuration.id === 3, "normalize applicable configuration");
assert(sc.indicatorPoints("kra1-c-adviser-ut", norm.kraSettings) === 5, "indicator points");
assert(sc.criterionCMax(norm.kraSettings) === 10, "criterion C cap");
assert(sc.criterionCIndicatorsComplete(norm.kraSettings) === false, "incomplete indicators flagged");

const reviewerShape = sc.normalizePayload({
  published: { id: 1, metadata: { version: 1 } },
  kraSettings: { criteria: {} },
  metadata: { version: 1 }
}, "reviewer");
assert(reviewerShape.configuration.id === 1, "normalize reviewer route");

const locked = sc.lockedSnapshotLabel({ version: 4, effectiveFrom: "2024-01-01", provenance: "explicit_id" });
assert(locked.indexOf("v4") >= 0, "locked snapshot label");

if (failed) {
  console.error(failed + " test(s) failed");
  process.exit(1);
}
console.log("scoring-configuration.test.js: all checks passed");
