"use strict";

var fs = require("fs");
var path = require("path");

var src = fs.readFileSync(path.join(__dirname, "../js/evidence-workspace.js"), "utf8");
var css = fs.readFileSync(path.join(__dirname, "../css/evidence-workspace.css"), "utf8");
var assert = function (cond, msg) {
  if (!cond) throw new Error(msg || "Assertion failed");
};

assert(src.indexOf("_paintNavHeader") !== -1, "nav header painter required");
assert(src.indexOf("evidence-nav-header") !== -1, "nav header markup required");
assert(src.indexOf("evidence-crumb-bar") === -1, "legacy crumb bar must be removed");
assert(src.indexOf("Previous level") === -1, "legacy back label must be removed");
assert(src.indexOf("_crumbParts") !== -1 && src.indexOf("Evidence Workspace") !== -1, "trail must include Evidence Workspace");
assert(src.indexOf("evidence-nav-badge") !== -1, "assigned badge markup required");
assert(src.indexOf('mount(session, { soft: true })') !== -1, "soft navigation must skip loading screen");
assert(css.indexOf(".evidence-nav-header") !== -1, "nav header styles required");

console.log("evidence-nav-header.test.js: all passed");
