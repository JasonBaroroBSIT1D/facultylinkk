"use strict";

var fs = require("fs");
var path = require("path");

var src = fs.readFileSync(path.join(__dirname, "../js/evidence-workspace.js"), "utf8");
var css = fs.readFileSync(path.join(__dirname, "../css/evidence-workspace.css"), "utf8");

function assert(cond, msg) {
  if (!cond) throw new Error(msg || "Assertion failed");
}

assert(src.indexOf("_paintReviewerStatsOverview") !== -1, "reviewer overview painter must exist");
assert(src.indexOf("Evidence Overview") !== -1, "section heading required");
assert(src.indexOf("Assigned Faculty") !== -1, "primary card label");
assert(src.indexOf("SET/SEF Pending") !== -1, "secondary SET/SEF pending label");
assert(src.indexOf("evidence-overview-primary") !== -1, "primary grid wrapper");
assert(src.indexOf("evidence-overview-secondary") !== -1, "secondary row wrapper");
assert(
  src.indexOf("if (!isAdmin)") !== -1 && src.indexOf("_paintReviewerStatsOverview(stats)") !== -1,
  "reviewer-only branch must use overview layout"
);
assert(css.indexOf("grid-template-columns: repeat(4, minmax(0, 1fr))") !== -1, "desktop 4-column grid");
assert(css.indexOf("max-width: 1024px") !== -1, "tablet breakpoint");

console.log("evidence-reviewer-overview-stats.test.js: all passed");
