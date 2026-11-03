var fs = require("fs");
var path = require("path");
var vm = require("vm");

var root = path.join(__dirname, "..", "js");
var ctx = { window: {}, FL: {}, console: console };
ctx.window.FL = ctx.FL;
vm.runInContext(fs.readFileSync(path.join(root, "kra2-a-workspace-ui.js"), "utf8"), vm.createContext(ctx));

var ui = ctx.FL.kra2AWorkspaceUi;
var meta = ui.facultyStatusMeta({ reviewStatus: "pending", submittedForReviewAt: "2025-01-01" });
if (meta.label !== "Under Review") throw new Error("expected Under Review");
var sole = ui.requiredSlotIds({ contribution: "sole" });
if (sole.length !== 1 || sole[0] !== "primary_output") throw new Error("sole slots");
var co = ui.requiredSlotIds({ contribution: "declared" });
if (co.length !== 2) throw new Error("co slots");

console.log("kra2-a-workspace-ui.test.js OK");
