"use strict";

var fs = require("fs");
var path = require("path");

var html = fs.readFileSync(path.join(__dirname, "../pages/admin/documents.html"), "utf8");
var assert = function (cond, msg) {
  if (!cond) throw new Error(msg || "Assertion failed");
};

var required = [
  "kra2-evidence.js",
  "kra2-a-workspace-ui.js",
  "reviewer-nav.js",
  "reviewer-accomplishment-state.js",
  "kra34-workspace-metadata.js"
];

required.forEach(function (file) {
  assert(html.indexOf(file) !== -1, "admin documents.html must load " + file);
});

var kra2Idx = html.indexOf("kra2-evidence.js");
var kra2ReviewIdx = html.indexOf("kra2-a-review.js");
assert(kra2Idx !== -1 && kra2Idx < kra2ReviewIdx, "kra2-evidence.js must load before kra2-a-review.js");

console.log("admin-evidence-workspace-scripts.test.js: all passed");
