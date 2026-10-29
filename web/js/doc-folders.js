/**
 * KRA folder explorer: Faculty → KRA → Criterion → Indicator → Documents
 */
window.FL = window.FL || {};

FL.docFolders = {
  statusBadge: function (status) {
    const map = {
      "pending-review": ["pending", "Pending review"],
      "reviewer-required": ["pending", "Reviewer required"],
      revision: ["warn", "Needs revision"],
      approved: ["valid", "Approved"],
      "simulation-auto-accepted": ["valid", "Auto-accepted for simulation"],
      "simulation-reviewer-validated": ["valid", "Reviewer-validated for simulation"],
      rejected: ["invalid", "Rejected"],
      invalid: ["invalid", "Invalid"]
    };
    const pair = map[status] || ["pending", status || "Unknown"];
    return FL.ui.badge(pair[0], pair[1]);
  },

  kraStats: function (docs, kraId) {
    const rows = docs.filter(function (d) { return d.kraId === kraId; });
    return FL.docFolders._counts(rows);
  },

  _counts: function (rows) {
    const out = { total: rows.length, pending: 0, approved: 0, revision: 0, rejected: 0 };
    rows.forEach(function (doc) {
      if (doc.status === "draft" && doc.hasFile !== false) out.pending += 1;
      else if (doc.status === "approved" || doc.status === "system-approved") out.approved += 1;
      else if (doc.status === "revision") out.revision += 1;
      else if (doc.status === "rejected") out.rejected += 1;
      else if (doc.status === "pending-review" || doc.status === "reviewer-required" || doc.status === "invalid") {
        out.pending += 1;
      }
    });
    return out;
  },

  buildTree: function (session, docs, rootMode) {
    const facultyList = rootMode === "admin"
      ? FL.store.faculty.slice()
      : FL.store.assignedFacultyForReviewer(session);
    const byFaculty = {};
    docs.forEach(function (doc) {
      const fid = doc.facultyId || "";
      if (!byFaculty[fid]) byFaculty[fid] = [];
      byFaculty[fid].push(doc);
    });
    if (rootMode === "admin" && facultyList.length) {
      facultyList.forEach(function (person) {
        if (!byFaculty[person.id]) byFaculty[person.id] = [];
      });
    }
    return { facultyList: facultyList, byFaculty: byFaculty };
  },

  renderExplorer: function (session, options) {
    const opts = options || {};
    const rootMode = session.role === "administrator" ? "admin" : "reviewer";
    const queueOnly = !!opts.queueOnly;
    let docs = queueOnly
      ? FL.documents.scoped(session).filter(FL.documents.needsAction)
      : FL.documents.scoped(session).slice();
    const page = document.getElementById("page");
    const state = {
      facultyId: opts.facultyId || "",
      kraId: opts.kraId || "",
      criterionId: opts.criterionId || "",
      indicatorId: opts.indicatorId || "",
      query: "",
      status: opts.statusFilter || "",
      kraFilter: ""
    };

    page.innerHTML = `
      <div class="page-head">
        <div>
          <p class="eyebrow">${FL.esc(opts.eyebrow || "Document management")}</p>
          <h1>${FL.esc(opts.title || "Documents")}</h1>
          <p class="lede">${FL.esc(opts.lede || "")}</p>
        </div>
      </div>
      <div class="doc-explorer-shell">
        <aside class="doc-explorer-sidebar card" id="doc-tree"></aside>
        <section class="doc-explorer-main">
          <div class="doc-explorer-toolbar">
            <nav class="doc-breadcrumbs" id="doc-crumb" aria-label="Folder path"></nav>
            <label class="search doc-explorer-search"><span class="sr-only">Search</span>
              <input id="doc-folder-search" type="search" placeholder="Search faculty, indicator, or file name">
            </label>
            ${queueOnly ? "" : `<label class="filter"><span>Status</span>
              <select id="doc-folder-status">
                <option value="">All statuses</option>
                <option value="pending-review">Pending review</option>
                <option value="revision">Needs revision</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
              </select></label>`}
          </div>
          <div class="doc-explorer-content card" id="doc-folder-panel"></div>
        </section>
      </div>`;

    const reviewBase = session.role === "administrator" ? "document-view.html" : "document-review.html";

    function breadcrumbs() {
      const parts = [];
      if (rootMode === "admin") parts.push({ label: "All faculty", level: "root" });
      else parts.push({ label: "Assigned faculty", level: "root" });
      if (state.facultyId) {
        const person = FL.store.facultyById(state.facultyId);
        parts.push({ label: person ? person.name : state.facultyId, level: "faculty", facultyId: state.facultyId });
      }
      if (state.kraId) {
        const kra = FL.rules.findKra(state.kraId);
        parts.push({ label: kra ? kra.code : state.kraId, level: "kra", kraId: state.kraId });
      }
      if (state.criterionId) {
        const found = FL.rules.kras.flatMap(function (k) {
          return k.criteria.map(function (c) { return { kra: k, criterion: c }; });
        }).find(function (x) { return x.criterion.id === state.criterionId; });
        parts.push({
          label: found ? found.criterion.name : state.criterionId,
          level: "criterion",
          criterionId: state.criterionId
        });
      }
      if (state.indicatorId) {
        const hit = FL.rules.findIndicator(state.indicatorId);
        parts.push({
          label: hit ? hit.indicator.name : state.indicatorId,
          level: "indicator",
          indicatorId: state.indicatorId
        });
      }
      return parts;
    }

    function filteredDocs(source) {
      const q = state.query.trim().toLowerCase();
      return source.filter(function (doc) {
        if (state.status && doc.status !== state.status) return false;
        if (state.kraFilter && doc.kraId !== state.kraFilter) return false;
        if (state.facultyId && doc.facultyId !== state.facultyId) return false;
        if (state.kraId && doc.kraId !== state.kraId) return false;
        if (state.criterionId && doc.criterionId !== state.criterionId) return false;
        if (state.indicatorId && doc.indicatorId !== state.indicatorId) return false;
        if (!q) return true;
        const faculty = FL.store.facultyById(doc.facultyId);
        const blob = [
          doc.name, doc.fileName, doc.id, faculty ? faculty.name : "",
          doc.kraId, doc.criterionId, doc.indicatorId, doc.status
        ].join(" ").toLowerCase();
        return blob.indexOf(q) !== -1;
      });
    }

    function drawTree() {
      const tree = FL.docFolders.buildTree(session, docs, rootMode);
      const host = document.getElementById("doc-tree");
      const facultyBlocks = (rootMode === "admin" ? tree.facultyList : tree.facultyList).map(function (person) {
        const rows = tree.byFaculty[person.id] || [];
        const open = state.facultyId === person.id;
        const kraNav = FL.rules.kras.map(function (kra) {
          const stats = FL.docFolders.kraStats(rows, kra.id);
          if (!stats.total && !open) return "";
          const kraOpen = open && state.kraId === kra.id;
          const icon = FL.kraConfig && FL.kraConfig.icons[kra.id] ? FL.kraConfig.icons[kra.id] : "";
          return `<div class="doc-tree-kra">
            <button type="button" class="doc-tree-kra-btn${kraOpen ? " is-active" : ""}" data-nav="kra" data-faculty="${FL.esc(person.id)}" data-kra="${FL.esc(kra.id)}">
              <span class="kra-nav-icon">${icon}</span>
              <span>${FL.esc(kra.code)} <small>${stats.total} file${stats.total === 1 ? "" : "s"}</small></span>
            </button>
          </div>`;
        }).join("");
        return `<div class="doc-tree-faculty${open ? " is-open" : ""}">
          <button type="button" class="doc-tree-faculty-btn${open ? " is-active" : ""}" data-nav="faculty" data-faculty="${FL.esc(person.id)}">
            <strong>${FL.esc(person.name)}</strong>
            <small>${rows.length} document${rows.length === 1 ? "" : "s"}</small>
          </button>
          ${open ? `<div class="doc-tree-kras">${kraNav || "<p class=\"sub\">No uploads yet.</p>"}</div>` : ""}
        </div>`;
      }).join("");
      host.innerHTML = facultyBlocks || FL.ui.empty("No faculty", "No assigned or registered faculty to show.");
      host.querySelectorAll("[data-nav]").forEach(function (btn) {
        btn.addEventListener("click", function () {
          state.facultyId = btn.getAttribute("data-faculty") || "";
          state.kraId = btn.getAttribute("data-kra") || "";
          state.criterionId = "";
          state.indicatorId = "";
          drawAll();
        });
      });
    }

    function drawCrumb() {
      const host = document.getElementById("doc-crumb");
      const parts = breadcrumbs();
      host.innerHTML = parts.map(function (part, index) {
        const sep = index ? " › " : "";
        return `${sep}<button type="button" class="doc-crumb-link" data-crumb-index="${index}">${FL.esc(part.label)}</button>`;
      }).join("");
      host.querySelectorAll(".doc-crumb-link").forEach(function (btn) {
        btn.addEventListener("click", function () {
          const index = Number(btn.getAttribute("data-crumb-index"));
          const part = parts[index];
          if (part.level === "root") {
            state.facultyId = "";
            state.kraId = "";
            state.criterionId = "";
            state.indicatorId = "";
          } else if (part.level === "faculty") {
            state.facultyId = part.facultyId;
            state.kraId = "";
            state.criterionId = "";
            state.indicatorId = "";
          } else if (part.level === "kra") {
            state.kraId = part.kraId;
            state.criterionId = "";
            state.indicatorId = "";
          } else if (part.level === "criterion") {
            state.criterionId = part.criterionId;
            state.indicatorId = "";
          }
          drawAll();
        });
      });
    }

    function drawPanel() {
      const host = document.getElementById("doc-folder-panel");
      const scoped = filteredDocs(docs);
      if (!state.facultyId) {
        const cards = (rootMode === "admin" ? FL.store.faculty : FL.store.assignedFacultyForReviewer(session)).map(function (person) {
          const rows = docs.filter(function (d) { return d.facultyId === person.id; });
          const c = FL.docFolders._counts(rows);
          return `<article class="doc-faculty-card">
            <button type="button" class="doc-faculty-card-btn" data-open-faculty="${FL.esc(person.id)}">
              <h3>${FL.esc(person.name)}</h3>
              <p class="sub">${FL.esc(person.department || person.college || "")}</p>
              <ul class="doc-faculty-stats">
                <li><span>Total</span><strong>${c.total}</strong></li>
                <li><span>Pending</span><strong>${c.pending}</strong></li>
                <li><span>Approved</span><strong>${c.approved}</strong></li>
                <li><span>Revision</span><strong>${c.revision}</strong></li>
              </ul>
            </button>
          </article>`;
        }).join("");
        host.innerHTML = cards
          ? `<div class="doc-faculty-grid">${cards}</div>`
          : FL.ui.empty("No faculty folders", "Uploads appear when faculty submit evidence.");
        host.querySelectorAll("[data-open-faculty]").forEach(function (btn) {
          btn.addEventListener("click", function () {
            state.facultyId = btn.getAttribute("data-open-faculty");
            drawAll();
          });
        });
        return;
      }
      if (!state.kraId) {
        const rows = scoped.filter(function (d) { return d.facultyId === state.facultyId; });
        const cards = FL.rules.kras.map(function (kra) {
          const stats = FL.docFolders.kraStats(rows, kra.id);
          const icon = FL.kraConfig && FL.kraConfig.icons[kra.id] ? FL.kraConfig.icons[kra.id] : "";
          return `<article class="doc-kra-card">
            <button type="button" class="doc-kra-card-btn" data-open-kra="${FL.esc(kra.id)}">
              <span class="doc-kra-icon">${icon}</span>
              <h3>${FL.esc(kra.code)}</h3>
              <p>${FL.esc(kra.name)}</p>
              <ul class="doc-faculty-stats">
                <li><span>Files</span><strong>${stats.total}</strong></li>
                <li><span>Pending</span><strong>${stats.pending}</strong></li>
                <li><span>Approved</span><strong>${stats.approved}</strong></li>
              </ul>
            </button>
          </article>`;
        }).join("");
        host.innerHTML = `<div class="doc-kra-grid">${cards}</div>`;
        host.querySelectorAll("[data-open-kra]").forEach(function (btn) {
          btn.addEventListener("click", function () {
            state.kraId = btn.getAttribute("data-open-kra");
            drawAll();
          });
        });
        return;
      }
      const kra = FL.rules.findKra(state.kraId);
      if (!state.criterionId && kra) {
        const rows = scoped.filter(function (d) {
          return d.facultyId === state.facultyId && d.kraId === state.kraId;
        });
        const blocks = kra.criteria.map(function (criterion) {
          const indDocs = rows.filter(function (d) { return d.criterionId === criterion.id; });
          if (!indDocs.length && state.query) return "";
          const indicators = criterion.indicators.map(function (indicator) {
            const idocs = indDocs.filter(function (d) { return d.indicatorId === indicator.id; });
            return `<li>
              <button type="button" class="doc-ind-btn" data-criterion="${FL.esc(criterion.id)}" data-indicator="${FL.esc(indicator.id)}">
                <span>${FL.esc(indicator.name)}</span>
                <small>${idocs.length} document${idocs.length === 1 ? "" : "s"}</small>
              </button>
            </li>`;
          }).join("");
          return `<article class="doc-criterion-fold">
            <h3>${FL.esc(criterion.name)}</h3>
            <ul class="doc-ind-list">${indicators}</ul>
          </article>`;
        }).join("");
        host.innerHTML = blocks || FL.ui.empty("No criteria matches", "Try another search or KRA.");
        host.querySelectorAll(".doc-ind-btn").forEach(function (btn) {
          btn.addEventListener("click", function () {
            state.criterionId = btn.getAttribute("data-criterion");
            state.indicatorId = btn.getAttribute("data-indicator");
            drawAll();
          });
        });
        return;
      }
      const indicatorDocs = scoped.filter(function (d) {
        return d.facultyId === state.facultyId
          && d.kraId === state.kraId
          && (!state.criterionId || d.criterionId === state.criterionId)
          && (!state.indicatorId || d.indicatorId === state.indicatorId);
      });
      const hit = state.indicatorId ? FL.rules.findIndicator(state.indicatorId) : null;
      const evidence = hit ? (hit.indicator.evidence || []) : [];
      host.innerHTML = `
        ${hit ? `<header class="doc-indicator-head">
          <h2>${FL.esc(hit.indicator.name)}</h2>
          ${hit.indicator.description ? `<p class="sub">${FL.esc(hit.indicator.description)}</p>` : ""}
          ${evidence.length ? `<div class="callout compact"><strong>Required evidence</strong><ul class="plain">${evidence.map(function (e) {
            return "<li>" + FL.esc(e) + "</li>";
          }).join("")}</ul></div>` : ""}
        </header>` : ""}
        <div class="doc-file-grid">
          ${indicatorDocs.map(function (doc) {
            const href = reviewBase + "?id=" + encodeURIComponent(doc.id)
              + "&faculty=" + encodeURIComponent(state.facultyId)
              + "&kra=" + encodeURIComponent(state.kraId)
              + "&criterion=" + encodeURIComponent(state.criterionId)
              + "&indicator=" + encodeURIComponent(state.indicatorId);
            const action = queueOnly ? "Review document" : (session.role === "administrator" ? "View document" : "Open");
            return `<article class="doc-file-card">
              <div class="doc-file-icon" aria-hidden="true">${/pdf/i.test(doc.fileName || "") ? "PDF" : "IMG"}</div>
              <div class="doc-file-body">
                <h4>${FL.esc(doc.name || doc.fileName || doc.id)}</h4>
                <p class="sub">${FL.esc(doc.fileName || "")} · ${FL.esc(doc.submittedAt || doc.uploadedAt || "—")}</p>
                ${FL.docFolders.statusBadge(doc.status)}
              </div>
              <a class="btn btn-small btn-primary" href="${href}">${FL.esc(action)}</a>
            </article>`;
          }).join("") || FL.ui.empty("No documents", queueOnly ? "Nothing pending in this folder." : "No uploads for this indicator yet.")}
        </div>`;
    }

    function drawAll() {
      drawTree();
      drawCrumb();
      drawPanel();
    }

    document.getElementById("doc-folder-search").addEventListener("input", function (event) {
      state.query = event.target.value;
      drawPanel();
    });
    const statusSel = document.getElementById("doc-folder-status");
    if (statusSel) {
      statusSel.addEventListener("change", function () {
        state.status = statusSel.value;
        drawPanel();
      });
    }
    if (opts.facultyId) state.facultyId = opts.facultyId;
    if (opts.kraId) state.kraId = opts.kraId;
    if (opts.criterionId) state.criterionId = opts.criterionId;
    if (opts.indicatorId) state.indicatorId = opts.indicatorId;
    drawAll();
  }
};
