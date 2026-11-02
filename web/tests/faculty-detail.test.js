"use strict";

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
  facultyById: function () { return { id: "fac-1", name: "Test Faculty", rank: "Instructor I" }; },
  userById: function () { return null; },
  documents: [],
  estimatedAssessmentByFaculty: {}
};

FL.store.estimatedAssessmentByFaculty["fac-1"] = {
  kraScores: [
    { kraId: "kra1", label: "Instruction", estimatedPoints: 12, maxPoints: 100 }
  ],
  estimatedTotalKraPoints: 12,
  weightedEstimatedScore: 8,
  simulation: { weightBand: "Band A", missingRequirements: [] }
};

(function testLiveSimulationIncludesCriteria() {
  var sim = FL.faculty.unifiedSimulation("fac-1");
  assert(sim.live === true);
  assert(sim.aggregate.kras.length === 1);
  assert(Array.isArray(sim.aggregate.kras[0].criteria));
  sim.aggregate.kras[0].criteria.forEach(function () {});
})();

(function testPaintDetailGuardsCriteriaAccess() {
  var src = fs.readFileSync(path.join(__dirname, "../js/faculty.js"), "utf8");
  assert(src.indexOf("(kra.criteria || [])") !== -1, "_paintDetail must guard kra.criteria");
  assert(src.indexOf("loadUnifiedAssessmentWithTimeout") !== -1, "assessment load must support timeout");
})();

console.log("faculty-detail.test.js: all passed");
