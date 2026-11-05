"use strict";

var fs = require("fs");
var path = require("path");
var vm = require("vm");

var src = fs.readFileSync(
  path.join(__dirname, "../js/reviewer-accomplishment-state.js"),
  "utf8"
);
var ctx = { window: {}, FL: {} };
ctx.window.FL = ctx.FL;
vm.runInNewContext(src, ctx);
var ras = ctx.FL.reviewerAccomplishmentState;

function assert(cond, msg) {
  if (!cond) throw new Error(msg || "Assertion failed");
}

var draftState = {
  doc: { status: "draft" },
  bundle: {},
  validation: { flags: ["not_submitted"] },
  canDecide: true
};
assert(ras.isDraftAwaitingFaculty(draftState), "draft doc is awaiting faculty");
assert(!ras.canVerifyEvidence(draftState), "draft cannot verify evidence");
assert(ras.canSavePreparationNotes(draftState), "draft allows prep notes");
assert(!ras.canSaveFullAssessment(draftState), "draft blocks full assessment");
assert(
  ras.slotVerificationDisplayLabel(draftState, "verified") === "Not ready for verification",
  "draft slot label"
);

var pendingState = {
  doc: { status: "pending_review" },
  bundle: { submittedForReviewAt: "2025-01-01T00:00:00Z", reviewStatus: "pending" },
  validation: {},
  canDecide: true
};
assert(ras.isSubmittedForReview(pendingState), "pending_review is submitted");
assert(ras.canVerifyEvidence(pendingState), "pending can verify");
assert(ras.canFinalizeReviewDecision(pendingState), "pending can finalize when eligible");

console.log("reviewer-accomplishment-state.test.js: all passed");
