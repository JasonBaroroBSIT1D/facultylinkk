"use strict";

var fs = require("fs");
var path = require("path");

var src = fs.readFileSync(path.join(__dirname, "../js/evidence-workspace.js"), "utf8");
var assert = function (cond, msg) {
  if (!cond) throw new Error(msg || "Assertion failed");
};

assert(src.indexOf("docStatusBucket") !== -1, "docStatusBucket helper required");
assert(src.indexOf("applyDocStatusFilter") !== -1, "applyDocStatusFilter required");
assert(src.indexOf("documentReviewBadge") !== -1, "documentReviewBadge required");
assert(src.indexOf("_filterCounts") !== -1, "filter tab counts from backend");
assert(
  src.indexOf('if (state.docFilter === "pending-review") docs = docs.filter(FL.documents.needsAction)') === -1,
  "must not double-filter pending with needsAction"
);
var facultyJs = fs.readFileSync(path.join(__dirname, "../js/faculty.js"), "utf8");
assert(facultyJs.indexOf("filter=all") !== -1, "faculty navigation links to evidence workspace");

console.log("evidence-doc-status-filter.test.js: all passed");
