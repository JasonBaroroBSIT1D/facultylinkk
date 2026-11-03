"use strict";

var fs = require("fs");
var path = require("path");
var global = globalThis;
global.window = global;
global.FL = {
  esc: function (s) { return String(s || ""); },
  criterionBWorkspaceUi: {
    scoringBlockMessages: function () { return []; }
  },
  criterionBEvidence: { patchBundle: function () { return Promise.resolve({}); }, fetchBundle: function () { return Promise.resolve({}); } },
  store: { refreshLiveDocument: function () { return Promise.resolve({}); } }
};

eval(fs.readFileSync(path.join(__dirname, "../js/criterion-b-simple-review.js"), "utf8"));

var review = global.FL.criterionBSimpleReview;
var assert = function (cond, msg) {
  if (!cond) throw new Error(msg || "Assertion failed");
};

(function testSkipsUnchangedSlotPatch() {
  var state = {
    bundleRemarks: "Nice work",
    drafts: {},
    items: [{
      slotId: "approved_syllabus",
      label: "Syllabus",
      entry: { status: "verified", reviewerNote: "" },
      draftStatus: "verified"
    }]
  };
  assert(review._checklistSlotChanged(state, state.items[0]) === false);
  assert(review._checklistSlotBody(state, state.items[0], true) === null);
})();

(function testBuildsChangedSlotBody() {
  var state = {
    bundleRemarks: "Feedback",
    drafts: { library_certification: { status: "verified", note: "" } },
    items: [{
      slotId: "library_certification",
      label: "Library",
      entry: { status: "present_unverified", reviewerNote: "" },
      draftStatus: "present_unverified"
    }]
  };
  assert(review._checklistSlotChanged(state, state.items[0]) === true);
  var body = review._checklistSlotBody(state, state.items[0], true);
  assert(body.evidenceSlot === "library_certification");
  assert(body.status === "verified");
  assert(body.remarks === "Feedback");
})();

console.log("criterion-b-simple-review-persist.test.js: all passed");
