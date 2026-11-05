"use strict";

var fs = require("fs");
var path = require("path");

var assert = function (cond, msg) {
  if (!cond) throw new Error(msg || "Assertion failed");
};

var kra2 = fs.readFileSync(path.join(__dirname, "../js/kra2-a-review.js"), "utf8");
var evidence = fs.readFileSync(path.join(__dirname, "../js/evidence-workspace.js"), "utf8");
var nav = fs.readFileSync(path.join(__dirname, "../js/reviewer-nav.js"), "utf8");
var documents = fs.readFileSync(path.join(__dirname, "../js/documents.js"), "utf8");
var docFolders = fs.readFileSync(path.join(__dirname, "../js/doc-folders.js"), "utf8");

assert(kra2.indexOf("_resolveMountEl") !== -1, "kra2-a-review must resolve mount host in workspace");
assert(kra2.indexOf("mountWorkspaceAccomplishmentReview") !== -1, "workspace accomplishment review mount required");
assert(
  kra2.indexOf("document.getElementById(\"page\").innerHTML = FL.ui.loading") === -1,
  "paintReviewPage must not wipe Evidence Workspace #page"
);
assert(nav.indexOf("accomplishmentReviewUrl") !== -1, "reviewer-nav must route to workspace accomplishment review");
assert(
  nav.indexOf("document-review.html?id=") === -1,
  "reviewer-nav must not build standalone document-review URLs"
);
assert(
  evidence.indexOf("if (state.focusDoc)") !== -1,
  "refreshCountsAfterReview must skip full re-render while focusDoc review is open"
);
assert(
  documents.indexOf("redirectLegacyDocumentReview") !== -1,
  "reviewer-review page must redirect legacy document-review bookmarks"
);
assert(
  documents.indexOf("accomplishmentReviewUrl") !== -1 && documents.indexOf("href: function (idOrDoc)") !== -1,
  "documents.href must route reviewers to accomplishment review URLs"
);
assert(
  documents.indexOf("paintReview: function (session, doc, canDecide)") !== -1
    && documents.indexOf("accomplishmentReviewUrl(FL.reviewerNav.enrichDocFromUrlParams(doc))") !== -1,
  "paintReview must redirect reviewers away from standalone tabbed document review"
);
assert(
  nav.indexOf("enrichDocFromUrlParams") !== -1,
  "reviewer-nav must merge URL context before resolving accomplishment targets"
);
assert(
  docFolders.indexOf("indicatorDocHref") !== -1 && docFolders.indexOf("accomplishmentReviewUrl") !== -1,
  "doc-folders must route reviewer file cards to accomplishment review"
);

console.log("reviewer-evidence-focus-mount.test.js: all passed");
