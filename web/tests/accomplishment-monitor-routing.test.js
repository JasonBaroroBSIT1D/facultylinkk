"use strict";

var fs = require("fs");
var path = require("path");

var evidence = fs.readFileSync(path.join(__dirname, "../js/evidence-workspace.js"), "utf8");
var documents = fs.readFileSync(path.join(__dirname, "../js/documents.js"), "utf8");
var assert = function (cond, msg) {
  if (!cond) throw new Error(msg || "Assertion failed");
};

assert(
  evidence.indexOf("FL.reviewerNav.accomplishmentReviewUrl(doc)") !== -1,
  "reviewDocHref must call accomplishmentReviewUrl when reviewerNav is loaded"
);
assert(
  evidence.indexOf('document.body.dataset.role === "reviewer" && FL.reviewerNav') === -1,
  "reviewDocHref must not gate accomplishmentReviewUrl on reviewer role only"
);
assert(
  documents.indexOf("redirectLegacyDocumentReview") !== -1,
  "admin-document-view must redirect legacy document view to workspace"
);
assert(
  documents.indexOf("if (FL.reviewerNav && FL.reviewerNav.accomplishmentReviewUrl) {") !== -1,
  "renderReview must redirect to accomplishment workspace when reviewerNav is present"
);

console.log("accomplishment-monitor-routing.test.js: all passed");
