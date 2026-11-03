"use strict";

/**
 * Smoke: Reviewer Faculty Detail KRA scores when Criterion B adapter is integrated (staging shape).
 * Run: node web/tests/faculty-kra-criterion-b-integration.test.js
 */

var fs = require("fs");
var path = require("path");
var global = globalThis;
global.window = global;
global.FL = global.FL || {};
FL.pages = FL.pages || {};

eval(fs.readFileSync(path.join(__dirname, "../js/rules.js"), "utf8"));
eval(fs.readFileSync(path.join(__dirname, "../js/scoring.js"), "utf8"));
eval(fs.readFileSync(path.join(__dirname, "../js/faculty.js"), "utf8"));

var assert = function (cond, msg) {
  if (!cond) throw new Error(msg || "Assertion failed");
};

FL.store = FL.store || {
  facultyById: function () {
    return { id: "fac-jason", name: "Jason Baroro", rank: "Instructor I" };
  },
  userById: function () { return null; },
  documents: [],
  estimatedAssessmentByFaculty: {}
};

/** Adapter ON: Criterion B counts toward KRA I (Jason co-author textbook scenario). */
FL.store.estimatedAssessmentByFaculty["fac-jason"] = {
  kraScores: [
    {
      kraId: "kra1",
      label: "Instruction",
      estimatedPoints: 14,
      maxPoints: 100,
      assessed: true,
      criteriaScores: [
        {
          criterionId: "kra1-b",
          name: "Criterion B",
          estimatedPoints: 14,
          maxPoints: 30,
          simulationAdapterEnabled: true
        }
      ]
    }
  ],
  estimatedTotalKraPoints: 14,
  weightedEstimatedScore: 9.8,
  simulation: { weightBand: "Instructor", missingRequirements: [] }
};

(function testKra1CriterionBIntegratedPoints() {
  var sim = FL.faculty.unifiedSimulation("fac-jason");
  assert(sim.live === true);
  assert(sim.aggregate.kras.length === 1);
  var kra1 = sim.aggregate.kras[0];
  assert(kra1.credited === 14, "KRA I credited should be 14");
  var criteria = kra1.criteria || [];
  var rowB = criteria.find(function (c) { return c.name.indexOf("B") !== -1 || c.maxPoints === 30; });
  assert(rowB, "Criterion B row expected");
  assert(rowB.earned === 14, "Criterion B earned should be 14 not preview");
  assert(String(rowB.earned).indexOf("preview") === -1);
  assert(String(rowB.earned).indexOf("Pending integration") === -1);
})();

/** Adapter OFF: preview only — must not show as full KRA credit. */
FL.store.estimatedAssessmentByFaculty["fac-preview"] = {
  kraScores: [
    {
      kraId: "kra1",
      label: "Instruction",
      estimatedPoints: null,
      maxPoints: 100,
      criteriaScores: [
        {
          criterionId: "kra1-b",
          estimatedPoints: null,
          accomplishmentPreviewPoints: 14,
          integrationState: "criterion_b_adapter_disabled",
          maxPoints: 30,
          simulationAdapterEnabled: false
        }
      ]
    }
  ],
  estimatedTotalKraPoints: 0,
  simulation: { missingRequirements: [] }
};

(function testAdapterOffShowsPreviewNotIntegratedTotal() {
  var sim = FL.faculty.unifiedSimulation("fac-preview");
  var kra1 = sim.aggregate.kras[0];
  assert(kra1.credited !== 14 || kra1.credited === null || kra1.credited === "—");
  var rowB = (kra1.criteria || []).find(function (c) {
    return c.earned === "14 (preview)" || String(c.earned).indexOf("preview") !== -1;
  });
  assert(rowB, "Expected preview label for Criterion B when adapter disabled");
})();

console.log("faculty-kra-criterion-b-integration.test.js: all passed");
