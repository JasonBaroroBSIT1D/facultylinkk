"use strict";

var fs = require("fs");
var path = require("path");

var src = fs.readFileSync(path.join(__dirname, "../js/evidence-workspace.js"), "utf8");
var assert = function (cond, msg) {
  if (!cond) throw new Error(msg || "Assertion failed");
};

assert(src.indexOf("isKra2CriterionId") !== -1, "KRA II criterion helper required");
assert(src.indexOf("_stripKra2IndicatorDocRoute") !== -1, "KRA II route normalizer required");
assert(
  src.indexOf("KRA II statistics") === -1,
  "sticky KRA II statistics Loading placeholder must be removed"
);
assert(
  src.indexOf("isKra2CriterionId(state.criterionId)") !== -1,
  "render must prefer KRA II criterion accomplishment view"
);
assert(
  src.indexOf('ind.indexOf("kra2-") === 0') !== -1,
  "legacy kra2 indicator URLs must redirect to criterion view"
);
assert(
  src.indexOf("mountAccomplishmentListInWorkspace") !== -1,
  "KRA II accomplishment list mount must remain"
);

console.log("evidence-workspace-kra2-routing.test.js: all passed");
