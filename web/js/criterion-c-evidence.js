/**
 * KRA I Criterion C — reviewer API integration.
 */
window.FL = window.FL || {};

FL.criterionCEvidence = {
  bundlePath: function (session, docId) {
    if (!docId) return "";
    if (session && session.role === "reviewer") {
      return "/api/reviewer/documents/" + encodeURIComponent(docId) + "/criterion-c/evidence-bundle";
    }
    if (session && session.role === "administrator") {
      return "/api/admin/documents/" + encodeURIComponent(docId) + "/criterion-c/evidence-bundle";
    }
    return "";
  },

  facultySummaryPath: function (session, facultyId) {
    if (!facultyId || !session || session.role !== "reviewer") return "";
    return "/api/reviewer/me/faculty/" + encodeURIComponent(facultyId) + "/criterion-c/summary";
  },

  facultyAccomplishmentsPath: function (session, facultyId) {
    if (!facultyId || !session || session.role !== "reviewer") return "";
    return "/api/reviewer/me/faculty/" + encodeURIComponent(facultyId) + "/criterion-c/accomplishments";
  },

  fetchBundle: function (session, docId) {
    var path = FL.criterionCEvidence.bundlePath(session, docId);
    if (!path || !FL.store.usesLiveDocuments()) {
      return Promise.reject(new Error("Criterion C evidence requires a live reviewer session."));
    }
    return FL.apiClient.adminRequest("GET", path);
  },

  patchBundle: function (session, docId, body) {
    var path = FL.criterionCEvidence.bundlePath(session, docId);
    if (!path || !FL.store.usesLiveDocuments()) {
      return Promise.reject(new Error("Criterion C updates require a live reviewer session."));
    }
    if (session.role !== "reviewer") {
      return Promise.reject(new Error("Only assigned reviewers may update Criterion C evidence."));
    }
    return FL.apiClient.adminRequest("PATCH", path, body || {});
  },

  fetchFacultySummary: function (session, facultyId) {
    var path = FL.criterionCEvidence.facultySummaryPath(session, facultyId);
    if (!path) return Promise.resolve(null);
    return FL.apiClient.adminRequest("GET", path);
  },

  fetchFacultyAccomplishments: function (session, facultyId) {
    var path = FL.criterionCEvidence.facultyAccomplishmentsPath(session, facultyId);
    if (!path) return Promise.resolve({ accomplishments: [] });
    return FL.apiClient.adminRequest("GET", path).then(function (payload) {
      return payload && payload.accomplishments ? payload : { accomplishments: [] };
    });
  },

  documentById: function (docId) {
    return FL.store.documentById(docId);
  },

  supportingDocsForPrimary: function (primaryDocId, facultyId) {
    return (FL.store.documents || []).filter(function (d) {
      if (facultyId && d.facultyId !== facultyId) return false;
      var ev = d.criterionCEvidence;
      if (ev && ev.link && ev.link.primaryDocumentId === primaryDocId) return true;
      var link = d.extractedInfo && d.extractedInfo.criterionCEvidenceLink;
      return link && link.role === "supporting" && link.primaryDocumentId === primaryDocId;
    });
  }
};
