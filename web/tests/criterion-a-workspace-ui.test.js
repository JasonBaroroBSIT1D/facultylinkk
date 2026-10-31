"use strict";

var fs = require("fs");
var path = require("path");
var global = globalThis;
eval(fs.readFileSync(path.join(__dirname, "../js/tev-review-ui.js"), "utf8"));
eval(fs.readFileSync(path.join(__dirname, "../js/criterion-a-workspace-ui.js"), "utf8"));

var ui = global.FL.criterionAWorkspaceUi;
var assert = function (cond, msg) {
  if (!cond) throw new Error(msg || "Assertion failed");
};

(function testGroupBySource() {
  var groups = ui.groupBySourceDocument(
    [{ documentId: "d1", fileName: "a.pdf" }],
    [
      { documentId: "d1", evaluationType: "SET", teachingEvaluationId: "t1" },
      { documentId: "d1", evaluationType: "SEF", teachingEvaluationId: "t2" }
    ]
  );
  assert(groups.length === 1);
  assert(groups[0].records.length === 2);
})();

(function testFilterSetAndSearch() {
  var rows = [
    { documentId: "d1", evaluationType: "SET", academicYear: "2024-2025", semester: "1st Semester", reviewerValidationStatus: "pending-review" },
    { documentId: "d1", evaluationType: "SEF", academicYear: "2024-2025", semester: "2nd Semester", reviewerValidationStatus: "approved" }
  ];
  var setOnly = ui.filterRecords(rows, "set", "");
  assert(setOnly.length === 1);
  var search = ui.filterRecords(rows, "all", "2nd");
  assert(search.length === 1);
  assert(search[0].evaluationType === "SEF");
})();

(function testSummaryFromBackendCounts() {
  var s = ui.summaryCounts({ total: 10, validated: 4, pending: 5, incomplete: 1 }, []);
  assert(s.total === 10);
  assert(s.reviewed === 4);
  assert(s.pending === 6);
})();

(function testAttentionDocs() {
  var att = ui.documentsNeedingAttention(
    [{ documentId: "d1" }, { documentId: "d2" }],
    [{ documentId: "d1", evaluationType: "SET" }]
  );
  assert(att.length === 1);
  assert(att[0].documentId === "d2");
})();

(function testFormatHelpers() {
  assert(ui.formatPeriodLabel({ academicYear: "2023-2024", semester: "1st Semester" }) === "2023-2024 · 1st Semester");
  assert(ui.formatExtractedRating({ ratingRaw: "92.00", ratingScale: 100 }) === "92.00 / 100");
  assert(ui.formatExtractedRating({ ratingRaw: "95.00 / 100", ratingScale: 100 }) === "95.00 / 100");
  assert(ui.formatExtractedRating({ ratingRaw: "89.00 / 100 / 100", ratingScale: 100 }) === "89.00 / 100");
  assert(ui.formatExtractedRating({ ratingRaw: "88/100", ratingScale: 100 }) === "88 / 100");
  assert(ui.formatExtractedRating({ ratingRaw: "4.25", ratingScale: 5 }) === "4.25 / 5");
  assert(ui.formatExtractedRating({ ratingRaw: "4.25 / 5", ratingScale: 5 }) === "4.25 / 5");
  var sorted = ui.sortEvaluationRecords([
    { academicYear: "2024-2025", semester: "1st", evaluationType: "SEF" },
    { academicYear: "2023-2024", semester: "2nd", evaluationType: "SET" }
  ]);
  assert(sorted[0].academicYear === "2023-2024");
})();

(function testDocumentsNeedingAttention() {
  var sources = [
    { documentId: "d1", fileName: "a.pdf", ocrStatus: "Completed" },
    { documentId: "d2", fileName: "b.pdf", ocrStatus: "Completed", classificationStatus: "needs_classification" }
  ];
  var records = [{ documentId: "d1", teachingEvaluationId: "t1" }];
  var attention = ui.documentsNeedingAttention(sources, records);
  assert(attention.length === 1 && attention[0].documentId === "d2");
  var docMap = function (id) {
    if (id === "d1") {
      return { documentInformation: { nameVerificationLabel: "Name Mismatch" } };
    }
    return null;
  };
  attention = ui.documentsNeedingAttention(sources, records, docMap);
  assert(attention.length === 2);
  assert(ui.attentionIssueLabel(sources[0], docMap("d1")).indexOf("mismatch") >= 0);
})();

(function testFacultyNameDisplay() {
  assert(ui.formatFacultyNameLabel({
    facultyName: "Jason Baroro",
    facultyNameSource: "document"
  }) === "Jason Baroro");
  assert(ui.formatFacultyNameLabel({
    facultyName: "Ana Reyes",
    facultyNameSource: "profile",
    facultyNameNote: "Taken from the faculty profile (name was not detected on the document)."
  }) === "Ana Reyes (from profile)");
  assert(ui.formatFacultyNameLabel({
    facultyName: "Diego Ramos",
    needsVerification: true,
    facultyNameSource: "document",
    nameVerificationLabel: "Name Mismatch"
  }) === "Diego Ramos");
  var meta = ui.facultyNameDisplayMeta({
    facultyName: "Diego Ramos",
    needsVerification: true,
    nameVerificationLabel: "Name Mismatch",
    facultyNameNote: "Mismatch note"
  });
  assert(meta.needsVerification === true);
  assert(meta.note === "Mismatch note");
})();

console.log("criterion-a-workspace-ui.test.js: all passed");
