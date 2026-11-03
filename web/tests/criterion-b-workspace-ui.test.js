"use strict";

var fs = require("fs");
var path = require("path");
var global = globalThis;
global.window = global;
global.FL = {
  esc: function (s) { return String(s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;"); },
  ui: {
    statusBadge: function (kind) { return "[" + kind + "]"; }
  },
  documents: {
    kvRow: function (label, value) {
      return "<div class=\"kv\"><dt>" + label + "</dt><dd>" + value + "</dd></div>";
    }
  },
  rules: {
    findIndicator: function (id) {
      if (id === "kra1-b-program-lead") {
        return { indicator: { name: "Program Lead", points: 10 } };
      }
      if (id === "kra1-b-module-sole") {
        return { indicator: { name: "Module sole", points: 16 } };
      }
      return null;
    },
    criterionUserLabel: function (_id, name) { return name; }
  }
};

eval(fs.readFileSync(path.join(__dirname, "../js/criterion-b-workspace-ui.js"), "utf8"));
eval(fs.readFileSync(path.join(__dirname, "../js/criterion-b-evidence.js"), "utf8"));

var ui = global.FL.criterionBWorkspaceUi;
var api = global.FL.criterionBEvidence;
var assert = function (cond, msg) {
  if (!cond) throw new Error(msg || "Assertion failed");
};

(function testPrimaryVsSupporting() {
  assert(ui.isPrimaryClaimDocument({ criterionId: "kra1-b", indicatorId: "kra1-b-module-sole" }) === true);
  assert(ui.isPrimaryClaimDocument({
    criterionId: "kra1-b",
    criterionBEvidence: { isSupportingDocument: true }
  }) === false);
  assert(ui.isPrimaryClaimDocument({
    criterionId: "kra1-b",
    indicatorId: "kra1-b-textbook-sole",
    name: "03 Approved Course Syllabus",
    criterionBEvidence: {
      link: { role: "supporting", primaryDocumentId: "doc_515", evidenceSlot: "approved_syllabus" }
    }
  }) === false);
})();

(function testValidationStatusIncompleteNotInvalid() {
  var meta = ui.validationStatusMeta("incomplete");
  assert(meta.label.indexOf("Incomplete") >= 0);
  assert(meta.badge === "pending");
})();

(function testIndicatorNavCategories() {
  var html = ui.indicatorNavHtml({ id: "kra1-b" }, [], {});
  assert(html.indexOf("Instructional Materials") >= 0);
  assert(html.indexOf("Academic Programs") >= 0);
  assert(html.indexOf("kra1-b-textbook-sole") >= 0);
  assert(html.indexOf("kra1-b-program-contributor") >= 0);
})();

(function testChecklistRendersVerifiedOption() {
  var bundle = {
    checklist: {
      dean_contribution_certification: { status: "present_unverified", documentId: "d1", ocrHintOnly: true }
    }
  };
  var html = ui.checklistHtml(bundle, {}, { canEdit: true });
  assert(html.indexOf("Verified") >= 0);
  assert(html.indexOf("not verified") >= 0 || html.indexOf("Automatic text read") >= 0);
})();

(function testCrossKraWarningsDoNotReject() {
  var html = ui.crossKraWarningsHtml([
    { confidence: "uncertain", message: "Possible Extension Criterion D overlap." }
  ]);
  assert(html.indexOf("Uncertain") >= 0);
  assert(html.indexOf("overlap") >= 0);
})();

(function testScoringPreviewNotOfficial() {
  var preview = ui.informationalScoringPreview(
    { authorship: "sole" },
    { readyForScoring: false },
    "kra1-b-program-lead"
  );
  assert(preview.points == null);
  assert(preview.note.indexOf("Informational") >= 0);
})();

(function testReviewerApiPath() {
  var pathReviewer = api.bundlePath({ role: "reviewer" }, "doc-abc");
  assert(pathReviewer === "/api/reviewer/documents/doc-abc/criterion-b/evidence-bundle");
  var pathAdmin = api.bundlePath({ role: "administrator" }, "doc-abc");
  assert(pathAdmin.indexOf("/api/admin/documents/") === 0);
})();

(function testProgramBundleSummary() {
  var html = ui.claimSummaryHtml(
    { id: "d1", ocr: { status: "completed" } },
    {
      claimType: "academic_program",
      programName: "BS CS",
      programDevelopmentKind: "new_program",
      facultyRole: "lead",
      contributionDescription: "Led outcomes mapping"
    },
    { validationStatus: "incomplete", flags: ["missing_dean_contribution_certification"], readyForScoring: false, readyForReviewer: false },
    [],
    { points: null, note: "Informational" },
    { ocr: { status: "completed" } }
  );
  assert(html.indexOf("BS CS") >= 0);
  assert(html.indexOf("Incomplete") >= 0 || html.indexOf("[pending]") >= 0);
  assert(html.indexOf("automatic text extraction") >= 0 || html.indexOf("OCR") >= 0);
})();

(function testHumanizeFlag() {
  var msg = ui.humanizeFlag("missing_library_certification");
  assert(msg.indexOf("Library") >= 0);
})();

(function testWorkspaceModelGroupsSupportingByChecklist() {
  var docs = [
    {
      id: "primary-1",
      criterionId: "kra1-b",
      name: "Calculus Module.pdf",
      criterionBEvidence: {
        bundle: {
          claimType: "instructional_material",
          materialTitle: "Calculus Module",
          checklist: {
            primary_material: { documentId: "primary-1", status: "present_unverified" },
            library_certification: { documentId: "sup-lib", status: "present_unverified" },
            imdc_evaluation_approval: { documentId: "sup-imdc", status: "verified" }
          }
        },
        validation: { validationStatus: "incomplete" }
      }
    },
    {
      id: "sup-lib",
      criterionId: "kra1-b",
      name: "Library cert.pdf",
      criterionBEvidence: { isSupportingDocument: true, link: { primaryDocumentId: "primary-1", evidenceSlot: "library_certification" } }
    },
    {
      id: "sup-imdc",
      criterionId: "kra1-b",
      name: "IMDC.pdf",
      criterionBEvidence: { isSupportingDocument: true, link: { primaryDocumentId: "primary-1" } }
    },
    {
      id: "orphan-1",
      criterionId: "kra1-b",
      name: "Loose syllabus.pdf",
      criterionBEvidence: { isSupportingDocument: true }
    }
  ];
  var model = ui.buildCriterionBWorkspaceModel(docs);
  assert(model.accomplishments.length === 1);
  assert(model.accomplishments[0].supporting.length === 2);
  assert(model.needsLinking.length === 1);
  assert(model.needsLinking[0].id === "orphan-1");
  var card = ui.accomplishmentReviewCardHtml(model.accomplishments[0], {
    reviewHref: function () { return "/review"; }
  });
  assert(card.indexOf("Review &amp; Give Score") >= 0 || card.indexOf("Review & Give Score") >= 0);
  assert(card.indexOf("Library cert") >= 0);
  assert(card.indexOf("Calculus Module") >= 0);
  var ws = ui.criterionBReviewWorkspaceHtml({
    documents: docs,
    reviewHref: function () { return "#"; }
  });
  assert(ws.indexOf("Needs linking") >= 0);
  assert(ws.indexOf("Loose syllabus") >= 0);
})();

(function testJasonLikeSupportingTitlesNotSeparateAccomplishments() {
  var docs = [
    {
      id: "doc_515cf7afd70c",
      criterionId: "kra1-b",
      indicatorId: "kra1-b-textbook-sole",
      name: "01 Primary Textbook",
      criterionBEvidence: {
        bundle: {
          claimType: "instructional_material",
          materialTitle: "Foundations of Applied Mathematics: A College Textbook",
          checklist: {
            primary_material: { documentId: "doc_515cf7afd70c", status: "present_unverified" },
            approved_syllabus: { documentId: "doc_2c29ab646b94", status: "present_unverified" },
            imdc_evaluation_approval: { documentId: "doc_d81c79e03d74", status: "present_unverified" },
            library_certification: { documentId: "doc_3b679f67e912", status: "present_unverified" }
          }
        },
        validation: {
          validationStatus: "reviewer_required",
          checklistSummary: {
            approved_syllabus: "reviewer_required",
            imdc_evaluation_approval: "reviewer_required",
            library_certification: "reviewer_required"
          }
        },
        scoring: {
          displayScore: { label: "Estimated", points: 30, source: "automated_estimate" },
          systemEstimatePoints: 30
        }
      }
    },
    {
      id: "doc_2c29ab646b94",
      criterionId: "kra1-b",
      name: "03 Approved Course Syllabus",
      criterionBEvidence: {
        link: { role: "supporting", primaryDocumentId: "doc_515cf7afd70c", evidenceSlot: "approved_syllabus" }
      }
    },
    {
      id: "doc_d81c79e03d74",
      criterionId: "kra1-b",
      name: "02 IMDC",
      criterionBEvidence: {
        link: { role: "supporting", primaryDocumentId: "doc_515cf7afd70c", evidenceSlot: "imdc_evaluation_approval" }
      }
    },
    {
      id: "doc_3b679f67e912",
      criterionId: "kra1-b",
      name: "04 Library Certification",
      criterionBEvidence: {
        link: { role: "supporting", primaryDocumentId: "doc_515cf7afd70c", evidenceSlot: "library_certification" }
      }
    }
  ];
  var model = ui.buildCriterionBWorkspaceModel(docs);
  assert(model.accomplishments.length === 1, "expected one accomplishment");
  assert(model.accomplishments[0].supporting.length === 3);
  assert(model.needsLinking.length === 0);
  var card = ui.accomplishmentReviewCardHtml(model.accomplishments[0], {
    reviewHref: function () { return "/review"; }
  });
  assert(card.indexOf("Foundations of Applied Mathematics") >= 0);
  assert(card.indexOf("Estimated") >= 0);
  assert(card.indexOf("30 pts") >= 0);
})();

(function testReviewReadinessListsUnverifiedSlots() {
  var state = {
    bundle: { materialType: "textbook", specializationAligned: null },
    validation: { readyForScoring: false },
    drafts: {},
    items: [
      {
        slotId: "approved_syllabus",
        label: "Approved syllabus",
        entry: { documentId: "syl1", status: "present_unverified" },
        fileDoc: { name: "03 Approved Course Syllabus.pdf" },
        draftStatus: "present_unverified"
      },
      {
        slotId: "library_certification",
        label: "Library certification",
        entry: { documentId: "lib1", status: "present_unverified" },
        fileDoc: { name: "04 Library Certification.pdf" },
        draftStatus: "present_unverified"
      }
    ]
  };
  assert(ui.canFinalizeReviewerScore(state) === false);
  var html = ui.reviewReadinessChecklistHtml(state, { showJump: true });
  assert(html.indexOf("Before you can finish") >= 0);
  assert(html.indexOf("Approved syllabus") >= 0);
  assert(html.indexOf("Pending review") >= 0);
  assert(html.indexOf("Estimated") >= 0);
  state.drafts.approved_syllabus = { status: "verified" };
  state.drafts.library_certification = { status: "verified" };
  state.specializationAligned = true;
  assert(ui.canFinalizeReviewerScore(state) === true);
})();

(function testRegressionCriterionANavUntouched() {
  var wsSrc = fs.readFileSync(path.join(__dirname, "../js/evidence-workspace.js"), "utf8");
  assert(wsSrc.indexOf('state.criterionId === "kra1-a"') >= 0);
  assert(wsSrc.indexOf("criterionAUnifiedWorkspaceHtml") >= 0);
  assert(wsSrc.indexOf('state.criterionId === "kra1-b"') >= 0);
})();

console.log("criterion-b-workspace-ui.test.js: all passed");
