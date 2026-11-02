"use strict";

var fs = require("fs");
var path = require("path");
var vm = require("vm");

var assert = function (cond, msg) {
  if (!cond) throw new Error(msg || "Assertion failed");
};

var dataSrc = fs.readFileSync(path.join(__dirname, "../js/data.js"), "utf8");
var ctx = { window: {}, FL: {} };
ctx.window.FL = ctx.FL;
vm.createContext(ctx);
vm.runInContext(dataSrc, ctx);

var metrics = ctx.FL.store.facultyEvidenceMetricsFromDocs([
  {
    id: "doc-1",
    status: "pending-review",
    setSefParentContext: {
      allChildValidationSummary: { total: 12, validated: 12, pending: 0, incomplete: 0, needsRevision: 0 }
    }
  }
]);

assert(metrics.sourcePdfTotal === 1, "one source PDF");
assert(metrics.sourcePdfPendingWorkflow === 1, "PDF workflow still pending");
assert(metrics.evaluationRecordsValidated === 12, "12 validated semesters");
assert(metrics.semesterEvaluationsPending === 0, "0 semester pending");

var dirSrc = fs.readFileSync(path.join(__dirname, "../js/evidence-workspace.js"), "utf8");
assert(dirSrc.indexOf("Semester evaluations") !== -1, "directory separates semester column");
assert(dirSrc.indexOf("PDF document review") !== -1, "directory separates PDF review column");
assert(dirSrc.indexOf("refreshCountsAfterReview") !== -1, "post-validation refresh hook");

console.log("faculty-evidence-metrics.test.js: all passed");
