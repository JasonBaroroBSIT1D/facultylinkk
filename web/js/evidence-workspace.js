/**
 * FacultyLink Evidence Workspace — admin & reviewer document management UI.
 */
window.FL = window.FL || {};

FL.evidence = {
  statusBadge: function (status) {
    return FL.docFolders.statusBadge(status);
  },

  initials: function (name) {
    const parts = String(name || "?").trim().split(/\s+/);
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  },

  parseLocation: function () {
    const params = new URLSearchParams(window.location.search);
    return {
      facultyId: params.get("faculty") || "",
      kraId: params.get("kra") || "",
      criterionId: params.get("criterion") || "",
      indicatorId: params.get("indicator") || "",
      docFilter: params.get("filter") || "all",
      page: Math.max(1, parseInt(params.get("page") || "1", 10) || 1),
      pageSize: parseInt(params.get("pageSize") || "20", 10) || 20,
      q: params.get("q") || "",
      department: params.get("department") || "",
      reviewerId: params.get("reviewerId") || "",
      sort: params.get("sort") || "name"
    };
  },

  pushLocation: function (patch) {
    const next = Object.assign(FL.evidence.parseLocation(), patch || {});
    const params = new URLSearchParams();
    if (next.q) params.set("q", next.q);
    if (next.department) params.set("department", next.department);
    if (next.reviewerId) params.set("reviewerId", next.reviewerId);
    if (next.sort && next.sort !== "name") params.set("sort", next.sort);
    if (next.page > 1) params.set("page", String(next.page));
    if (next.pageSize !== 20) params.set("pageSize", String(next.pageSize));
    if (next.docFilter && next.docFilter !== "all") params.set("filter", next.docFilter);
    if (next.facultyId) params.set("faculty", next.facultyId);
    if (next.kraId) params.set("kra", next.kraId);
    if (next.criterionId) params.set("criterion", next.criterionId);
    if (next.indicatorId) params.set("indicator", next.indicatorId);
    const qs = params.toString();
    const path = window.location.pathname;
    window.history.replaceState(null, "", qs ? path + "?" + qs : path);
  },

  mount: function (session, options) {
    const opts = options || {};
    const isAdmin = session.role === "administrator";
    const state = FL.evidence.parseLocation();
    if (opts.initialFilter) state.docFilter = opts.initialFilter;
    const page = document.getElementById("page");
    page.innerHTML = FL.ui.loading("Loading Evidence Workspace…");

    const finish = function () {
      FL.evidence._render(session, state, isAdmin);
    };

    const jobs = [FL.evidence._loadStats(session, isAdmin)];
    if (!state.facultyId && state.docFilter === "all") {
      jobs.push(FL.evidence._loadDirectory(session, state, isAdmin));
    } else {
      if (state.facultyId) jobs.push(FL.store.loadFacultyDocuments(session, state.facultyId));
      else jobs.push(FL.store.loadLiveDocuments(session));
    }
    Promise.all(jobs).then(finish).catch(function (err) {
      page.innerHTML = FL.ui.empty("Workspace unavailable", err.message || "Could not load evidence data.");
    });
  },

  _loadStats: function (session, isAdmin) {
    if (!FL.store.usesLiveDocuments()) {
      FL.evidence._mockStats(session, isAdmin);
      return Promise.resolve();
    }
    const path = isAdmin ? "/api/admin/documents/workspace" : "/api/reviewer/me/documents/workspace";
    return FL.apiClient.adminRequest("GET", path).then(function (data) {
      FL.store.evidenceStats = data.stats || {};
    });
  },

  _mockStats: function (session, isAdmin) {
    const docs = FL.documents.scoped(session);
    const facultyIds = {};
    docs.forEach(function (d) { if (d.facultyId) facultyIds[d.facultyId] = true; });
    FL.store.evidenceStats = {
      totalFaculty: isAdmin ? FL.store.faculty.length : FL.store.assignedFacultyForReviewer(session).length,
      facultyWithDocuments: Object.keys(facultyIds).length,
      totalDocuments: docs.length,
      pendingReview: docs.filter(function (d) { return d.status === "pending-review" || d.status === "reviewer-required"; }).length,
      approvedEvidence: docs.filter(function (d) { return d.status === "approved"; }).length,
      needsRevision: docs.filter(function (d) { return d.status === "revision"; }).length
    };
  },

  _loadDirectory: function (session, state, isAdmin) {
    if (!FL.store.usesLiveDocuments()) {
      return FL.evidence._mockDirectory(session, state, isAdmin);
    }
    const qs = new URLSearchParams({
      page: String(state.page),
      pageSize: String(state.pageSize),
      sort: state.sort
    });
    if (state.q) qs.set("q", state.q);
    if (state.department) qs.set("department", state.department);
    if (state.reviewerId && isAdmin) qs.set("reviewerId", state.reviewerId);
    const path = (isAdmin ? "/api/admin/documents/faculty-directory?" : "/api/reviewer/me/documents/faculty-directory?") + qs.toString();
    return FL.apiClient.adminRequest("GET", path).then(function (data) {
      FL.store.evidenceDirectory = data;
      (data.faculty || []).forEach(function (row) {
        if (row && row.id) FL.store.upsertServerFaculty(row);
      });
    });
  },

  _mockDirectory: function (session, state, isAdmin) {
    let rows = isAdmin ? FL.store.faculty.slice() : FL.store.assignedFacultyForReviewer(session);
    const q = state.q.trim().toLowerCase();
    if (q) {
      rows = rows.filter(function (p) {
        return [p.name, p.email, p.employeeNo, p.department].join(" ").toLowerCase().indexOf(q) !== -1;
      });
    }
    rows = rows.map(function (p) {
      const docs = FL.store.documents.filter(function (d) { return d.facultyId === p.id; });
      const pending = docs.filter(function (d) {
        return d.status === "pending-review" || d.status === "reviewer-required" || d.status === "invalid";
      }).length;
      const reviewer = FL.store.reviewerById(p.reviewerId);
      return {
        id: p.id,
        name: p.name,
        email: p.email,
        employeeNo: p.employeeNo || "",
        department: p.department || "",
        reviewerId: p.reviewerId,
        reviewerName: reviewer ? reviewer.name : "",
        documentTotal: docs.length,
        documentPending: pending,
        documentApproved: docs.filter(function (d) { return d.status === "approved"; }).length,
        documentRevision: docs.filter(function (d) { return d.status === "revision"; }).length,
        lastActivity: docs[0] && (docs[0].submittedAt || docs[0].uploadedAt) || null
      };
    });
    if (state.sort === "pending") rows.sort(function (a, b) { return b.documentPending - a.documentPending; });
    else if (state.sort === "documents") rows.sort(function (a, b) { return b.documentTotal - a.documentTotal; });
    else rows.sort(function (a, b) { return a.name.localeCompare(b.name); });
    const total = rows.length;
    const start = (state.page - 1) * state.pageSize;
    FL.store.evidenceDirectory = {
      faculty: rows.slice(start, start + state.pageSize),
      pagination: {
        page: state.page,
        pageSize: state.pageSize,
        total: total,
        totalPages: Math.max(1, Math.ceil(total / state.pageSize))
      }
    };
    return Promise.resolve();
  },

  _render: function (session, state, isAdmin) {
    const stats = FL.store.evidenceStats || {};
    const page = document.getElementById("page");
    const inFolder = !!(state.facultyId || state.kraId || state.indicatorId);
    const pendingMode = state.docFilter !== "all" && !inFolder;

    page.innerHTML = `
      <div class="evidence-workspace">
        <header class="evidence-head">
          <div>
            <p class="eyebrow">FacultyLink</p>
            <h1>Evidence Workspace</h1>
            <p class="lede">${isAdmin
              ? "Monitor and organize faculty supporting documents."
              : "Review evidence for faculty assigned to you."}</p>
          </div>
          <nav class="evidence-crumb" id="evidence-crumb" aria-label="Breadcrumb"></nav>
        </header>
        <div class="evidence-stats" id="evidence-stats"></div>
        <div class="evidence-toolbar">
          <div class="evidence-filters" role="tablist">
            ${FL.evidence._filterTabs(state.docFilter)}
          </div>
          ${pendingMode ? "" : `<label class="search evidence-search"><span class="sr-only">Search faculty</span>
            <input id="evidence-search" type="search" placeholder="Search name, email, or employee ID" value="${FL.esc(state.q)}"></label>`}
        </div>
        <div class="evidence-body card" id="evidence-body"></div>
      </div>`;

    FL.evidence._paintStats(stats, isAdmin);
    FL.evidence._paintCrumb(state, isAdmin, session);
    if (pendingMode) FL.evidence._paintPendingList(session, state, isAdmin);
    else if (state.indicatorId && state.facultyId) FL.evidence._paintIndicatorDocs(session, state, isAdmin);
    else if (state.kraId && state.facultyId) FL.evidence._paintCriteria(session, state, isAdmin);
    else if (state.facultyId) FL.evidence._paintKraGrid(session, state, isAdmin);
    else FL.evidence._paintDirectory(session, state, isAdmin);

    page.querySelectorAll("[data-doc-filter]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        state.docFilter = btn.getAttribute("data-doc-filter");
        state.facultyId = "";
        state.kraId = "";
        state.criterionId = "";
        state.indicatorId = "";
        state.page = 1;
        FL.evidence.pushLocation(state);
        FL.evidence.mount(session);
      });
    });

    const search = document.getElementById("evidence-search");
    if (search) {
      let timer;
      search.addEventListener("input", function () {
        clearTimeout(timer);
        timer = setTimeout(function () {
          state.q = search.value.trim();
          state.page = 1;
          FL.evidence.pushLocation(state);
          FL.evidence._loadDirectory(session, state, isAdmin).then(function () {
            FL.evidence._paintDirectory(session, state, isAdmin);
          });
        }, 280);
      });
    }
  },

  _filterTabs: function (active) {
    const tabs = [
      ["all", "All documents"],
      ["pending-review", "Pending review"],
      ["revision", "Needs revision"],
      ["approved", "Approved"],
      ["rejected", "Rejected"]
    ];
    return tabs.map(function (pair) {
      const sel = pair[0] === active ? " is-active" : "";
      const hot = pair[0] === "pending-review" ? " evidence-filter-hot" : "";
      return `<button type="button" class="evidence-filter${sel}${hot}" data-doc-filter="${pair[0]}" role="tab">${FL.esc(pair[1])}</button>`;
    }).join("");
  },

  _paintStats: function (stats, isAdmin) {
    const host = document.getElementById("evidence-stats");
    if (!host) return;
    const cards = isAdmin
      ? [
          ["Faculty w/ docs", stats.facultyWithDocuments ?? "—"],
          ["Total documents", stats.totalDocuments ?? "—"],
          ["Pending review", stats.pendingReview ?? "—"],
          ["Approved", stats.approvedEvidence ?? "—"],
          ["Needs revision", stats.needsRevision ?? "—"]
        ]
      : [
          ["Assigned faculty", stats.assignedFaculty ?? stats.facultyWithDocuments ?? "—"],
          ["Pending review", stats.pendingReview ?? "—"],
          ["Approved", stats.approvedEvidence ?? "—"],
          ["Needs revision", stats.needsRevision ?? "—"]
        ];
    host.innerHTML = cards.map(function (c) {
      return `<div class="evidence-stat"><span>${FL.esc(c[0])}</span><strong>${FL.esc(String(c[1]))}</strong></div>`;
    }).join("");
  },

  _paintCrumb: function (state, isAdmin, session) {
    const host = document.getElementById("evidence-crumb");
    if (!host) return;
    const parts = [{ label: isAdmin ? "All faculty" : "Assigned faculty", go: { facultyId: "", kraId: "", criterionId: "", indicatorId: "" } }];
    if (state.facultyId) {
      const person = FL.store.facultyById(state.facultyId) || { name: state.facultyId };
      parts.push({ label: person.name, go: { facultyId: state.facultyId, kraId: "", criterionId: "", indicatorId: "" } });
    }
    if (state.kraId) {
      const kra = FL.rules.findKra(state.kraId);
      parts.push({ label: kra ? kra.code : state.kraId, go: { facultyId: state.facultyId, kraId: state.kraId, criterionId: "", indicatorId: "" } });
    }
    if (state.criterionId) {
      parts.push({ label: state.criterionId, go: { facultyId: state.facultyId, kraId: state.kraId, criterionId: state.criterionId, indicatorId: "" } });
    }
    if (state.indicatorId) {
      const hit = FL.rules.findIndicator(state.indicatorId);
      parts.push({ label: hit ? hit.indicator.name : state.indicatorId, go: null });
    }
    host.innerHTML = parts.map(function (part, i) {
      const sep = i ? " › " : "";
      if (!part.go) return sep + `<span>${FL.esc(part.label)}</span>`;
      return sep + `<button type="button" class="evidence-crumb-link" data-crumb='${FL.esc(JSON.stringify(part.go))}'>${FL.esc(part.label)}</button>`;
    }).join("");
    host.querySelectorAll(".evidence-crumb-link").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const go = JSON.parse(btn.getAttribute("data-crumb"));
        Object.assign(state, go);
        FL.evidence.pushLocation(state);
        FL.evidence.mount(session);
      });
    });
  },

  _paintDirectory: function (session, state, isAdmin) {
    const host = document.getElementById("evidence-body");
    const data = FL.store.evidenceDirectory || { faculty: [], pagination: { page: 1, totalPages: 1, total: 0 } };
    const rows = data.faculty || [];
    if (!rows.length) {
      host.innerHTML = FL.ui.empty("No faculty found", "Try another search or filter.");
      return;
    }
    host.innerHTML = `
      <div class="evidence-dir-toolbar">
        <label class="filter"><span>Sort</span>
          <select id="evidence-sort">
            <option value="name">Name</option>
            <option value="pending">Pending count</option>
            <option value="documents">Document count</option>
            <option value="activity">Recent activity</option>
          </select>
        </label>
        <label class="filter"><span>Per page</span>
          <select id="evidence-page-size">
            <option value="20">20</option>
            <option value="50">50</option>
            <option value="100">100</option>
          </select>
        </label>
        <p class="evidence-result-count">${FL.esc(String(data.pagination.total))} faculty</p>
      </div>
      <div class="table-wrap">
        <table class="data evidence-directory">
          <thead><tr>
            <th>Faculty</th><th>Department</th><th>Reviewer</th><th>Documents</th><th>Pending</th><th>Last activity</th><th></th>
          </tr></thead>
          <tbody>
            ${rows.map(function (row) {
              return `<tr>
                <td><div class="evidence-person"><span class="evidence-avatar">${FL.esc(FL.evidence.initials(row.name))}</span>
                  <span><strong>${FL.esc(row.name)}</strong><small>${FL.esc(row.employeeNo || row.email || "")}</small></span></div></td>
                <td>${FL.esc(row.department || "—")}</td>
                <td>${FL.esc(row.reviewerName || "Unassigned")}</td>
                <td>${FL.esc(String(row.documentTotal || 0))}</td>
                <td>${row.documentPending ? FL.ui.badge("pending", String(row.documentPending)) : "0"}</td>
                <td>${FL.esc(row.lastActivity ? FL.formatWhen(row.lastActivity) : "—")}</td>
                <td class="action-cell"><button type="button" class="btn btn-small btn-primary" data-open-faculty="${FL.esc(row.id)}">Open folder</button></td>
              </tr>`;
            }).join("")}
          </tbody>
        </table>
      </div>
      <div class="evidence-pagination" id="evidence-pagination"></div>`;

    const sortSel = document.getElementById("evidence-sort");
    const sizeSel = document.getElementById("evidence-page-size");
    if (sortSel) sortSel.value = state.sort;
    if (sizeSel) sizeSel.value = String(state.pageSize);
    sortSel.addEventListener("change", function () {
      state.sort = sortSel.value;
      state.page = 1;
      FL.evidence.pushLocation(state);
      FL.evidence._loadDirectory(session, state, isAdmin).then(function () {
        FL.evidence._paintDirectory(session, state, isAdmin);
      });
    });
    sizeSel.addEventListener("change", function () {
      state.pageSize = parseInt(sizeSel.value, 10);
      state.page = 1;
      FL.evidence.pushLocation(state);
      FL.evidence._loadDirectory(session, state, isAdmin).then(function () {
        FL.evidence._paintDirectory(session, state, isAdmin);
      });
    });

    host.querySelectorAll("[data-open-faculty]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        state.facultyId = btn.getAttribute("data-open-faculty");
        state.kraId = "";
        state.criterionId = "";
        state.indicatorId = "";
        FL.evidence.pushLocation(state);
        FL.evidence.mount(session);
      });
    });

    FL.evidence._paintPagination(data.pagination, session, state, isAdmin);
    FL.responsive.labelTables(host);
  },

  _paintPagination: function (pagination, session, state, isAdmin) {
    const host = document.getElementById("evidence-pagination");
    if (!host || !pagination) return;
    const page = pagination.page || 1;
    const totalPages = pagination.totalPages || 1;
    host.innerHTML = `
      <button type="button" class="btn btn-ghost btn-small" ${page <= 1 ? "disabled" : ""} data-page="${page - 1}">Previous</button>
      <span>Page ${page} of ${totalPages}</span>
      <button type="button" class="btn btn-ghost btn-small" ${page >= totalPages ? "disabled" : ""} data-page="${page + 1}">Next</button>`;
    host.querySelectorAll("[data-page]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        state.page = parseInt(btn.getAttribute("data-page"), 10);
        FL.evidence.pushLocation(state);
        FL.evidence._loadDirectory(session, state, isAdmin).then(function () {
          FL.evidence._paintDirectory(session, state, isAdmin);
        });
      });
    });
  },

  _facultyDocs: function (session, facultyId) {
    return FL.store.documents.filter(function (d) { return d.facultyId === facultyId; });
  },

  _paintKraGrid: function (session, state, isAdmin) {
    const host = document.getElementById("evidence-body");
    const docs = FL.evidence._facultyDocs(session, state.facultyId);
    host.innerHTML = `<div class="evidence-kra-grid">${FL.rules.kras.map(function (kra) {
      const stats = FL.docFolders.kraStats(docs, kra.id);
      const critCount = kra.criteria.length;
      const icon = FL.kraConfig && FL.kraConfig.icons[kra.id] ? FL.kraConfig.icons[kra.id] : "";
      const pct = stats.total ? Math.round((stats.approved / stats.total) * 100) : 0;
      return `<article class="evidence-kra-card">
        <button type="button" class="evidence-kra-open" data-kra="${FL.esc(kra.id)}">
          <span class="evidence-kra-icon">${icon}</span>
          <h3>${FL.esc(kra.code)}</h3>
          <p>${FL.esc(kra.name)}</p>
          <ul class="evidence-kra-meta">
            <li>${critCount} criteria</li>
            <li>${stats.total} files</li>
            <li>${stats.pending} pending</li>
          </ul>
          <div class="evidence-progress" aria-hidden="true"><span style="width:${pct}%"></span></div>
        </button>
      </article>`;
    }).join("")}</div>`;
    host.querySelectorAll("[data-kra]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        state.kraId = btn.getAttribute("data-kra");
        state.criterionId = "";
        state.indicatorId = "";
        FL.evidence.pushLocation(state);
        FL.evidence.mount(session);
      });
    });
  },

  _paintCriteria: function (session, state, isAdmin) {
    const host = document.getElementById("evidence-body");
    const kra = FL.rules.findKra(state.kraId);
    const docs = FL.evidence._facultyDocs(session, state.facultyId).filter(function (d) { return d.kraId === state.kraId; });
    if (!kra) {
      host.innerHTML = FL.ui.empty("KRA not found", "");
      return;
    }
    if (!state.criterionId) {
      host.innerHTML = kra.criteria.map(function (criterion) {
        const count = docs.filter(function (d) { return d.criterionId === criterion.id; }).length;
        return `<article class="evidence-criterion-card">
          <button type="button" class="evidence-criterion-open" data-criterion="${FL.esc(criterion.id)}">
            <h3>${FL.esc(criterion.name)}</h3>
            <p>${count} document${count === 1 ? "" : "s"}</p>
          </button>
        </article>`;
      }).join("");
      host.querySelectorAll("[data-criterion]").forEach(function (btn) {
        btn.addEventListener("click", function () {
          state.criterionId = btn.getAttribute("data-criterion");
          FL.evidence.pushLocation(state);
          FL.evidence.mount(session);
        });
      });
      return;
    }
    const criterion = kra.criteria.find(function (c) { return c.id === state.criterionId; });
    if (!criterion) return;
    host.innerHTML = `<div class="evidence-indicator-list">${criterion.indicators.map(function (indicator) {
      const idocs = docs.filter(function (d) { return d.indicatorId === indicator.id; });
      return `<button type="button" class="evidence-ind-open" data-indicator="${FL.esc(indicator.id)}">
        <span>${FL.esc(indicator.name)}</span>
        <small>${idocs.length} file${idocs.length === 1 ? "" : "s"}</small>
      </button>`;
    }).join("")}</div>`;
    host.querySelectorAll("[data-indicator]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        state.indicatorId = btn.getAttribute("data-indicator");
        FL.evidence.pushLocation(state);
        FL.evidence.mount(session);
      });
    });
  },

  _paintIndicatorDocs: function (session, state, isAdmin) {
    if (!state.indicatorId && state.criterionId) {
      FL.evidence._paintCriteria(session, state, isAdmin);
      return;
    }
    const host = document.getElementById("evidence-body");
    const hit = FL.rules.findIndicator(state.indicatorId);
    const docs = FL.evidence._facultyDocs(session, state.facultyId).filter(function (d) {
      return d.kraId === state.kraId && d.criterionId === state.criterionId && d.indicatorId === state.indicatorId;
    });
    const reviewBase = isAdmin ? "document-view.html" : "document-review.html";
    host.innerHTML = `
      ${hit ? `<div class="evidence-indicator-head"><h2>${FL.esc(hit.indicator.name)}</h2>
        ${hit.indicator.evidence && hit.indicator.evidence.length ? `<p class="sub">Required: ${FL.esc(hit.indicator.evidence.join("; "))}</p>` : ""}</div>` : ""}
      <div class="evidence-file-grid">${docs.map(function (doc) {
        const href = reviewBase + "?id=" + encodeURIComponent(doc.id);
        const action = isAdmin ? "Monitor" : "Review document";
        return `<article class="evidence-file-card">
          <div class="evidence-file-type">${/pdf/i.test(doc.fileName || "") ? "PDF" : "IMG"}</div>
          <div><strong>${FL.esc(doc.name || doc.fileName)}</strong>
            <p class="sub">${FL.esc(doc.submittedAt || "—")}</p>${FL.evidence.statusBadge(doc.status)}</div>
          <a class="btn btn-small btn-primary" href="${href}">${FL.esc(action)}</a>
        </article>`;
      }).join("") || FL.ui.empty("No documents", "No uploads for this indicator yet.")}</div>`;
  },

  _paintPendingList: function (session, state, isAdmin) {
    const host = document.getElementById("evidence-body");
    let docs = FL.documents.scoped(session);
    const map = {
      "pending-review": function (d) { return d.status === "pending-review" || d.status === "reviewer-required" || d.status === "invalid"; },
      revision: function (d) { return d.status === "revision"; },
      approved: function (d) { return d.status === "approved" || d.status === "system-approved"; },
      rejected: function (d) { return d.status === "rejected"; }
    };
    const fn = map[state.docFilter];
    if (fn) docs = docs.filter(fn);
    if (state.docFilter === "pending-review") docs = docs.filter(FL.documents.needsAction);
    const reviewBase = isAdmin ? "document-view.html" : "document-review.html";
    host.innerHTML = `
      <div class="table-wrap">
        <table class="data">
          <thead><tr><th>Faculty</th><th>Document</th><th>KRA</th><th>Indicator</th><th>Submitted</th><th>Status</th><th></th></tr></thead>
          <tbody>${docs.map(function (doc) {
            const faculty = FL.store.facultyById(doc.facultyId);
            const hit = doc.indicatorId ? FL.rules.findIndicator(doc.indicatorId) : null;
            const href = reviewBase + "?id=" + encodeURIComponent(doc.id)
              + "&faculty=" + encodeURIComponent(doc.facultyId || "")
              + "&kra=" + encodeURIComponent(doc.kraId || "")
              + "&criterion=" + encodeURIComponent(doc.criterionId || "")
              + "&indicator=" + encodeURIComponent(doc.indicatorId || "");
            return `<tr>
              <td>${FL.esc(faculty ? faculty.name : "—")}</td>
              <td>${FL.esc(doc.name || doc.fileName || doc.id)}</td>
              <td>${FL.esc(doc.kraId || "—")}</td>
              <td>${FL.esc(hit ? hit.indicator.name : doc.indicatorId || "—")}</td>
              <td>${FL.esc(doc.submittedAt ? FL.formatWhen(doc.submittedAt) : "—")}</td>
              <td>${FL.evidence.statusBadge(doc.status)}</td>
              <td class="action-cell"><a class="btn btn-small btn-primary" href="${href}">${isAdmin ? "View" : "Review document"}</a></td>
            </tr>`;
          }).join("")}</tbody>
        </table>
      </div>`;
    if (!docs.length) host.innerHTML = FL.ui.empty("No documents", "Nothing matches this filter.");
    FL.responsive.labelTables(host);
  }
};

FL.docFolders.renderExplorer = function (session, options) {
  const opts = options || {};
  if (opts.queueOnly) {
    opts.initialFilter = "pending-review";
  }
  FL.evidence.mount(session, opts);
};
