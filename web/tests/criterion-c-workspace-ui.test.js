"use strict";

var fs = require("fs");
var path = require("path");
var global = globalThis;
global.window = global;
global.FL = {
  esc: function (s) {
    return String(s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;");
  },
  ui: {
    statusBadge: function (kind) {
      return "[" + kind + "]";
    },
    empty: function (title, msg) {
      return title + ": " + msg;
    },
    loading: function (msg) {
      return "loading:" + msg;
    }
  },
  documents: {
    kvRow: function (label, value) {
      return "<div class=\"kv\"><dt>" + label + "</dt><dd>" + value + "</dd></div>";
    },
    ocrStatusLabel: function () {
      return "completed";
    }
  },
  rules: {
    findIndicator: function (id) {
      if (id === "kra1-c-adviser-sp") return { indicator: { name: "SP Adviser", points: 3 } };
      if (id === "kra1-c-mentor") return { indicator: { name: "Mentor", points: 3 } };
      return null;
    },
    criterionUserLabel: function (_id, name) {
      return name;
    }
  },
  store: { documents: [], documentById: function () { return null; } },
  apiClient: { adminRequest: function () { return Promise.resolve({}); } },
  evidence: { _facultyDocs: function () { return []; } }
};

eval(fs.readFileSync(path.join(__dirname, "../js/criterion-c-workspace-ui.js"), "utf8"));
eval(fs.readFileSync(path.join(__dirname, "../js/criterion-c-evidence.js"), "utf8"));

var ui = global.FL.criterionCWorkspaceUi;
var assert = function (cond, msg) {
  if (!cond) throw new Error(msg || "Assertion failed");
};

(function testPrimaryVsSupporting() {
  assert(ui.isPrimaryClaimDocument({ criterionId: "kra1-c", indicatorId: "kra1-c-adviser-sp" }) === true);
  assert(
    ui.isPrimaryClaimDocument({
      criterionId: "kra1-c",
      criterionCEvidence: { isSupportingDocument: true }
    }) === false
  );
})();

(function testApprovalSheetSelfLinkStillPrimary() {
  var docs = [
    {
      id: "p1",
      criterionId: "kra1-c",
      indicatorId: "kra1-c-panel-sp",
      status: "pending_review",
      criterionCEvidence: {
        bundle: {
          projectTitle: "AI-Assisted Campus Help Desk",
          checklist: {
            approval_sheet: { documentId: "p1", status: "present_unverified" },
            rrpa_copc: { documentId: "s1", status: "present_unverified" }
          }
        }
      }
    },
    {
      id: "s1",
      criterionId: "kra1-c",
      criterionCEvidence: { isSupportingDocument: true, link: { role: "supporting", primaryDocumentId: "p1" } }
    }
  ];
  var model = ui.buildWorkspaceModel(docs);
  assert(model.length === 1, "expected one primary accomplishment");
  assert(model[0].primary.id === "p1");
})();

(function testMergeApiRowsWhenStoreEmpty() {
  var rows = [
    {
      documentId: "doc-a",
      indicatorId: "kra1-c-adviser-sp",
      status: "pending_review",
      projectTitle: "Thesis Alpha",
      reviewStatus: "pending",
      estimatedPoints: 3
    }
  ];
  var items = ui.mergeAccomplishmentListItems(rows, []);
  assert(items.length === 1);
  assert(items[0].bundle.projectTitle === "Thesis Alpha");
  assert(items[0].primary.id === "doc-a");
})();

(function testSplitDraftAndReview() {
  var items = [
    { primary: { status: "draft" }, bundle: {} },
    { primary: { status: "pending_review" }, bundle: { reviewStatus: "pending" } }
  ];
  var split = ui.splitReviewAndDraftItems(items);
  assert(split.drafts.length === 1);
  assert(split.review.length === 1);
})();

(function testWorkspaceRendersWhenApiHasRows() {
  var html = ui.criterionCReviewWorkspaceHtml({
    personName: "Jason Baroro",
    summary: { accomplishmentCount: 2, reviewCounts: { pending: 2, approved: 0, rejected: 0 }, draftEstimatedSum: 4 },
    items: [
      { primary: { id: "a", status: "draft", indicatorId: "kra1-c-panel-sp" }, bundle: { projectTitle: "Draft One" }, validation: {}, scoring: {} },
      { primary: { id: "b", status: "pending_review", indicatorId: "kra1-c-adviser-sp" }, bundle: { projectTitle: "Submitted Two", reviewStatus: "pending" }, validation: {}, scoring: { estimatedPoints: 3 } }
    ],
    reviewHref: function () { return "#"; }
  });
  assert(html.indexOf("No accomplishments") < 0, "must not show empty state when items exist");
  assert(html.indexOf("cc-accomplishment-list") >= 0);
  assert(html.indexOf("Faculty drafts") >= 0);
})();

(function testOfficialPoints() {
  assert(ui.officialPointsForIndicator("kra1-c-adviser-sp") === 3);
  assert(ui.officialPointsForIndicator("kra1-c-mentor") === 3);
})();

(function testMultipleAccomplishmentsSameIndicator() {
  var docs = [
    { id: "a1", criterionId: "kra1-c", indicatorId: "kra1-c-adviser-sp", criterionCEvidence: { bundle: { projectTitle: "T1" } } },
    { id: "a2", criterionId: "kra1-c", indicatorId: "kra1-c-adviser-sp", criterionCEvidence: { bundle: { projectTitle: "T2" } } }
  ];
  var model = ui.buildWorkspaceModel(docs);
  assert(model.length === 2);
})();

(function testPolicyFlagHumanize() {
  var msg = ui.humanizeFlag("adviser_panel_same_thesis_review");
  assert(msg.indexOf("Policy") >= 0);
  assert(ui.humanizeFlag("duplicate_service_suspected").indexOf("duplicate") >= 0);
})();

(function testSlotLabelsResearch() {
  var slots = ui.requiredSlotIds({ serviceCategory: "research" });
  assert(slots.indexOf("approval_sheet") >= 0);
  assert(slots.indexOf("rrpa_copc") >= 0);
})();

(function testSlotLabelsMentorship() {
  var slots = ui.requiredSlotIds({ serviceCategory: "mentorship" });
  assert(slots.length === 4);
})();

(function testFilterAccomplishments() {
  var items = [
    {
      primary: { indicatorId: "kra1-c-adviser-ut" },
      bundle: { projectTitle: "Alpha Thesis", studentNames: "S1" }
    },
    {
      primary: { indicatorId: "kra1-c-mentor" },
      bundle: { projectTitle: "Beta Coach", serviceCategory: "mentorship" }
    }
  ];
  var filtered = ui.filterAccomplishments(items, "alpha");
  assert(filtered.length === 1);
})();

(function testSummaryHeaderCap() {
  var html = ui.summaryHeaderHtml({
    summary: {
      maxPoints: 10,
      estimatedPoints: 8,
      draftEstimatedSum: 6,
      reviewCounts: { pending: 1, approved: 2, rejected: 0 },
      accomplishmentCount: 3
    },
    personName: "Test Faculty",
    visibleCount: 3,
    criterionTitle: "Criterion C — Research Advising and Mentorship Services"
  });
  assert(html.indexOf("Accomplishments") >= 0);
  assert(html.indexOf("Estimated (unverified)") >= 0);
  assert(html.indexOf("Research Advising and Mentorship") >= 0);
  assert(html.indexOf("6") >= 0);
  assert(html.indexOf("10") >= 0);
})();

(function testWorkspaceOmitsSearchAndIntro() {
  var html = ui.criterionCReviewWorkspaceHtml({
    personName: "Faculty",
    summary: { accomplishmentCount: 1, reviewCounts: { pending: 1, approved: 0, rejected: 0 } },
    items: [
      {
        primary: { id: "x", status: "pending_review", indicatorId: "kra1-c-adviser-sp" },
        bundle: { projectTitle: "T", researchType: "sp_cp", role: "adviser" },
        validation: {},
        scoring: { estimatedPoints: 3 }
      }
    ],
    reviewHref: function () { return "#"; }
  });
  assert(html.indexOf("cc-accomplishment-filter") < 0);
  assert(html.indexOf("Each card is one research") < 0);
  assert(html.indexOf("Open Review") >= 0);
})();

(function testAccomplishmentScoringContextUsesDynamicPoints() {
  var html = ui.accomplishmentScoringContextHtml({
    facultyName: "Jason Baroro",
    bundle: { researchType: "sp_cp", role: "adviser", serviceCategory: "research" },
    doc: { indicatorId: "kra1-c-adviser-sp" }
  });
  assert(html.indexOf("Jason Baroro") >= 0);
  assert(html.indexOf("Applicable points") >= 0);
  assert(html.indexOf("3") >= 0);
  assert(html.indexOf("Criterion C maximum") >= 0);
})();

(function testApiPaths() {
  assert(
    FL.criterionCEvidence.bundlePath({ role: "reviewer" }, "doc_x").indexOf("criterion-c") >= 0
  );
  assert(
    FL.criterionCEvidence.facultySummaryPath({ role: "reviewer" }, "fac_1").indexOf("fac_1") >= 0
  );
})();

(function testApprovedAccomplishmentCardShowsVerifiedPoints() {
  var html = ui.accomplishmentCardHtml(
    {
      primary: { id: "doc_help", status: "pending_review", indicatorId: "kra1-c-adviser-sp" },
      bundle: {
        projectTitle: "AI-Assisted Campus Help Desk",
        reviewStatus: "approved",
        academicYear: "2025-2026",
        researchType: "sp_cp",
        role: "adviser"
      },
      scoring: { estimatedPoints: 3, reviewerAssessedPoints: 3 }
    },
    { reviewHref: function () { return "#"; } }
  );
  assert(html.indexOf("Approved") >= 0);
  assert(html.indexOf("Reviewer-verified") >= 0);
  assert(html.indexOf("Estimated (unverified)") < 0);
})();

console.log("criterion-c-workspace-ui.test.js: all tests passed");
