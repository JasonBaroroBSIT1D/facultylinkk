"use strict";

var fs = require("fs");
var path = require("path");

function assert(cond, msg) {
  if (!cond) throw new Error(msg || "Assertion failed");
}

var ui = fs.readFileSync(path.join(__dirname, "../js/ui.js"), "utf8");
var evidence = fs.readFileSync(path.join(__dirname, "../js/evidence-workspace.js"), "utf8");

assert(ui.indexOf("tableDateTimeHtml") !== -1, "tableDateTimeHtml helper");
assert(evidence.indexOf("FL.ui.tableDateTimeHtml(row.lastActivity)") !== -1, "directory uses table datetime");
assert(evidence.indexOf("portal-data-table") !== -1, "evidence tables use portal-data-table class");

var css = fs.readFileSync(path.join(__dirname, "../css/portal-page.css"), "utf8");
assert(css.indexOf(".fl-table-datetime") !== -1, "datetime styles");

console.log("portal-table-datetime.test.js: all passed");
