"use strict";

var fs = require("fs");
var path = require("path");
var vm = require("vm");

var root = path.join(__dirname, "..", "js");
var ctx = {
  window: {},
  FL: {
    esc: function (s) {
      return String(s);
    },
    documents: { kvRow: function () { return ""; } },
    kra2AWorkspaceUi: {}
  }
};
ctx.window.FL = ctx.FL;
vm.runInContext(fs.readFileSync(path.join(root, "kra2-a-workspace-ui.js"), "utf8"), vm.createContext(ctx));

var ui = ctx.FL.kra2AWorkspaceUi;

function decisionHtml(scoring) {
  return ui.decisionSectionHtml({
    canDecide: true,
    bundle: {},
    validation: {},
    scoring: scoring,
    doc: { indicatorId: scoring.indicatorId }
  });
}

var fixedHtml = decisionHtml({
  indicatorId: "kra2-a-book-sole",
  scoringMethod: "fixed",
  scoringMethodLabel: "Fixed",
  allowsPointAdjustment: false,
  systemCalculatedPoints: 100,
  indicatorMaxPoints: 100,
  estimatedPoints: 100,
  adjustmentGoverningRule: "Official fixed points."
});
if (fixedHtml.indexOf('type="hidden"') < 0 || fixedHtml.indexOf("Fixed scoring") < 0) {
  throw new Error("fixed indicator should use read-only assessed points");
}
if (fixedHtml.indexOf('type="number"') >= 0 && fixedHtml.indexOf("kra2-assessed-points") >= 0) {
  var numIdx = fixedHtml.indexOf('type="number"');
  var hiddenIdx = fixedHtml.indexOf('type="hidden"');
  if (numIdx >= 0 && hiddenIdx < 0) throw new Error("fixed should not expose number assessed input");
}

var variableHtml = decisionHtml({
  indicatorId: "kra2-a-journal-sole",
  scoringMethod: "variable",
  scoringMethodLabel: "Variable",
  allowsPointAdjustment: true,
  systemCalculatedPoints: 50,
  indicatorMaxPoints: 50,
  maxAssessedPoints: 50,
  adjustmentGoverningRule: "Journal indexing rules."
});
if (variableHtml.indexOf('id="kra2-assessed-points"') < 0 || variableHtml.indexOf('type="number"') < 0) {
  throw new Error("variable indicator should expose editable assessed points");
}
if (variableHtml.indexOf("Official eligible points") < 0) {
  throw new Error("expected Official eligible points label");
}
if (fixedHtml.indexOf("Reviewer-assessed points") >= 0 && fixedHtml.indexOf("kra2-scoring-readonly") >= 0) {
  throw new Error("fixed scoring must not duplicate assessed points blocks");
}

console.log("kra2-scoring-ui.test.js OK");
