"use strict";

var fs = require("fs");
var path = require("path");
var vm = require("vm");

var ctx = { window: {}, FL: { esc: function (s) { return String(s); } }, console: console };
ctx.window.FL = ctx.FL;
vm.runInContext(fs.readFileSync(path.join(__dirname, "../js/kra2-a-workspace-ui.js"), "utf8"), vm.createContext(ctx));

var ui = ctx.FL.kra2AWorkspaceUi;

var merged = ui.mergeValidationMessages({
  userBlockers: [],
  blockers: ["Confirm accomplishment metadata before approving."]
});
if (merged.length !== 1 || merged[0].indexOf("Confirm") < 0) {
  throw new Error("empty userBlockers must not hide blockers: " + JSON.stringify(merged));
}

var state = {
  canDecide: true,
  remarks: "",
  validation: {
    approvalBlockers: ["Confirm accomplishment metadata before approving."],
    checklistSummary: { primary_output: "verified" }
  },
  bundle: {}
};
var blockers = ui.computeApprovalBlockers(state, "goods na sya");
if (blockers.indexOf("Confirm accomplishment metadata before approving.") < 0) {
  throw new Error("expected metadata blocker, got " + JSON.stringify(blockers));
}
if (blockers.indexOf("Enter reviewer remarks") >= 0) {
  throw new Error("remarks should pass");
}

console.log("kra2-approval-blockers.test.js OK");
