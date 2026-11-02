"use strict";

var fs = require("fs");
var path = require("path");
var vm = require("vm");

var rulesSrc = fs.readFileSync(path.join(__dirname, "../js/rules.js"), "utf8");
var ctx = { window: {}, FL: { rules: {} } };
ctx.window.FL = ctx.FL;
vm.createContext(ctx);
vm.runInContext(rulesSrc, ctx);

var label = ctx.FL.rules.criterionUserLabel("kra2-a", "kra2-a");
if (label.indexOf("kra2-a") !== -1) throw new Error("must not expose internal id");
if (!/^Criterion A/.test(label)) throw new Error("expected Criterion A prefix, got: " + label);

var formatted = ctx.FL.rules.formatCriterionLabel(
  "kra1-b",
  "Instructional Materials Development and Academic Programs"
);
if (formatted.indexOf("Criterion B —") !== 0) throw new Error("bad format: " + formatted);

console.log("criterion-user-label.test.js: all passed");
