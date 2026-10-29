/**
 * FacultyLink store — loads from the frontend mock API (localStorage).
 * Scores are computed in the browser from rules.js and are not official results.
 */
window.FL = window.FL || {};

FL.institution = {
  name: "University of Science and Technology of Southern Philippines",
  campus: "Oroquieta City",
  system: "FacultyLink",
  tagline: "Intelligent Document-Validated Faculty Self-Assessment System",
  circular: "DBM–CHED Joint Circular No. 01, s. 2026 — Faculty Reclassification"
};

FL.seed = {
  users: [],
  faculty: [],
  documents: [],
  notifications: [],
  audit: []
};
FL.clone = function (value) {
  return JSON.parse(JSON.stringify(value));
};

FL.store = {
  documents: [],
  faculty: [],
  notifications: [],
  audit: [],
  users: [],
  evaluationPeriods: [],
  liveAccounts: false,
  serverReviewers: [],
  adminDirectoryLoaded: false,
  adminDirectoryError: null,

  load: function () {
    const store = this;
    const liveSession = !!(FL.apiClient && FL.apiClient.getAccessToken());
    return FL.api.send("GET", "/api/state").then(function (data) {
      if (!liveSession) {
        store.documents = data.documents || [];
        store.faculty = data.faculty || [];
        store.users = data.users || [];
        store.notifications = data.notifications || [];
        store.audit = data.audit || [];
        store.evaluationPeriods = data.evaluationPeriods || [];
      }
      store.kraSettings = data.kraSettings || {};
      if (FL.rules.applySettings) FL.rules.applySettings(data.kraSettings || {});
    });
  },

  saveProfile: function (user) {
    return FL.api.send("PATCH", "/api/profile", {
      office: user.office,
      contact: user.contact,
      specialization: user.specialization
    });
  },

  facultyById: function (id) {
    const fromFaculty = this.faculty.find(function (person) { return person.id === id; });
    if (fromFaculty) return fromFaculty;
    return this.reviewerFaculty.find(function (person) { return person.id === id; }) || null;
  },

  userById: function (id) {
    if (id == null || id === "") return null;
    return this.users.find(function (user) { return user.id === id; }) || null;
  },

  /** Upsert a faculty row returned from POST /api/admin/faculty (real API only). */
  upsertServerFaculty: function (row) {
    if (!row || !row.id) return;
    const normalized = this._normalizeFacultyRow ? this._normalizeFacultyRow(Object.assign({}, row)) : row;
    const email = (normalized.email || "").toLowerCase();
    const idx = this.faculty.findIndex(function (person) {
      return person.id === normalized.id || (email && (person.email || "").toLowerCase() === email);
    });
    if (idx >= 0) Object.assign(this.faculty[idx], normalized);
    else this.faculty.push(normalized);
  },

  /** Upsert a reviewer user returned from POST /api/admin/reviewers (real API only). */
  upsertServerReviewer: function (row) {
    if (!row || !row.id) return;
    const normalized = {
      id: row.id,
      name: row.name || row.fullName || row.email || "Reviewer",
      email: row.email || "",
      role: "reviewer",
      office: row.office || "",
      department: row.department || row.office || "",
      mustChangePassword: !!row.mustChangePassword
    };
    const email = (normalized.email || "").toLowerCase();
    const idx = this.users.findIndex(function (user) {
      return user.id === normalized.id || (email && (user.email || "").toLowerCase() === email);
    });
    if (idx >= 0) {
      Object.assign(this.users[idx], normalized);
    } else {
      this.users.push(normalized);
    }
    const serverIdx = this.serverReviewers.findIndex(function (item) { return item.id === normalized.id; });
    const serverRow = Object.assign({ role: "reviewer", _fromServer: true }, row, normalized);
    if (serverIdx >= 0) Object.assign(this.serverReviewers[serverIdx], serverRow);
    else if (this.usesRealAdminApi()) this.serverReviewers.push(serverRow);
  },

  usesRealAdminApi: function () {
    return !!(FL.apiClient && FL.apiClient.getAccessToken());
  },

  usesLiveReviewerApi: function () {
    return !!(FL.apiClient && FL.apiClient.getAccessToken());
  },

  isLiveAccountManagement: function () {
    return this.usesRealAdminApi();
  },

  reviewerFaculty: [],
  reviewerDirectoryLoaded: false,

  assignedFacultyForReviewer: function (session) {
    if (this.usesLiveReviewerApi() && this.reviewerDirectoryLoaded) {
      return this.reviewerFaculty.slice();
    }
    if (!session || !session.userId) return [];
    return this.faculty.filter(function (person) {
      return String(person.reviewerId) === String(session.userId);
    });
  },

  loadReviewerAssignedFaculty: function () {
    const store = this;
    if (!store.usesLiveReviewerApi()) {
      return Promise.reject(new Error("Sign in required."));
    }
    return FL.apiClient.adminRequest("GET", "/api/reviewer/me/faculty").then(function (data) {
      store.reviewerFaculty = (data.faculty || []).map(function (row) {
        return Object.assign({ _fromServer: true }, row);
      });
      store.reviewerDirectoryLoaded = true;
      return store.reviewerFaculty;
    });
  },

  clearAccountMocksForLiveAdmin: function () {
    if (!this.usesRealAdminApi()) return;
    this.faculty = [];
    this.serverReviewers = [];
    this.users = this.users.filter(function (user) {
      return user.role === "administrator";
    });
    const cached = FL.apiClient && FL.apiClient.cachedUser();
    if (cached && !this.users.some(function (user) { return user.id === cached.id; })) {
      this.users.push(cached);
    }
  },

  _applyFacultyRows: function (rows) {
    this.faculty = (rows || []).map(this._normalizeFacultyRow.bind(this));
  },

  _applyReviewerRows: function (rows) {
    const store = this;
    store.serverReviewers = (rows || []).map(function (row) {
      return Object.assign({ role: "reviewer" }, row, { _fromServer: true });
    });
    const cached = FL.apiClient.cachedUser();
    const admins = store.users.filter(function (user) {
      return user.role === "administrator";
    });
    if (cached && !admins.some(function (admin) { return admin.id === cached.id; })) {
      admins.push(cached);
    }
    store.users = admins.concat(store.serverReviewers);
  },

  loadAdminFaculty: function () {
    const store = this;
    if (!store.usesRealAdminApi()) {
      return Promise.reject(new Error("Sign in required."));
    }
    return FL.apiClient.adminRequest("GET", "/api/admin/faculty").then(function (data) {
      store._applyFacultyRows(data.faculty || []);
      return store.faculty;
    });
  },

  loadAdminReviewers: function () {
    const store = this;
    if (!store.usesRealAdminApi()) {
      return Promise.reject(new Error("Sign in required."));
    }
    return FL.apiClient.adminRequest("GET", "/api/admin/reviewers").then(function (data) {
      store._applyReviewerRows(data.reviewers || []);
      return store.serverReviewers;
    });
  },

  _normalizeFacultyRow: function (row) {
    const copy = Object.assign({}, row);
    copy._fromServer = true;
    if (copy.reviewerId == null) copy.reviewerId = "";
    return copy;
  },

  loadAdminDirectory: function () {
    const store = this;
    if (!store.usesRealAdminApi()) {
      store.liveAccounts = false;
      store.adminDirectoryLoaded = false;
      return Promise.reject(new Error("Sign in required."));
    }
    store.adminDirectoryError = null;
    return Promise.all([
      store.loadAdminFaculty(),
      store.loadAdminReviewers()
    ]).then(function () {
      store.liveAccounts = true;
      store.adminDirectoryLoaded = true;
      return { faculty: store.faculty, reviewers: store.serverReviewers };
    }).catch(function (error) {
      store.adminDirectoryLoaded = false;
      store.adminDirectoryError = error;
      store.liveAccounts = false;
      throw error;
    });
  },

  reviewerById: function (id) {
    if (id == null || id === "") return null;
    const fromUsers = this.userById(id);
    if (fromUsers) return fromUsers;
    return this.serverReviewers.find(function (reviewer) { return reviewer.id === id; }) || null;
  },

  facultyCredentialsId: function (person) {
    return person && (person.userId || person.id);
  },

  documentById: function (id) {
    return this.documents.find(function (doc) { return doc.id === id; }) || null;
  },

  usesLiveDocuments: function () {
    return !!(FL.apiClient && FL.apiClient.getAccessToken());
  },

  _normalizeLiveDocument: function (row) {
    const copy = Object.assign({}, row);
    if (!copy.name && copy.title) copy.name = copy.title;
    const base = FL.apiConfig && FL.apiConfig.baseUrl ? FL.apiConfig.baseUrl : "";
    const path = copy.fileApiPath || copy.fileUrl;
    if (path && path.indexOf("http") !== 0) {
      copy.fileApiPath = path;
      copy.fileUrl = base + path;
    }
    if (!copy.ocr || typeof copy.ocr !== "object") {
      copy.ocr = { status: "pending" };
    }
    if (copy.ocr.status === "complete") copy.ocr.status = "completed";
    if (!copy.ocr.content && copy.ocr.contentPreview) copy.ocr.content = copy.ocr.contentPreview;
    if (!copy.dateSubmitted && copy.submittedAt) copy.dateSubmitted = copy.submittedAt;
    return copy;
  },

  refreshLiveDocument: function (session, docId) {
    const store = this;
    if (!docId) return Promise.resolve(null);
    if (!store.usesLiveDocuments()) return Promise.resolve(store.documentById(docId));
    let path = "/api/admin/documents/" + encodeURIComponent(docId);
    if (session && session.role === "reviewer") {
      path = "/api/reviewer/documents/" + encodeURIComponent(docId);
    }
    return FL.apiClient.adminRequest("GET", path).then(function (row) {
      return store.upsertDocument(row);
    });
  },

  retryDocumentOcr: function (session, docId) {
    const store = this;
    if (!store.usesLiveDocuments() || !docId) {
      return Promise.reject(new Error("OCR retry requires a live API session."));
    }
    let path = "/api/admin/documents/" + encodeURIComponent(docId) + "/ocr/retry";
    if (session && session.role === "reviewer") {
      path = "/api/reviewer/documents/" + encodeURIComponent(docId) + "/ocr/retry";
    } else if (session && session.role === "faculty") {
      path = "/api/faculty/me/documents/" + encodeURIComponent(docId) + "/ocr/retry";
    }
    return FL.apiClient.adminRequest("POST", path, {}).then(function (data) {
      const saved = data.document || data;
      return store.upsertDocument(saved);
    });
  },

  loadFacultyDocuments: function (session, facultyId) {
    const store = this;
    if (!facultyId) return store.loadLiveDocuments(session);
    if (!store.usesLiveDocuments()) {
      return Promise.resolve(store.documents);
    }
    const base = session.role === "reviewer" ? "/api/reviewer/me/documents" : "/api/admin/documents";
    return FL.apiClient.adminRequest("GET", base + "?facultyId=" + encodeURIComponent(facultyId)).then(function (data) {
      const rows = (data.documents || []).map(function (row) { return store._normalizeLiveDocument(row); });
      const others = store.documents.filter(function (d) { return d.facultyId !== facultyId; });
      store.documents = others.concat(rows);
      return store.documents;
    });
  },

  loadLiveDocuments: function (session) {
    const store = this;
    if (!store.usesLiveDocuments()) {
      return Promise.resolve(store.documents);
    }
    store.documents = [];
    let path = "/api/admin/documents";
    if (session && session.role === "reviewer") path = "/api/reviewer/me/documents";
    return FL.apiClient.adminRequest("GET", path).then(function (data) {
      store.documents = (data.documents || []).map(function (row) {
        return store._normalizeLiveDocument(row);
      });
      store.documentStats = data.stats || null;
      store.liveDocumentsLoaded = true;
      return store.documents;
    });
  },

  /** Drop stale SET/SEF rows for one indicator after live folder API returns. */
  syncSetSefIndicatorDocuments: function (facultyId, indicatorId, block) {
    if (!facultyId || !indicatorId || !block || typeof block !== "object") return;
    const rows = block.documents || [];
    const apiIds = {};
    rows.forEach(function (row) {
      const id = row.documentId || row.id;
      if (id) apiIds[id] = true;
    });
    this.documents = this.documents.filter(function (d) {
      if (d.facultyId !== facultyId || d.indicatorId !== indicatorId) return true;
      return !!apiIds[d.id];
    });
  },

  loadLiveDocumentStats: function () {
    if (!this.usesLiveDocuments()) return Promise.resolve(null);
    return FL.apiClient.adminRequest("GET", "/api/admin/documents/stats").then(function (data) {
      return data.stats || null;
    });
  },

  fetchSetSefSimulationPolicy: function () {
    return FL.apiClient.adminRequest("GET", "/api/admin/policies/set-sef-auto-approval");
  },

  saveSetSefSimulationPolicy: function (enabled) {
    return FL.apiClient.adminRequest("PUT", "/api/admin/policies/set-sef-auto-approval", { enabled: !!enabled });
  },

  upsertDocument: function (row) {
    const normalized = this._normalizeLiveDocument(row);
    const idx = this.documents.findIndex(function (doc) { return doc.id === normalized.id; });
    if (idx >= 0) Object.assign(this.documents[idx], normalized);
    else this.documents.unshift(normalized);
    return normalized;
  },

  saveDocument: function (doc, session) {
    const store = this;
    if (store.usesLiveDocuments() && session && session.role === "reviewer") {
      return FL.apiClient.adminRequest("PUT", "/api/reviewer/documents/" + encodeURIComponent(doc.id), doc)
        .then(function (saved) {
          store.upsertDocument(saved);
          Object.assign(doc, saved);
          return saved;
        });
    }
    if (store.usesLiveDocuments() && session && session.role === "administrator") {
      return Promise.resolve(doc);
    }
    return FL.api.send("PUT", "/api/documents/" + encodeURIComponent(doc.id), doc).then(function (saved) {
      if (saved && typeof saved === "object") {
        Object.keys(saved).forEach(function (key) { doc[key] = saved[key]; });
      }
      return saved;
    });
  },

  submitDocumentReview: function (doc, decision, remarks, session) {
    const store = this;
    if (!store.usesLiveDocuments() || !session || session.role !== "reviewer") {
      return Promise.reject(new Error("Live review API is not available."));
    }
    return FL.apiClient.adminRequest(
      "POST",
      "/api/reviewer/documents/" + encodeURIComponent(doc.id) + "/review",
      { decision: decision, remarks: remarks || "" }
    ).then(function (data) {
      const saved = data.document || data;
      store.upsertDocument(saved);
      Object.assign(doc, saved);
      return saved;
    });
  },

  correctDocumentMetadata: function (documentId, payload, session) {
    const store = this;
    if (store.usesLiveDocuments() && session && session.role === "reviewer") {
      return FL.apiClient.adminRequest(
        "POST",
        "/api/reviewer/documents/" + encodeURIComponent(documentId) + "/correct-metadata",
        payload
      ).then(function (data) {
        const saved = data.document || data;
        if (saved && saved.id) store.upsertDocument(saved);
        return saved;
      });
    }
    return FL.api.send("POST", "/api/documents/" + encodeURIComponent(documentId) + "/correct-metadata", payload);
  },

  fetchEvaluationEligibility: function (session, facultyId) {
    const store = this;
    if (!store.usesLiveDocuments() || !facultyId) return Promise.resolve(null);
    if (session.role === "reviewer") {
      return FL.apiClient.adminRequest(
        "GET",
        "/api/reviewer/me/faculty/" + encodeURIComponent(facultyId) + "/evaluation-eligibility"
      );
    }
    if (session.role === "administrator") {
      return FL.apiClient.adminRequest(
        "GET",
        "/api/admin/documents/faculty/" + encodeURIComponent(facultyId) + "/evaluation-eligibility"
      );
    }
    return Promise.resolve(null);
  },

  saveEvaluationEligibility: function (session, facultyId, payload) {
    if (!this.usesLiveDocuments() || !session || session.role !== "reviewer") {
      return Promise.reject(new Error("Only assigned reviewers can update Section 10 eligibility."));
    }
    return FL.apiClient.adminRequest(
      "PUT",
      "/api/reviewer/me/faculty/" + encodeURIComponent(facultyId) + "/evaluation-eligibility",
      payload
    );
  },

  fetchTeachingEffectiveness: function (session, facultyId) {
    const store = this;
    if (!store.usesLiveDocuments() || !facultyId) return Promise.resolve(null);
    const bust = "&_=" + Date.now();
    if (session.role === "reviewer") {
      return FL.apiClient.adminRequest(
        "GET",
        "/api/reviewer/me/teaching-effectiveness?facultyId=" + encodeURIComponent(facultyId) + bust
      );
    }
    if (session.role === "administrator") {
      return FL.apiClient.adminRequest(
        "GET",
        "/api/admin/documents/faculty/" + encodeURIComponent(facultyId) + "/teaching-effectiveness" + bust
      );
    }
    return Promise.resolve(null);
  },

  /** Remove SET/SEF rows from the in-memory store when live API reports none. */
  pruneSetSefDocumentsFromTeachingPayload: function (facultyId, payload) {
    if (!facultyId || !payload || typeof payload !== "object") return;
    const setUploads = ((payload.set || {}).coverageSummary || {}).totalUploads || 0;
    const sefUploads = ((payload.sef || {}).coverageSummary || {}).totalUploads || 0;
    const setIds = payload.set && payload.set.documents ? payload.set.documents.map(function (r) {
      return r.documentId;
    }) : [];
    const sefIds = payload.sef && payload.sef.documents ? payload.sef.documents.map(function (r) {
      return r.documentId;
    }) : [];
    const allowed = {};
    setIds.concat(sefIds).forEach(function (id) { if (id) allowed[id] = true; });
    this.documents = this.documents.filter(function (d) {
      if (d.facultyId !== facultyId) return true;
      if (d.indicatorId !== "kra1-a-student" && d.indicatorId !== "kra1-a-supervisor") return true;
      if (setUploads === 0 && sefUploads === 0) return false;
      return !!allowed[d.id];
    });
  },

  fetchSetSefIndicator: function (session, facultyId, indicatorId) {
    const store = this;
    if (!store.usesLiveDocuments() || !facultyId || !indicatorId) return Promise.resolve(null);
    const bust = "&_=" + Date.now();
    if (session.role === "reviewer") {
      return FL.apiClient.adminRequest(
        "GET",
        "/api/reviewer/me/set-sef-indicator?facultyId=" + encodeURIComponent(facultyId)
          + "&indicatorId=" + encodeURIComponent(indicatorId) + bust
      );
    }
    if (session.role === "administrator") {
      return FL.apiClient.adminRequest(
        "GET",
        "/api/admin/documents/faculty/" + encodeURIComponent(facultyId) + "/set-sef-indicator?indicatorId="
          + encodeURIComponent(indicatorId) + bust
      );
    }
    return Promise.resolve(null);
  },

  assignReviewer: function (facultyId, reviewerId) {
    const store = this;
    const person = this.facultyById(facultyId);
    if (!person) return Promise.reject(new Error("Faculty was not found."));
    const nextId = reviewerId == null || reviewerId === "" ? null : String(reviewerId);
    if (store.usesRealAdminApi()) {
      return store.assignFacultyReviewer(facultyId, nextId);
    }
    person.reviewerId = nextId || "";
    store.documents.forEach(function (doc) {
      if (doc.facultyId === facultyId && (doc.status === "pending-review" || doc.status === "reviewer-required" || doc.status === "invalid")) {
        doc.reviewerId = nextId || "";
      }
    });
    return FL.api.send("POST", "/api/faculty/" + encodeURIComponent(facultyId) + "/reviewer", {
      reviewerId: nextId
    });
  },

  assignFacultyReviewer: function (facultyId, reviewerId) {
    const store = this;
    return FL.apiClient.adminRequest(
      "PATCH",
      "/api/admin/faculty/" + encodeURIComponent(facultyId) + "/reviewer",
      { reviewerId: reviewerId }
    ).then(function (data) {
      if (data.faculty) store.upsertServerFaculty(data.faculty);
      return data;
    });
  },

  fetchAdminFacultyDetail: function (facultyId) {
    return FL.apiClient.adminRequest("GET", "/api/admin/faculty/" + encodeURIComponent(facultyId));
  },

  fetchReviewerWork: function (reviewerId) {
    return FL.apiClient.adminRequest("GET", "/api/admin/reviewers/" + encodeURIComponent(reviewerId) + "/work");
  },

  syncReviewerFacultyAssignments: function (reviewerId, facultyIds, confirmReassign) {
    const store = this;
    return FL.apiClient.adminRequest(
      "PUT",
      "/api/admin/reviewers/" + encodeURIComponent(reviewerId) + "/faculty-assignments",
      { facultyIds: facultyIds, confirmReassign: !!confirmReassign }
    ).then(function (data) {
      if (data.reviewer) store.upsertServerReviewer(data.reviewer);
      return store.refreshAdminDirectory().then(function () { return data; });
    });
  },

  refreshAdminDirectory: function () {
    return Promise.all([this.loadAdminFaculty(), this.loadAdminReviewers()]);
  },

  deactivateAccount: function (userPublicId) {
    return FL.apiClient.adminRequest(
      "POST",
      "/api/admin/users/" + encodeURIComponent(userPublicId) + "/deactivate"
    );
  },

  reactivateAccount: function (userPublicId) {
    return FL.apiClient.adminRequest(
      "POST",
      "/api/admin/users/" + encodeURIComponent(userPublicId) + "/reactivate"
    );
  },

  createFaculty: function (payload) {
    const store = this;
    const body = Object.assign({}, payload);
    delete body.password;
    if (FL.apiClient && FL.apiClient.getAccessToken()) {
      return FL.apiClient.adminRequest("POST", "/api/admin/faculty", body);
    }
    return FL.api.send("POST", "/api/faculty", payload).then(function (data) {
      return store.load().then(function () { return data; });
    });
  },

  reissueFacultyCredentials: function (facultyId) {
    if (FL.apiClient && FL.apiClient.getAccessToken()) {
      const person = this.facultyById(facultyId);
      const userPublicId = person ? this.facultyCredentialsId(person) : facultyId;
      return FL.apiClient.adminRequest(
        "POST",
        "/api/admin/users/" + encodeURIComponent(userPublicId) + "/resend-credentials"
      );
    }
    return FL.api.send("POST", "/api/faculty/" + encodeURIComponent(facultyId) + "/credentials");
  },

  removeFaculty: function (facultyId) {
    const store = this;
    const person = store.facultyById(facultyId);
    if (store.usesRealAdminApi()) {
      const userId = person ? store.facultyCredentialsId(person) : facultyId;
      return store.deactivateAccount(userId).then(function () {
        return store.loadAdminFaculty();
      });
    }
    return FL.api.send("DELETE", "/api/faculty/" + encodeURIComponent(facultyId)).then(function (data) {
      return store.load().then(function () { return data; });
    });
  },

  createReviewer: function (payload) {
    const store = this;
    const body = Object.assign({}, payload);
    delete body.password;
    if (FL.apiClient && FL.apiClient.getAccessToken()) {
      return FL.apiClient.adminRequest("POST", "/api/admin/reviewers", body);
    }
    return FL.api.send("POST", "/api/reviewers", payload).then(function (data) {
      return store.load().then(function () { return data; });
    });
  },

  reissueReviewerCredentials: function (reviewerId) {
    if (FL.apiClient && FL.apiClient.getAccessToken()) {
      return FL.apiClient.adminRequest(
        "POST",
        "/api/admin/users/" + encodeURIComponent(reviewerId) + "/resend-credentials"
      );
    }
    return FL.api.send("POST", "/api/reviewers/" + encodeURIComponent(reviewerId) + "/credentials");
  },

  removeReviewer: function (reviewerId) {
    const store = this;
    if (store.usesRealAdminApi()) {
      return store.deactivateAccount(reviewerId).then(function () {
        return store.loadAdminReviewers();
      });
    }
    return FL.api.send("DELETE", "/api/reviewers/" + encodeURIComponent(reviewerId)).then(function (data) {
      return store.load().then(function () { return data; });
    });
  },

  addNotification: function (item) {
    this.notifications.unshift(item);
    return FL.api.send("POST", "/api/notifications", item);
  },

  loadKraConfigurationDraft: function () {
    const store = this;
    if (!store.usesRealAdminApi()) return Promise.resolve(null);
    return FL.apiClient.adminRequest("GET", "/api/admin/kra-configuration/draft").then(function (data) {
      const ks = (data.draft && data.draft.kraSettings) || null;
      if (ks) {
        store.kraSettings = ks;
        FL.rules.applySettings(ks);
      }
      store.kraConfigurationDraft = data.draft || null;
      store.kraConfigurationPublishedSummary = data.publishedSummary || null;
      return data;
    });
  },

  loadPublishedKraConfiguration: function () {
    const store = this;
    if (store.usesRealAdminApi()) {
      return FL.apiClient.adminRequest("GET", "/api/admin/kra-configuration/published").then(function (data) {
        if (data.kraSettings) {
          store.kraSettings = data.kraSettings;
          FL.rules.applySettings(data.kraSettings);
        }
        store.kraConfigurationPublished = data.published || null;
        return data;
      });
    }
    if (store.usesLiveReviewerApi()) {
      return FL.apiClient.adminRequest("GET", "/api/reviewer/kra-configuration").then(function (data) {
        if (data.kraSettings) {
          store.kraSettings = data.kraSettings;
          FL.rules.applySettings(data.kraSettings);
        }
        store.kraConfigurationPublished = data.published || null;
        return data;
      });
    }
    return Promise.resolve(null);
  },

  loadKraConfigurationVersions: function () {
    if (!this.usesRealAdminApi()) return Promise.resolve({ versions: [] });
    return FL.apiClient.adminRequest("GET", "/api/admin/kra-configuration/versions");
  },

  saveKraSettings: function (settings, metadata) {
    const store = this;
    if (store.usesRealAdminApi()) {
      return FL.apiClient.adminRequest("PUT", "/api/admin/kra-configuration/draft", {
        kraSettings: settings,
        metadata: metadata || store.kraConfigurationDraftMetadata || {}
      }).then(function (data) {
        const ks = data.kraSettings || (data.draft && data.draft.kraSettings) || settings;
        store.kraSettings = ks;
        store.kraConfigurationDraft = data.draft || null;
        FL.rules.applySettings(ks);
        return data;
      });
    }
    return FL.api.send("PUT", "/api/kra-settings", settings).then(function (data) {
      store.kraSettings = data.kraSettings || settings;
      FL.rules.applySettings(data.kraSettings || settings);
      return data;
    });
  },

  validateKraPublish: function (publishPayload) {
    if (!this.usesRealAdminApi()) {
      return Promise.reject(new Error("Publishing validation requires a signed-in administrator account."));
    }
    return FL.apiClient.adminRequest("POST", "/api/admin/kra-configuration/validate-publish", publishPayload || {});
  },

  publishKraConfiguration: function (publishPayload) {
    const store = this;
    if (!store.usesRealAdminApi()) {
      return Promise.reject(new Error("Publishing requires a signed-in administrator account."));
    }
    return FL.apiClient.adminRequest("POST", "/api/admin/kra-configuration/publish", publishPayload || {}).then(function (data) {
      store.kraConfigurationPublished = data.published || null;
      store.kraConfigurationPublishedSummary = data.published
        ? {
            id: data.published.id,
            version: data.published.metadata && data.published.metadata.version,
            publishedAt: data.published.publishedAt,
            effectiveFrom: data.published.metadata && data.published.metadata.effectiveFrom
          }
        : null;
      return data;
    });
  },

  saveEvaluationPeriods: function (periods) {
    const store = this;
    return FL.api.send("PUT", "/api/evaluation-periods", { periods: periods }).then(function (data) {
      store.evaluationPeriods = data.evaluationPeriods || periods;
      return data;
    });
  },

  addAudit: function (entry) {
    this.audit.unshift(entry);
    return FL.api.send("POST", "/api/audit", entry);
  }
};

