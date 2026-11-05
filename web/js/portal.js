/**
 * Live Admin / Reviewer portal aggregates (Flask + PostgreSQL).
 */
window.FL = window.FL || {};

FL.portal = {
  _workspaceVersion: 0,

  bumpWorkspaceVersion: function () {
    this._workspaceVersion += 1;
    return this._workspaceVersion;
  },

  /** Call after assignments, reviews, or schedule publish so open dashboards can refresh. */
  afterWorkspaceMutation: function (session, meta) {
    FL.portal.bumpWorkspaceVersion();
    const page = document.body && document.body.dataset ? document.body.dataset.page : "";
    const promises = [];
    if (page === "admin-dashboard" && FL.admin && FL.admin.renderDashboard) {
      promises.push(Promise.resolve().then(function () { FL.admin.renderDashboard(); }));
    }
    if (page === "reviewer-dashboard" && FL.reviewer && FL.reviewer.renderDashboard) {
      const sess = session || FL.portal._sessionFromStorage();
      promises.push(Promise.resolve().then(function () { FL.reviewer.renderDashboard(sess); }));
    }
    if ((page === "reviewer-documents" || page === "admin-documents") && FL.evidence && FL.evidence.mount) {
      const sess = session || FL.portal._sessionFromStorage();
      promises.push(Promise.resolve().then(function () { FL.evidence.mount(sess); }));
    }
    if (page === "admin-reports" && FL.admin && FL.admin.renderReports) {
      promises.push(Promise.resolve().then(function () { FL.admin.renderReports(); }));
    }
    if (meta && meta.facultyId && FL.store && FL.store.loadEstimatedAssessment) {
      promises.push(FL.store.loadEstimatedAssessment(meta.facultyId).catch(function () { return null; }));
    }
    if (meta && meta.scope === "schedule" && FL.store && FL.store.loadEvaluationPeriods) {
      const sess = session || FL.portal._sessionFromStorage();
      if (sess) {
        promises.push(FL.store.loadEvaluationPeriods(sess).catch(function () { return null; }));
      }
    }
    return promises.length ? Promise.all(promises) : Promise.resolve(null);
  },

  loadSyncHealth: function (session) {
    const role = session && session.role;
    let path = "/api/admin/sync-health";
    if (role === "reviewer") path = "/api/reviewer/me/sync-health";
    else if (role === "faculty") path = "/api/faculty/me/sync-health";
    return FL.apiClient.adminRequest("GET", path);
  },

  loadAdminDashboard: function () {
    return FL.apiClient.adminRequest("GET", "/api/admin/dashboard");
  },

  loadAdminReports: function (params) {
    const qs = new URLSearchParams(params || {});
    return FL.apiClient.adminRequest("GET", "/api/admin/reports?" + qs.toString());
  },

  reportsCsvUrl: function (params) {
    const qs = new URLSearchParams(params || {});
    qs.set("format", "csv");
    const base = FL.apiConfig && FL.apiConfig.baseUrl ? FL.apiConfig.baseUrl : "";
    return base + "/api/admin/reports?" + qs.toString();
  },

  loadAdminAuditLog: function (params) {
    const qs = new URLSearchParams(params || {});
    return FL.apiClient.adminRequest("GET", "/api/admin/audit-log?" + qs.toString());
  },

  loadReviewerDashboard: function () {
    return FL.apiClient.adminRequest("GET", "/api/reviewer/me/dashboard");
  },

  loadNotifications: function (session) {
    const path = session.role === "reviewer"
      ? "/api/reviewer/me/notifications"
      : "/api/admin/notifications";
    return FL.apiClient.adminRequest("GET", path).then(function (data) {
      const rows = (data.notifications || []).map(FL.portal._normalizeNotification);
      FL.store.notifications = rows;
      FL.store.notificationUnreadCount = data.unreadCount != null ? data.unreadCount : rows.filter(function (n) { return !n.read; }).length;
      return rows;
    });
  },

  patchNotification: function (session, id, read) {
    const path = session.role === "reviewer"
      ? "/api/reviewer/me/notifications/" + encodeURIComponent(id)
      : "/api/admin/notifications/" + encodeURIComponent(id);
    return FL.apiClient.adminRequest("PATCH", path, { read: !!read });
  },

  markAllNotifications: function (session, ids, read) {
    const path = session.role === "reviewer"
      ? "/api/reviewer/me/notifications"
      : "/api/admin/notifications";
    return FL.apiClient.adminRequest("PATCH", path, { ids: ids || [], read: read !== false });
  },

  _normalizeNotification: function (row) {
    return {
      id: row.id,
      title: row.title,
      body: row.body,
      at: row.at,
      read: !!row.read,
      ref: row.ref || row.documentId || row.facultyId || "",
      documentId: row.documentId,
      facultyId: row.facultyId,
      audience: row.audience || "administrator",
      userId: row.userId
    };
  },

  statusLabel: function (status) {
    const map = {
      approved: "Approved",
      valid: "Approved",
      pending_review: "Waiting for review",
      "pending-review": "Waiting for review",
      needs_revision: "Needs changes",
      revision: "Needs changes",
      rejected: "Rejected"
    };
    return map[status] || (status || "Unknown");
  },

  reviewHref: function (doc) {
    if (!doc) return "documents.html";
    var id = doc.id || doc.documentId;
    if (!id) return "documents.html";
    var stored = FL.store.documentById(id);
    var merged = stored ? Object.assign({}, stored, doc) : doc;
    if (FL.reviewerNav && FL.reviewerNav.accomplishmentReviewUrl) {
      return FL.reviewerNav.accomplishmentReviewUrl(merged);
    }
    return "documents.html";
  },

  _sessionFromStorage: function () {
    try {
      return JSON.parse(sessionStorage.getItem("facultylink.session") || "null");
    } catch (error) {
      return null;
    }
  }
};
