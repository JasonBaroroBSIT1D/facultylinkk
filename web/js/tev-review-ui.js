/**
 * Plain-language SET/SEF semester review UI helpers (no DOM; testable).
 */
(function (global) {
  "use strict";
  var FL = global.FL = global.FL || {};

  function normalizeStatus(raw) {
    return String(raw || "pending-review").replace(/_/g, "-").toLowerCase();
  }

  FL.tevReviewUi = {
    statusLabel: function (tev) {
      if (!tev) return "Pending Review";
      if (tev.incompleteExtraction || tev.extractionStatus === "partial" || tev.extractionStatus === "ambiguous") {
        return "Incomplete Extraction";
      }
      var s = normalizeStatus(tev.reviewerValidationStatus || tev.reviewDisplayStatus);
      if (s === "approved" || s === "valid" || s === "accepted") return "Validated";
      if (s === "revision" || s === "needs-revision") return "Needs Revision";
      if (s === "rejected") return "Rejected";
      return "Pending Review";
    },

    isReviewed: function (tev) {
      var label = FL.tevReviewUi.statusLabel(tev);
      return label === "Validated" || label === "Rejected" || label === "Needs Revision";
    },

    summaryCounts: function (list) {
      var rows = list || [];
      var out = {
        total: rows.length,
        reviewed: 0,
        pending: 0,
        needsRevision: 0,
        rejected: 0,
        incomplete: 0
      };
      rows.forEach(function (tev) {
        var label = FL.tevReviewUi.statusLabel(tev);
        if (label === "Validated" || label === "Rejected" || label === "Needs Revision") {
          out.reviewed += 1;
        }
        if (label === "Pending Review") out.pending += 1;
        if (label === "Needs Revision") out.needsRevision += 1;
        if (label === "Rejected") out.rejected += 1;
        if (label === "Incomplete Extraction") out.incomplete += 1;
      });
      return out;
    },

    passesFilter: function (tev, filter) {
      var f = (filter || "all").toLowerCase();
      if (f === "all") return true;
      if (f === "set") return (tev.evaluationType || "").toUpperCase() === "SET";
      if (f === "sef") return (tev.evaluationType || "").toUpperCase() === "SEF";
      if (f === "pending") return FL.tevReviewUi.statusLabel(tev) === "Pending Review";
      if (f === "reviewed") return FL.tevReviewUi.isReviewed(tev);
      return true;
    }
  };
})(typeof window !== "undefined" ? window : global);
