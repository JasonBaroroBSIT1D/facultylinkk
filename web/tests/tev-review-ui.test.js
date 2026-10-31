/**
 * Synthetic tests for FL.tevReviewUi (run: node web/tests/tev-review-ui.test.js)
 */
"use strict";

var fs = require("fs");
var path = require("path");
var global = globalThis;
eval(fs.readFileSync(path.join(__dirname, "../js/tev-review-ui.js"), "utf8"));

var ui = global.FL.tevReviewUi;
var assert = function (cond, msg) {
  if (!cond) throw new Error(msg || "Assertion failed");
};

(function testStatusLabels() {
  assert(ui.statusLabel({ reviewerValidationStatus: "pending-review" }) === "Pending Review");
  assert(ui.statusLabel({ reviewerValidationStatus: "approved" }) === "Validated");
  assert(ui.statusLabel({ reviewerValidationStatus: "revision" }) === "Needs Revision");
  assert(ui.statusLabel({ incompleteExtraction: true }) === "Incomplete Extraction");
})();

(function testSummaryCounts() {
  var list = [
    { evaluationType: "SET", reviewerValidationStatus: "approved" },
    { evaluationType: "SEF", reviewerValidationStatus: "pending-review" },
    { evaluationType: "SET", reviewerValidationStatus: "revision" }
  ];
  var c = ui.summaryCounts(list);
  assert(c.total === 3);
  assert(c.pending === 1);
  assert(c.needsRevision === 1);
})();

(function testFilters() {
  var tev = { evaluationType: "SET", reviewerValidationStatus: "pending-review" };
  assert(ui.passesFilter(tev, "set"));
  assert(!ui.passesFilter(tev, "sef"));
  assert(ui.passesFilter(tev, "pending"));
  assert(!ui.passesFilter(tev, "reviewed"));
})();

console.log("tev-review-ui.test.js: all passed");
