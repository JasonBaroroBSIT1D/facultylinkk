"use strict";

var fs = require("fs");
var path = require("path");

var uiSrc = fs.readFileSync(path.join(__dirname, "../js/kra2-a-workspace-ui.js"), "utf8");

if (uiSrc.indexOf("CRITERION_B_REQUIRED_SLOTS") < 0) throw new Error("CRITERION_B_REQUIRED_SLOTS block missing");
if (uiSrc.indexOf('"kra2-b-patent-g-sole"') < 0) throw new Error("patent grant sole missing from B catalog");
if (uiSrc.indexOf("invention_photo") < 0) throw new Error("invention_photo slot missing");
if (uiSrc.indexOf("criterionBRequiredSlots") < 0) throw new Error("criterionBRequiredSlots helper missing");

function slotsFor(id) {
  var re = new RegExp('"' + id + '":\\s*\\[([^\\]]+)\\]', "m");
  var m = uiSrc.match(re);
  if (!m) throw new Error("missing slots for " + id);
  return m[1].split(",").map(function (s) {
    return s.trim().replace(/^"|"$/g, "");
  });
}

var swCo = slotsFor("kra2-b-sw-new-co");
if (swCo.length !== 6) throw new Error("sw-new-co must list 6 slots, got " + swCo.length);
if (swCo.indexOf("contribution_certificate") < 0) throw new Error("sw-new-co missing contribution_certificate");

var varietyCo = slotsFor("kra2-b-variety-co");
if (varietyCo.join(",") !== "registration_deposit_evidence,contribution_certificate") {
  throw new Error("variety-co slots mismatch: " + varietyCo.join(","));
}

console.log("kra2-criterion-b-evidence.test.js OK");
