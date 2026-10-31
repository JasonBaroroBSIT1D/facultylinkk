/**
 * Criterion A workspace helpers (filter, search, counts; no DOM).
 */
(function (global) {
  "use strict";
  var FL = global.FL = global.FL || {};

  function rowAsTev(row) {
    return {
      evaluationType: row.evaluationType,
      reviewerValidationStatus: row.reviewerValidationStatus || row.reviewDisplayStatus,
      incompleteExtraction: row.incompleteExtraction,
      extractionStatus: row.extractionStatus
    };
  }

  FL.criterionAWorkspaceUi = {
    groupBySourceDocument: function (sources, records) {
      var map = {};
      (sources || []).forEach(function (s) {
        if (!s || !s.documentId) return;
        map[s.documentId] = { source: s, records: [] };
      });
      (records || []).forEach(function (r) {
        var id = r.documentId;
        if (!id) return;
        if (!map[id]) {
          map[id] = {
            source: {
              documentId: id,
              fileName: r.fileName,
              ocrStatus: "—",
              compositionDisplay: "—",
              childValidationSummary: { total: 0 }
            },
            records: []
          };
        }
        map[id].records.push(r);
      });
      return Object.keys(map).map(function (k) { return map[k]; });
    },

    recordPassesFilter: function (row, filter) {
      if (!FL.tevReviewUi) return true;
      return FL.tevReviewUi.passesFilter(rowAsTev(row), filter);
    },

    filterRecords: function (records, filter, query) {
      var q = String(query || "").trim().toLowerCase();
      return (records || []).filter(function (row) {
        if (!FL.criterionAWorkspaceUi.recordPassesFilter(row, filter || "all")) return false;
        if (!q) return true;
        var hay = [
          row.academicYear,
          row.semester,
          row.evaluationType,
          row.ratingRaw,
          row.fileName
        ].join(" ").toLowerCase();
        return hay.indexOf(q) >= 0;
      });
    },

    summaryCounts: function (childValidation, records) {
      if (childValidation && childValidation.total != null) {
        var total = parseInt(childValidation.total, 10) || 0;
        var validated = parseInt(childValidation.validated, 10) || 0;
        var pending = parseInt(childValidation.pending, 10) || 0;
        var incomplete = parseInt(childValidation.incomplete, 10) || 0;
        return {
          total: total,
          reviewed: validated,
          pending: pending + incomplete
        };
      }
      if (FL.tevReviewUi && records && records.length) {
        var c = FL.tevReviewUi.summaryCounts(records);
        return {
          total: c.total,
          reviewed: c.reviewed,
          pending: c.pending
        };
      }
      return { total: 0, reviewed: 0, pending: 0 };
    },

    documentsNeedingAttention: function (sources, records, getDoc) {
      var withRecords = {};
      (records || []).forEach(function (r) {
        if (r.documentId) withRecords[r.documentId] = true;
      });
      var seen = {};
      var out = [];
      (sources || []).forEach(function (s) {
        if (!s || !s.documentId || seen[s.documentId]) return;
        var doc = typeof getDoc === "function" ? getDoc(s.documentId) : null;
        var info = doc && doc.documentInformation;
        var verify = info && info.nameVerificationLabel;
        var ownershipIssue = verify && verify !== "Name Matched";
        var needsClass = s.compositionDisplay === "Needs Classification"
          || s.classificationStatus === "needs_classification";
        var ocrFailed = String(s.ocrStatus || "").toLowerCase() === "failed";
        var noRows = !withRecords[s.documentId];
        if (noRows || ownershipIssue || needsClass || ocrFailed) {
          seen[s.documentId] = true;
          out.push(s);
        }
      });
      return out;
    },

    attentionIssueLabel: function (source, doc) {
      var info = doc && doc.documentInformation;
      var verify = info && info.nameVerificationLabel;
      if (verify === "Name Mismatch") return "Name mismatch — document identifies a different faculty";
      if (verify === "Name Not Detected") return "Faculty name not detected on document";
      if (verify === "Needs Manual Review") return "Ownership needs manual review";
      if (source.compositionDisplay === "Needs Classification" || source.classificationStatus === "needs_classification") {
        return "Needs classification";
      }
      if (String(source.ocrStatus || "").toLowerCase() === "failed") return "OCR failed";
      if ((source.totalEvaluationRecords || 0) === 0) return "No SET/SEF semester rows extracted yet";
      return "Document needs review";
    },

    formatPeriodLabel: function (row) {
      var year = (row && row.academicYear) ? String(row.academicYear).trim() : "";
      var sem = (row && row.semester) ? String(row.semester).trim() : "";
      if (!year && !sem) return "—";
      if (year && sem) return year + " · " + sem;
      return year || sem;
    },

    parseRatingParts: function (ratingRaw, ratingScale) {
      var text = ratingRaw == null ? "" : String(ratingRaw).trim();
      var scaleField = ratingScale == null ? "" : String(ratingScale).trim();
      if (!text) {
        return { rating: null, scale: scaleField || null };
      }
      var segments = text.split(/\s*\/\s*/).filter(function (part) {
        return part != null && String(part).trim() !== "";
      }).map(function (part) { return String(part).trim(); });
      if (segments.length >= 2) {
        var ratingPart = segments[0];
        var scalePart = segments[1];
        return {
          rating: ratingPart,
          scale: scaleField || scalePart || null
        };
      }
      return {
        rating: text,
        scale: scaleField || null
      };
    },

    formatExtractedRating: function (row) {
      if (!row) return "—";
      var parts = FL.criterionAWorkspaceUi.parseRatingParts(row.ratingRaw, row.ratingScale);
      if (!parts.rating) return "—";
      if (parts.scale) {
        return parts.rating + " / " + parts.scale;
      }
      return parts.rating;
    },

    facultyNameDisplayMeta: function (row) {
      if (!row) {
        return { label: "—", note: null, needsVerification: false, profileFallback: false };
      }
      var name = row.facultyName != null ? String(row.facultyName).trim() : "";
      if (!name) name = "—";
      return {
        label: name,
        note: row.facultyNameNote || null,
        needsVerification: !!row.needsVerification,
        profileFallback: row.facultyNameSource === "profile",
        verificationLabel: row.nameVerificationLabel || null
      };
    },

    formatFacultyNameLabel: function (row) {
      var meta = FL.criterionAWorkspaceUi.facultyNameDisplayMeta(row);
      if (meta.label === "Not detected" || meta.label === "—") return "Not detected";
      if (meta.profileFallback && meta.label && meta.label !== "—") {
        return meta.label + " (from profile)";
      }
      return meta.label;
    },

    sortEvaluationRecords: function (records) {
      return (records || []).slice().sort(function (a, b) {
        var ya = String(a.academicYear || "");
        var yb = String(b.academicYear || "");
        if (ya !== yb) return ya.localeCompare(yb);
        var sa = String(a.semester || "");
        var sb = String(b.semester || "");
        if (sa !== sb) return sa.localeCompare(sb);
        var ta = String(a.evaluationType || "");
        var tb = String(b.evaluationType || "");
        return ta.localeCompare(tb);
      });
    }
  };
})(typeof window !== "undefined" ? window : global);
