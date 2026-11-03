/**
 * KRA II — shared evidence API (Criterion A journal reference workflow).
 */
window.FL = window.FL || {};

FL.kra2Evidence = {
  bundlePath: function (session, docId) {
    if (!docId) return "";
    if (session && session.role === "reviewer") {
      return "/api/reviewer/documents/" + encodeURIComponent(docId) + "/kra2/evidence-bundle";
    }
    if (session && session.role === "faculty") {
      return "/api/faculty/me/documents/" + encodeURIComponent(docId) + "/kra2/evidence-bundle";
    }
    return "";
  },

  facultySummaryPath: function (session, facultyId, criterionKey) {
    if (!facultyId || !session || session.role !== "reviewer") return "";
    var crit = criterionKey || "kra2-a";
    return "/api/reviewer/me/faculty/" + encodeURIComponent(facultyId) + "/" + crit + "/summary";
  },

  facultyAccomplishmentsPath: function (session, facultyId, criterionKey) {
    if (!facultyId || !session || session.role !== "reviewer") return "";
    var crit = criterionKey || "kra2-a";
    return "/api/reviewer/me/faculty/" + encodeURIComponent(facultyId) + "/" + crit + "/accomplishments";
  },

  _authorizedRequest: function (method, path, body) {
    var client = FL.apiClient;
    if (!client || typeof client.adminRequest !== "function") {
      return Promise.reject(new Error("Sign in required."));
    }
    return client.adminRequest.call(client, method, path, body);
  },

  _withTimeout: function (promise, ms, label) {
    var limit = ms || 25000;
    return Promise.race([
      promise,
      new Promise(function (_resolve, reject) {
        setTimeout(function () {
          reject(new Error((label || "Request") + " timed out. Please try again."));
        }, limit);
      })
    ]);
  },

  fetchBundle: function (session, docId) {
    var path = FL.kra2Evidence.bundlePath(session, docId);
    if (!path || !FL.store.usesLiveDocuments()) {
      return Promise.reject(new Error("KRA II evidence requires a live session."));
    }
    return FL.kra2Evidence._authorizedRequest("GET", path);
  },

  patchBundle: function (session, docId, body) {
    var path = FL.kra2Evidence.bundlePath(session, docId);
    if (!path || !FL.store.usesLiveDocuments()) {
      return Promise.reject(new Error("KRA II updates require a live session."));
    }
    return FL.kra2Evidence._authorizedRequest("PATCH", path, body || {});
  },

  fetchFacultySummary: function (session, facultyId, criterionKey) {
    var path = FL.kra2Evidence.facultySummaryPath(session, facultyId, criterionKey);
    if (!path) return Promise.resolve(null);
    return FL.kra2Evidence._withTimeout(
      FL.kra2Evidence._authorizedRequest("GET", path),
      25000,
      "Summary request"
    );
  },

  fetchFacultyAccomplishments: function (session, facultyId, criterionKey) {
    var path = FL.kra2Evidence.facultyAccomplishmentsPath(session, facultyId, criterionKey);
    if (!path) return Promise.resolve({ accomplishments: [] });
    return FL.kra2Evidence._withTimeout(
      FL.kra2Evidence._authorizedRequest("GET", path).then(function (payload) {
        return payload && payload.accomplishments ? payload : { accomplishments: [] };
      }),
      25000,
      "Accomplishments request"
    );
  }
};
