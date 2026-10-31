"use strict";

var fs = require("fs");
var path = require("path");

var src = fs.readFileSync(path.join(__dirname, "../js/evidence-workspace.js"), "utf8");
var assert = function (cond, msg) {
  if (!cond) throw new Error(msg || "Assertion failed");
};

assert(src.indexOf("refreshTe(") === -1, "refreshTe() call must be removed");
assert(src.indexOf("refreshTeachingEffectiveness") !== -1, "refreshTeachingEffectiveness must exist");
assert(
  src.indexOf("_refreshCriterionATeaching") !== -1,
  "fallback refresh hook must be registered on FL.evidence"
);
assert(src.indexOf("ca-eval-table") !== -1, "teaching evaluations must use table layout");
assert(src.indexOf("openCriterionADocumentReviewDrawer") !== -1, "document attention must open unified modal");
assert(src.indexOf("data-ca-doc-attention") !== -1, "View document must not redirect to full page");
assert(src.indexOf("setCriterionADrawerMode") !== -1, "drawer must support semester vs document modes");
assert(src.indexOf("ca-tev-drawer-actions") !== -1, "single unified action footer required");
assert(src.indexOf("ca-tev-actions-semester") === -1, "legacy duplicate semester action bar must be removed");
assert(src.indexOf("ca-tev-actions-document") === -1, "legacy duplicate document action bar must be removed");
assert(src.indexOf("renderCriterionADrawerActions") !== -1, "dynamic action rendering required");
assert(src.indexOf("skipDrawer") !== -1, "drawer must not duplicate on workspace refresh");
assert(src.indexOf("ca-eval-grid") === -1 || src.indexOf("criterionAEvalTableHtml") !== -1, "card grid replaced by table");
assert(
  src.indexOf("if (state.criterionId === \"kra1-a\"") < src.indexOf("paintCriterionWorkspace"),
  "paintCriterionWorkspace must live inside kra1-a live branch"
);

console.log("evidence-workspace-refresh.test.js: all passed");
