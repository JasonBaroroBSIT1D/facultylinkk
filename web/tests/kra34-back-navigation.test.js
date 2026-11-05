"use strict";

var fs = require("fs");
var path = require("path");

var assert = function (cond, msg) {
  if (!cond) throw new Error(msg || "Assertion failed");
};

var documentsSrc = fs.readFileSync(path.join(__dirname, "../js/documents.js"), "utf8");
var evidenceSrc = fs.readFileSync(path.join(__dirname, "../js/evidence-workspace.js"), "utf8");
var reviewSrc = fs.readFileSync(path.join(__dirname, "../js/kra2-a-review.js"), "utf8");

assert(documentsSrc.indexOf("_isKra4Criterion(criterionId)") !== -1, "KRA IV back href branch required");
assert(
  documentsSrc.indexOf("kra34") !== -1 || documentsSrc.indexOf("_isKra3Criterion(criterionId)") !== -1,
  "KRA III/IV criterion back routing required"
);
assert(
  documentsSrc.indexOf('return "documents.html?" + back.toString();') !== -1,
  "explicit documents.html back target required"
);
assert(
  documentsSrc.indexOf('back.set("indicator", indicatorId)') === -1 ||
    documentsSrc.indexOf("if (!isKra34Crit && !isKra2Crit)") !== -1 ||
    documentsSrc.indexOf("kra34") !== -1,
  "KRA III/IV back must omit indicator param"
);

assert(evidenceSrc.indexOf("isKra34CriterionId") !== -1, "KRA III/IV criterion helper required");
assert(
  evidenceSrc.indexOf("isKra34CriterionId(state.criterionId)") !== -1,
  "render must prefer KRA III/IV criterion accomplishment view"
);
assert(evidenceSrc.indexOf('ind.indexOf("kra4-")') !== -1, "kra4 indicator URLs must redirect");
assert(evidenceSrc.indexOf("criterionScrollStorageKey") !== -1, "scroll restore key required");

assert(reviewSrc.indexOf("criterionScrollStorageKey") !== -1, "save scroll before open review");

console.log("kra34-back-navigation.test.js: all passed");
