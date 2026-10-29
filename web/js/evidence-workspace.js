/**
 * FacultyLink Evidence Workspace — admin & reviewer document management UI.
 */
window.FL = window.FL || {};

FL.evidence = {
  statusBadge: function (status) {
    return FL.docFolders.statusBadge(status);
  },

  docTimestamp: function (doc) {
    return FL.formatDocStamp(doc.submittedAt || doc.uploadedAt || doc.dateSubmitted);
  },

  ocrStatusMeta: function (doc) {
    let st = (doc.ocr && doc.ocr.status) || "pending";
    if (st === "complete") st = "completed";
    const labels = {
      pending: "Pending",
      processing: "Processing",
      completed: "Completed",
      failed: "Failed"
    };
    const badge = { pending: "pending", processing: "processing", completed: "completed", failed: "failed" };
    return {
      key: st,
      label: labels[st] || st,
      badge: badge[st] || "pending"
    };
  },

  fileTypeInfo: function (doc) {
    const name = doc.fileName || doc.name || "";
    const mime = (doc.mimeType || "").toLowerCase();
    if (/\.pdf$/i.test(name) || mime.indexOf("pdf") >= 0) {
      return { short: "PDF", mod: "ev-file-icon--pdf" };
    }
    if (/\.(png|jpe?g|gif|webp|bmp|tiff?)$/i.test(name) || mime.indexOf("image/") === 0) {
      return { short: "Image", mod: "ev-file-icon--img" };
    }
    return { short: "File", mod: "" };
  },

  statIcon: function (key) {
    return FL.ui.statIcon(key);
  },

  chevronIcon: function () {
    return FL.navIcons.icon("chevron-right");
  },

  isSetSefIndicator: function (indicatorId) {
    return indicatorId === "kra1-a-student" || indicatorId === "kra1-a-supervisor";
  },

  reviewDocHref: function (doc, reviewBase) {
    return reviewBase + "?id=" + encodeURIComponent(doc.id || doc.documentId)
      + (doc.facultyId ? "&faculty=" + encodeURIComponent(doc.facultyId) : "")
      + (doc.kraId ? "&kra=" + encodeURIComponent(doc.kraId) : "")
      + (doc.criterionId ? "&criterion=" + encodeURIComponent(doc.criterionId) : "")
      + (doc.indicatorId ? "&indicator=" + encodeURIComponent(doc.indicatorId) : "");
  },

  setSefAggregationLabel: function (methodId) {
    const id = (methodId || "").trim();
    const labels = {
      circular_jc_2026_semester_average: "Semester rating average"
    };
    return labels[id] || (id ? id.replace(/_/g, " ") : "");
  },

  formatSetSefMetric: function (value, decimals) {
    if (value == null || value === "") return "—";
    const num = Number(value);
    if (!Number.isFinite(num)) return String(value);
    if (typeof decimals === "number") return num.toFixed(decimals);
    return String(num);
  },

  setSefMetricCardHtml: function (label, value) {
    return `<div class="set-sef-metric-card">
      <span class="set-sef-metric-label">${FL.esc(label)}</span>
      <span class="set-sef-metric-value">${FL.esc(value)}</span>
    </div>`;
  },

  setSefCalcPanelHtml: function (block) {
    if (!block || typeof block !== "object") return "";
    const cfg = block.configuration || {};
    const cov = block.coverageSummary || {};
    const note = block.scoringNote || block.summaryNote || "";
    const periodRows = block.documents || block.periods || [];
    const hasEvidence = periodRows.length > 0;
    if (!hasEvidence) {
      return `<section class="set-sef-calc card-inset" aria-label="Calculation breakdown">
        <h3 class="set-sef-calc-title">Calculation breakdown</h3>
        <p class="set-sef-calc-empty">No semester evidence uploaded yet. Scores appear here after documents are uploaded and official scoring rules apply.</p>
      </section>`;
    }
    const docs = periodRows;
    const included = cov.includedPeriods;
    const fmt = FL.evidence.formatSetSefMetric.bind(FL.evidence);
    const aggLabel = FL.evidence.setSefAggregationLabel(cfg.aggregationMethod);
    const configParts = [];
    if (cfg.configurationLabel) configParts.push(String(cfg.configurationLabel));
    if (cfg.configurationVersion != null && cfg.configurationVersion !== "") {
      configParts.push("Version " + cfg.configurationVersion);
    }
    if (cfg.effectiveFrom) configParts.push("Effective " + cfg.effectiveFrom);
    if (cfg.publishedAt) configParts.push("Published " + FL.formatDocStamp(cfg.publishedAt));
    const configLine = configParts.length ? configParts.join(" · ") : "—";
    const metrics = [
      ["Included periods", fmt(included, 0)],
      ["Accepted periods", fmt(cov.acceptedPeriods, 0)],
      ["Average rating (%)", fmt(block.averageRatingPercent, 4)],
      ["Validated average (%)", fmt(block.validatedAverageRatingPercent, 4)],
      ["Indicator maximum", fmt(cfg.maxPoints, 2)],
      ["Provisional points", fmt(block.provisionalPoints, 2)],
      ["Validated points", fmt(block.validatedPoints, 2)]
    ];
    const metricHtml = metrics.map(function (pair) {
      return FL.evidence.setSefMetricCardHtml(pair[0], pair[1]);
    }).join("");
    const missingHtml = (block.missingPeriods && block.missingPeriods.length)
      ? `<p class="set-sef-calc-coverage" role="status"><strong>Missing semester coverage:</strong> ${FL.esc(block.missingPeriods.join("; "))}</p>`
      : "";
    return `<section class="set-sef-calc card-inset" aria-label="Calculation breakdown">
      <header class="set-sef-calc-head">
        <h3 class="set-sef-calc-title">Calculation breakdown</h3>
        ${aggLabel ? `<p class="set-sef-calc-method">Method: <span>${FL.esc(aggLabel)}</span></p>` : ""}
      </header>
      ${note ? `<p class="note set-sef-calc-note">${FL.esc(note)}</p>` : ""}
      <div class="set-sef-calc-metrics">${metricHtml}</div>
      <div class="set-sef-calc-config-row">
        <span class="set-sef-calc-config-label">Published configuration</span>
        <span class="set-sef-calc-config-value">${FL.esc(configLine)}</span>
      </div>
      ${missingHtml}
      ${(block.excludedPeriods && block.excludedPeriods.length) ? `<details class="set-sef-exclusions"><summary>Excluded uploads (${block.excludedPeriods.length})</summary><ul>${block.excludedPeriods.map(function (row) {
        return "<li>" + FL.esc((row.fileName || row.documentId || "Document") + ": " + (row.exclusionReason || "Excluded")) + "</li>";
      }).join("")}</ul></details>` : ""}
    </section>`;
  },

  section10StatusLabel: function (data) {
    const cur = (data && data.current) || {};
    const catalog = (data && data.section10Catalog) || [];
    if (cur.reviewerVerified === true) {
      return { text: "Verified Exception", badgeKind: "valid" };
    }
    if (cur.section10Code) {
      const hit = catalog.find(function (item) { return item.code === cur.section10Code; });
      return { text: hit ? hit.label : "Exception saved (unverified)", badgeKind: "pending" };
    }
    return { text: "Standard Coverage", badgeKind: "info" };
  },

  bindSection10Collapse: function () {
    const panel = document.querySelector(".section10-panel[data-collapsible]");
    if (!panel || panel.getAttribute("data-s10-collapse-bound") === "1") return;
    panel.setAttribute("data-s10-collapse-bound", "1");
    const btn = panel.querySelector(".section10-toggle");
    const body = panel.querySelector(".section10-body");
    if (!btn || !body) return;
    const setExpanded = function (expanded) {
      panel.classList.toggle("is-expanded", expanded);
      btn.setAttribute("aria-expanded", expanded ? "true" : "false");
      if (expanded) body.removeAttribute("hidden");
      else body.setAttribute("hidden", "");
    };
    setExpanded(false);
    btn.addEventListener("click", function () {
      setExpanded(!panel.classList.contains("is-expanded"));
    });
  },

  section10PanelHtml: function (data, editable) {
    if (!data) return "";
    const cur = data.current || {};
    const catalog = data.section10Catalog || [];
    const status = FL.evidence.section10StatusLabel(data);
    const opts = catalog.map(function (item) {
      const sel = cur.section10Code === item.code ? " selected" : "";
      return `<option value="${FL.esc(item.code)}"${sel}>${FL.esc(item.label)}</option>`;
    }).join("");
    const verified = cur.reviewerVerified === true;
    const readOnly = !editable;
    return `<section class="section10-panel card-inset" data-collapsible aria-label="Section 10 evaluation eligibility">
      <button type="button" class="section10-toggle" aria-expanded="false" aria-controls="s10-panel-body">
        <span class="section10-toggle-main">
          <span class="section10-toggle-title">Section 10 — special evaluation circumstances</span>
          ${FL.ui.badge(status.badgeKind, status.text)}
        </span>
        <span class="section10-toggle-chevron" aria-hidden="true">${FL.evidence.chevronIcon()}</span>
      </button>
      <div id="s10-panel-body" class="section10-body" hidden>
      <p class="note">Standard divisor: ${FL.esc(String(data.standardRequiredSemesters || 6))} semesters unless a verified exception applies. Semester count alone is not sufficient — attest evidence on file.</p>
      ${readOnly ? `<p class="sub">Read-only (administrator monitor).</p>` : ""}
      <div class="section10-form">
        <label class="field"><span>Circumstance</span>
          <select id="s10-code" ${readOnly ? "disabled" : ""}>
            <option value="">— Standard coverage (no Section 10 exception) —</option>${opts}
          </select></label>
        <label class="field"><span>Eligible semester count</span>
          <input id="s10-count" type="number" min="1" max="6" step="1" ${readOnly ? "disabled" : ""}
            value="${cur.eligibleSemesterCount != null ? FL.esc(String(cur.eligibleSemesterCount)) : ""}" placeholder="Required when verified"></label>
        <label class="field field-span"><span>Supporting evidence summary</span>
          <textarea id="s10-evidence" rows="2" ${readOnly ? "disabled" : ""} placeholder="Describe official documents on file (leave, appointment, lab school assignment, etc.)">${FL.esc(cur.supportingEvidenceSummary || "")}</textarea></label>
        <label class="field field-span"><span>Justification</span>
          <textarea id="s10-justification" rows="2" ${readOnly ? "disabled" : ""} placeholder="Reviewer rationale (min. 16 characters)">${FL.esc(cur.justification || "")}</textarea></label>
        ${readOnly ? "" : `<label class="field field-span"><span><input id="s10-attest" type="checkbox" ${cur.evidenceOnFileAttested ? "checked" : ""}> Supporting evidence verified on file</span></label>
        <label class="field field-span"><span><input id="s10-verify" type="checkbox" ${verified ? "checked" : ""}> Mark Section 10 exception as reviewer-verified for scoring</span></label>
        <p class="field-error" id="s10-error"></p>
        <div class="section10-actions">
          <button type="button" class="btn btn-primary btn-small" id="s10-save">Save eligibility</button>
          <button type="button" class="btn btn-ghost btn-small" id="s10-clear">Clear exception</button>
        </div>`}
        ${verified ? `<p class="note">Verified exception active for scoring divisor.</p>` : `<p class="note">Unverified or draft entries use the standard six-semester divisor.</p>`}
      </div>
      ${(data.auditLog && data.auditLog.length) ? `<details class="set-sef-exclusions"><summary>Eligibility audit (${data.auditLog.length})</summary><ul>${data.auditLog.slice().reverse().slice(0, 8).map(function (row) {
        return "<li>" + FL.esc((row.at || "") + " · " + (row.reviewerName || row.reviewerId || "Reviewer") + " · " + (row.action || "update")) + "</li>";
      }).join("")}</ul></details>` : ""}
      </div>
    </section>`;
  },

  bindSection10Panel: function (session, facultyId, editable, onSaved) {
    FL.evidence.bindSection10Collapse();
    if (!editable) return;
    const err = document.getElementById("s10-error");
    const payloadFromForm = function (extra) {
      const base = {
        section10Code: (document.getElementById("s10-code").value || "").trim() || null,
        eligibleSemesterCount: (document.getElementById("s10-count").value || "").trim(),
        supportingEvidenceSummary: (document.getElementById("s10-evidence").value || "").trim(),
        justification: (document.getElementById("s10-justification").value || "").trim(),
        evidenceOnFileAttested: document.getElementById("s10-attest").checked,
        reviewerVerified: document.getElementById("s10-verify").checked
      };
      return Object.assign(base, extra || {});
    };
    const saveBtn = document.getElementById("s10-save");
    if (saveBtn) {
      saveBtn.addEventListener("click", function () {
        if (err) err.textContent = "";
        FL.store.saveEvaluationEligibility(session, facultyId, payloadFromForm()).then(function (data) {
          FL.ui.toast("Section 10 eligibility saved.", "ok");
          if (typeof onSaved === "function") onSaved(data);
        }).catch(function (e) {
          if (err) err.textContent = e.message || "Save failed.";
        });
      });
    }
    const clearBtn = document.getElementById("s10-clear");
    if (clearBtn) {
      clearBtn.addEventListener("click", function () {
        if (err) err.textContent = "";
        const reason = (document.getElementById("s10-justification").value || "").trim();
        if (reason.length < 16) {
          if (err) err.textContent = "Enter a justification in the field above before clearing (min. 16 characters).";
          return;
        }
        FL.store.saveEvaluationEligibility(session, facultyId, { clear: true, justification: reason }).then(function (data) {
          FL.ui.toast("Section 10 exception cleared.", "ok");
          if (typeof onSaved === "function") onSaved(data);
        }).catch(function (e) {
          if (err) err.textContent = e.message || "Clear failed.";
        });
      });
    }
  },

  setSefUploadCountFromTe: function (indicatorId, payload) {
    if (!FL.evidence.isSetSefIndicator(indicatorId) || !payload) return null;
    if (indicatorId === "kra1-a-student") {
      return ((payload.set || {}).coverageSummary || {}).totalUploads;
    }
    if (indicatorId === "kra1-a-supervisor") {
      return ((payload.sef || {}).coverageSummary || {}).totalUploads;
    }
    return null;
  },

  formatTeScorePair: function (block) {
    const uploads = ((block || {}).coverageSummary || {}).totalUploads || 0;
    if (uploads === 0) return "0 / 0";
    const prov = block.provisionalPoints;
    const val = block.validatedPoints;
    const fmt = function (v) { return v == null || v === "" ? "—" : String(v); };
    return fmt(prov) + " / " + fmt(val);
  },

  formatCombinedTePoints: function (payload, key) {
    const setUp = ((payload.set || {}).coverageSummary || {}).totalUploads || 0;
    const sefUp = ((payload.sef || {}).coverageSummary || {}).totalUploads || 0;
    if (setUp === 0 && sefUp === 0) return "0";
    const v = payload[key];
    return v == null || v === "" ? "—" : String(v);
  },

  criterionASummaryHtml: function (payload) {
    if (!payload) return "";
    const set = payload.set || {};
    const sef = payload.sef || {};
    const note = payload.summaryNote || "";
    const fmtMax = function (v) { return v == null || v === "" ? "—" : String(v); };
    return `<section class="criterion-a-summary card-inset" aria-label="Teaching Effectiveness summary">
      <h3 class="set-sef-calc-title">Criterion A — Teaching Effectiveness (SET + SEF)</h3>
      ${note ? `<p class="note">${FL.esc(note)}</p>` : ""}
      <dl class="set-sef-calc-grid">
        <div><dt>SET provisional / validated</dt><dd>${FL.esc(FL.evidence.formatTeScorePair(set))}</dd></div>
        <div><dt>SEF provisional / validated</dt><dd>${FL.esc(FL.evidence.formatTeScorePair(sef))}</dd></div>
        <div><dt>Combined provisional</dt><dd>${FL.esc(FL.evidence.formatCombinedTePoints(payload, "combinedProvisionalPoints"))}</dd></div>
        <div><dt>Combined validated</dt><dd>${FL.esc(FL.evidence.formatCombinedTePoints(payload, "combinedValidatedPoints"))}</dd></div>
        <div><dt>Criterion maximum</dt><dd>${FL.esc(fmtMax(payload.criterionMaxPoints))}</dd></div>
        <div><dt>Configuration</dt><dd>${payload.configurationComplete ? "Published rules loaded" : "Incomplete"}</dd></div>
      </dl>
    </section>`;
  },

  _paintCriterionAIndicators: function (criterion, payload, docs) {
    return criterion.indicators.map(function (indicator) {
      let count = docs.filter(function (d) { return d.indicatorId === indicator.id; }).length;
      const liveCount = FL.evidence.setSefUploadCountFromTe(indicator.id, payload);
      if (liveCount != null) count = liveCount;
      return `<button type="button" class="evidence-ind-open" data-indicator="${FL.esc(indicator.id)}">
        <span>${FL.esc(indicator.name)}</span>
        <small>${count} file${count === 1 ? "" : "s"}</small>
      </button>`;
    }).join("");
  },

  documentCardHtml: function (doc, options) {
    const opts = options || {};
    const reviewBase = opts.reviewBase || "document-review.html";
    const actionLabel = opts.actionLabel || "Review";
    const href = reviewBase + "?id=" + encodeURIComponent(doc.id)
      + (doc.facultyId ? "&faculty=" + encodeURIComponent(doc.facultyId) : "")
      + (doc.kraId ? "&kra=" + encodeURIComponent(doc.kraId) : "")
      + (doc.criterionId ? "&criterion=" + encodeURIComponent(doc.criterionId) : "")
      + (doc.indicatorId ? "&indicator=" + encodeURIComponent(doc.indicatorId) : "");
    const fileName = doc.fileName || doc.name || doc.id;
    const ft = FL.evidence.fileTypeInfo(doc);
    const ocr = FL.evidence.ocrStatusMeta(doc);
    const dateStr = FL.evidence.docTimestamp(doc);
    let downloadBtn = "";
    if (doc.fileUrl && opts.allowDownload) {
      downloadBtn = `<a class="btn btn-ghost btn-small ev-doc-action" href="${FL.esc(doc.fileUrl)}" download="${FL.esc(fileName)}" target="_blank" rel="noopener">Download</a>`;
    }
    const primaryAction = downloadBtn || `<a class="btn btn-ghost btn-small ev-doc-action" href="${href}">${FL.esc(actionLabel)}</a>`;
    return `<article class="ev-doc-card">
      <div class="ev-doc-card-row">
        <div class="ev-file-icon ${ft.mod}" aria-hidden="true">${FL.esc(ft.short)}</div>
        <div class="ev-doc-card-main">
          <h3 class="ev-doc-title" title="${FL.esc(fileName)}">${FL.esc(fileName)}</h3>
          <p class="ev-doc-meta">${FL.esc(ft.short)} · ${FL.esc(dateStr)}</p>
          <div class="ev-doc-status-inline">
            <span class="ev-pill"><span class="ev-pill-label">Review</span>${FL.evidence.statusBadge(doc.status)}</span>
            <span class="ev-pill"><span class="ev-pill-label">OCR</span>${FL.ui.statusBadge(ocr.badge, ocr.label)}</span>
          </div>
        </div>
        ${primaryAction}
      </div>
    </article>`;
  },

  _criterionLabel: function (kraId, criterionId) {
    const kra = FL.rules.findKra(kraId);
    if (!kra) return criterionId;
    const c = kra.criteria.find(function (row) { return row.id === criterionId; });
    return c ? c.name : criterionId;
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

    const showFilters = !inFolder;
    page.innerHTML = `
      <div class="evidence-workspace">
        ${FL.ui.pageHeader({
          eyebrow: "FacultyLink",
          title: "Evidence Workspace",
          lede: isAdmin
            ? "Monitor and organize supporting documents across faculty."
            : "Manage and review supporting documents for your assigned faculty."
        })}
        ${isAdmin && FL.store.usesRealAdminApi() ? `<section class="card set-sef-policy-card" id="set-sef-policy-panel" aria-label="SET/SEF simulation auto-accept policy"><p class="note">Loading simulation auto-accept policy…</p></section>` : ""}
        <nav class="evidence-crumb-bar" id="evidence-crumb" aria-label="Breadcrumb"></nav>
        ${inFolder ? `<div class="evidence-nav-bar"><button type="button" class="btn btn-ghost btn-small" id="evidence-back">← Previous level</button></div>` : ""}
        <div class="evidence-stats" id="evidence-stats"></div>
        ${showFilters || pendingMode ? `<div class="evidence-toolbar">
          ${showFilters ? `<div class="evidence-filters" role="tablist">${FL.evidence._filterTabs(state.docFilter)}</div>` : ""}
          ${!inFolder && !pendingMode ? `<label class="search evidence-search"><span class="sr-only">Search faculty</span>
            <input id="evidence-search" type="search" placeholder="Search name, email, or employee ID" value="${FL.esc(state.q)}"></label>` : ""}
        </div>` : ""}
        <div class="evidence-body card" id="evidence-body"></div>
      </div>`;

    FL.evidence._paintStats(stats, isAdmin);
    if (isAdmin && FL.store.usesRealAdminApi()) FL.evidence._paintSetSefSimulationPolicy(session);
    FL.evidence._paintCrumb(state, isAdmin, session);
    FL.evidence._bindBack(state, session);
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

  _paintSetSefSimulationPolicy: function (session) {
    const host = document.getElementById("set-sef-policy-panel");
    if (!host) return;
    FL.store.fetchSetSefSimulationPolicy().then(function (data) {
      const policy = (data && data.policy) || {};
      const active = policy.active === true;
      const toggleOk = policy.adminToggleAllowed === true || policy.envForcedOn === true;
      const disabledNote = !toggleOk
        ? "<p class=\"note\">Server has not allowed Admin toggling. Set <code>SET_SEF_AUTO_APPROVAL_ALLOW_ADMIN_TOGGLE=true</code> and restart the API.</p>"
        : "";
      host.innerHTML = `
        <div class="card-head">
          <h2>SET/SEF simulation auto-accept</h2>
          ${FL.ui.badge(active ? "valid" : "pending", active ? "Active" : "Inactive")}
        </div>
        <p class="note">When active, OCR-complete SET/SEF uploads with valid evaluation metadata are auto-accepted for simulation scoring only — not official document certification.</p>
        <p class="sub">Policy version ${FL.esc(String(policy.policyVersion || "—"))}${policy.enabledAt ? " · enabled " + FL.esc(FL.formatDocStamp(policy.enabledAt)) : ""}</p>
        ${disabledNote}
        <label class="field field-inline">
          <input type="checkbox" id="set-sef-policy-enabled" ${active ? "checked" : ""} ${toggleOk ? "" : "disabled"}>
          <span>Enable simulation auto-accept for new OCR completions</span>
        </label>
        <p class="sub">Existing pending documents are not changed until you run a controlled reassessment (CLI) after enabling.</p>`;
      const box = document.getElementById("set-sef-policy-enabled");
      if (!box || !toggleOk) return;
      box.addEventListener("change", function () {
        const want = box.checked;
        FL.store.saveSetSefSimulationPolicy(want).then(function (res) {
          const p = (res && res.policy) || {};
          FL.ui.toast(want ? "Simulation auto-accept enabled." : "Simulation auto-accept disabled.", "ok");
          FL.evidence._paintSetSefSimulationPolicy(session);
        }).catch(function (err) {
          box.checked = !want;
          FL.ui.toast(err.message || "Policy was not updated.", "danger");
        });
      });
    }).catch(function (err) {
      host.innerHTML = `<p class="note">Could not load simulation auto-accept policy: ${FL.esc(err.message || "error")}</p>`;
    });
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
          { label: "Faculty with documents", value: stats.facultyWithDocuments, iconKey: "faculty", accent: "teal" },
          { label: "Total documents", value: stats.totalDocuments, iconKey: "documents", accent: "" },
          { label: "Pending review", value: stats.pendingReview, iconKey: "pending", accent: "warn" },
          { label: "Approved", value: stats.approvedEvidence, iconKey: "approved", accent: "ok" },
          { label: "Needs revision", value: stats.needsRevision, iconKey: "revision", accent: "warn" }
        ]
      : [
          { label: "Assigned faculty", value: stats.assignedFaculty ?? stats.facultyWithDocuments, iconKey: "faculty", accent: "teal" },
          { label: "Pending review", value: stats.pendingReview, iconKey: "pending", accent: "warn" },
          { label: "Approved", value: stats.approvedEvidence, iconKey: "approved", accent: "ok" },
          { label: "Needs revision", value: stats.needsRevision, iconKey: "revision", accent: "warn" }
        ];
    host.innerHTML = cards.map(function (c) {
      const accent = c.accent ? " is-accent-" + c.accent : "";
      const val = c.value == null ? "—" : c.value;
      return `<div class="evidence-stat${accent}">
        <span class="evidence-stat-icon" aria-hidden="true">${FL.evidence.statIcon(c.iconKey)}</span>
        <div class="evidence-stat-body"><span>${FL.esc(c.label)}</span><strong>${FL.esc(String(val))}</strong></div>
      </div>`;
    }).join("");
  },

  _bindBack: function (state, session) {
    const btn = document.getElementById("evidence-back");
    if (!btn) return;
    btn.addEventListener("click", function () {
      if (state.indicatorId) state.indicatorId = "";
      else if (state.criterionId) state.criterionId = "";
      else if (state.kraId) state.kraId = "";
      else if (state.facultyId) state.facultyId = "";
      FL.evidence.pushLocation(state);
      FL.evidence.mount(session);
    });
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
      parts.push({
        label: kra ? kra.code : state.kraId,
        go: { facultyId: state.facultyId, kraId: state.kraId, criterionId: "", indicatorId: "" }
      });
    }
    if (state.criterionId) {
      parts.push({
        label: FL.evidence._criterionLabel(state.kraId, state.criterionId),
        go: { facultyId: state.facultyId, kraId: state.kraId, criterionId: state.criterionId, indicatorId: "" }
      });
    }
    if (state.indicatorId) {
      const hit = FL.rules.findIndicator(state.indicatorId);
      parts.push({ label: hit ? hit.indicator.name : state.indicatorId, go: null });
    }
    if (state.indicatorId && state.facultyId) {
      parts.push({ label: "Documents", go: null });
    }
    host.innerHTML = parts.map(function (part, i) {
      const sep = i ? `<span class="evidence-crumb-segment" aria-hidden="true">›</span>` : "";
      if (!part.go) {
        return sep + `<span class="evidence-crumb-current">${FL.esc(part.label)}</span>`;
      }
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
            <th>Faculty</th><th>Department</th><th>Assigned reviewer</th><th>Documents</th><th>Pending review</th><th>Last activity</th><th>Actions</th>
          </tr></thead>
          <tbody>
            ${rows.map(function (row) {
              return `<tr>
                <td><div class="evidence-person"><span class="evidence-avatar">${FL.esc(FL.evidence.initials(row.name))}</span>
                  <div class="evidence-person-text"><strong>${FL.esc(row.name)}</strong><small>${FL.esc(row.employeeNo || row.email || "—")}</small></div></div></td>
                <td>${FL.esc(row.department || "—")}</td>
                <td>${FL.esc(row.reviewerName || "Unassigned")}</td>
                <td>${FL.esc(String(row.documentTotal || 0))}</td>
                <td>${row.documentPending ? FL.ui.badge("pending", String(row.documentPending)) : "0"}</td>
                <td>${FL.esc(row.lastActivity ? FL.formatWhen(row.lastActivity) : "—")}</td>
                <td class="action-cell"><button type="button" class="btn btn-ghost btn-small" data-open-faculty="${FL.esc(row.id)}">Open</button></td>
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
    host.innerHTML = `<h2 class="evidence-section-title">Key Result Areas</h2><div class="evidence-kra-grid">${FL.rules.kras.map(function (kra) {
      const stats = FL.docFolders.kraStats(docs, kra.id);
      const critCount = kra.criteria.length;
      const icon = FL.navIcons.icon("folder");
      const active = state.kraId === kra.id ? " is-active" : "";
      const approvedNote = stats.total
        ? `<p class="evidence-kra-footnote">${stats.approved} of ${stats.total} approved</p>`
        : `<p class="evidence-kra-footnote">No uploads yet</p>`;
      return `<article class="evidence-kra-card${active}">
        <button type="button" class="evidence-kra-open" data-kra="${FL.esc(kra.id)}">
          <div class="evidence-kra-head">
            <span class="evidence-kra-icon">${icon}</span>
            <span class="evidence-kra-arrow">${FL.evidence.chevronIcon()}</span>
          </div>
          <h3>${FL.esc(kra.code)}</h3>
          <p>${FL.esc(kra.name)}</p>
          <ul class="evidence-kra-meta">
            <li><strong>${critCount}</strong> criteria</li>
            <li><strong>${stats.total}</strong> documents</li>
            <li><strong>${stats.pending}</strong> pending</li>
          </ul>
          ${approvedNote}
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
      host.innerHTML = `<h2 class="evidence-section-title">${FL.esc(kra.code)} — Select criterion</h2><div class="evidence-criterion-grid">${kra.criteria.map(function (criterion) {
        const count = docs.filter(function (d) { return d.criterionId === criterion.id; }).length;
        return `<article class="evidence-criterion-card">
          <button type="button" class="evidence-criterion-open" data-criterion="${FL.esc(criterion.id)}">
            <div>
              <h3>${FL.esc(criterion.name)}</h3>
              <p class="sub">${count} document${count === 1 ? "" : "s"}</p>
            </div>
            <span class="evidence-kra-arrow">${FL.evidence.chevronIcon()}</span>
          </button>
        </article>`;
      }).join("")}</div>`;
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
    const paintCriterionIndicators = function (tePayload) {
      const list = document.getElementById("criterion-a-indicators");
      if (!list) return;
      list.innerHTML = FL.evidence._paintCriterionAIndicators(criterion, tePayload, docs);
      list.querySelectorAll("[data-indicator]").forEach(function (btn) {
        btn.addEventListener("click", function () {
          state.indicatorId = btn.getAttribute("data-indicator");
          FL.evidence.pushLocation(state);
          FL.evidence.mount(session);
        });
      });
    };
    if (state.criterionId === "kra1-a" && FL.store.usesLiveDocuments()) {
      const loadFaculty = state.facultyId;
      const loadCriterion = state.criterionId;
      const fetchSeq = (FL.evidence._teFetchSeq = (FL.evidence._teFetchSeq || 0) + 1);
      host.innerHTML = `<h2 class="evidence-section-title">${FL.esc(criterion.name)} — Indicators</h2>
        <div id="criterion-a-summary-slot">${FL.ui.loading("Loading Teaching Effectiveness summary…")}</div>
        <div id="criterion-a-section10-slot">${FL.ui.loading("Loading Section 10 eligibility…")}</div>
        <div class="evidence-indicator-list" id="criterion-a-indicators">${FL.ui.loading("Loading indicator counts…")}</div>`;
      const slot = function () { return document.getElementById("criterion-a-summary-slot"); };
      const s10Slot = function () { return document.getElementById("criterion-a-section10-slot"); };
      const editableS10 = !isAdmin && session.role === "reviewer";
      const refreshTe = function () {
        return FL.store.fetchTeachingEffectiveness(session, loadFaculty).then(function (payload) {
          if (fetchSeq !== FL.evidence._teFetchSeq) return payload;
          if (loadFaculty !== state.facultyId || loadCriterion !== state.criterionId) return payload;
          FL.store.pruneSetSefDocumentsFromTeachingPayload(loadFaculty, payload);
          const s = slot();
          if (s) s.innerHTML = FL.evidence.criterionASummaryHtml(payload);
          paintCriterionIndicators(payload);
          return payload;
        });
      };
      const paintS10 = function (elig) {
        const el = s10Slot();
        if (!el || fetchSeq !== FL.evidence._teFetchSeq) return;
        el.innerHTML = FL.evidence.section10PanelHtml(elig, editableS10);
        FL.evidence.bindSection10Panel(session, loadFaculty, editableS10, onS10Saved);
      };
      const onS10Saved = function () {
        FL.store.fetchEvaluationEligibility(session, loadFaculty).then(function (updated) {
          paintS10(updated);
          refreshTe();
        });
      };
      Promise.all([
        FL.store.loadFacultyDocuments(session, loadFaculty),
        refreshTe(),
        FL.store.fetchEvaluationEligibility(session, loadFaculty).then(paintS10)
      ]).catch(function () {
        if (fetchSeq !== FL.evidence._teFetchSeq) return;
        const s = slot();
        if (s) s.innerHTML = "";
        const s10 = s10Slot();
        if (s10) s10.innerHTML = "";
        paintCriterionIndicators(null);
      });
      return;
    }
    host.innerHTML = `<h2 class="evidence-section-title">${FL.esc(criterion.name)} — Indicators</h2>
      <div id="criterion-a-summary-slot"></div>
      <div id="criterion-a-section10-slot"></div>
      <div class="evidence-indicator-list" id="criterion-a-indicators">${FL.evidence._paintCriterionAIndicators(criterion, null, docs)}</div>`;
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
    const isSetSef = FL.evidence.isSetSefIndicator(state.indicatorId);

    if (isSetSef) {
      if (!FL.store.usesLiveDocuments()) {
        host.innerHTML = FL.ui.empty(
          "Live API required",
          "SET/SEF evidence is loaded from PostgreSQL only. Sign in again if this message persists."
        );
        return;
      }
      const loadIndicator = state.indicatorId;
      const loadFaculty = state.facultyId;
      host.innerHTML = `${hit ? `<div class="evidence-indicator-head"><h2>${FL.esc(hit.indicator.name)}</h2>
        ${hit.indicator.evidence && hit.indicator.evidence.length ? `<p class="sub">Required: ${FL.esc(hit.indicator.evidence.join("; "))}</p>` : ""}</div>` : ""}
        ${FL.ui.loading("Loading SET/SEF evidence…")}`;
      const fetchSeq = (FL.evidence._setSefFetchSeq = (FL.evidence._setSefFetchSeq || 0) + 1);
      Promise.all([
        FL.store.loadFacultyDocuments(session, loadFaculty),
        FL.store.fetchSetSefIndicator(session, loadFaculty, loadIndicator)
      ]).then(function (results) {
        if (fetchSeq !== FL.evidence._setSefFetchSeq) return;
        if (state.indicatorId !== loadIndicator || state.facultyId !== loadFaculty) return;
        const block = results[1];
        FL.store.syncSetSefIndicatorDocuments(loadFaculty, loadIndicator, block || {});
        const freshDocs = FL.evidence._facultyDocs(session, loadFaculty).filter(function (d) {
          return d.kraId === state.kraId && d.criterionId === state.criterionId && d.indicatorId === loadIndicator;
        });
        FL.evidence._paintSetSefIndicatorTable(host, session, state, isAdmin, hit, freshDocs, reviewBase, block);
      }).catch(function (err) {
        if (fetchSeq !== FL.evidence._setSefFetchSeq) return;
        if (state.indicatorId !== loadIndicator) return;
        host.innerHTML = FL.ui.empty("Could not load indicator data", err.message || "Try again.");
      });
      return;
    }

    host.innerHTML = `
      ${hit ? `<div class="evidence-indicator-head"><h2>${FL.esc(hit.indicator.name)}</h2>
        ${hit.indicator.evidence && hit.indicator.evidence.length ? `<p class="sub">Required: ${FL.esc(hit.indicator.evidence.join("; "))}</p>` : ""}</div>` : ""}
      <div class="evidence-file-grid">${docs.map(function (doc) {
        return FL.evidence.documentCardHtml(doc, {
          reviewBase: reviewBase,
          actionLabel: isAdmin ? "Monitor document" : "Review document",
          allowDownload: false
        });
      }).join("") || FL.ui.empty("No documents uploaded", "No evidence files for this indicator yet.")}</div>`;
  },

  _paintSetSefIndicatorTable: function (host, session, state, isAdmin, hit, localDocs, reviewBase, block) {
    const rows = (block && block.documents) || [];
    const ctx = {
      facultyId: state.facultyId,
      kraId: state.kraId || "kra1",
      criterionId: state.criterionId || "kra1-a",
      indicatorId: state.indicatorId
    };
    const mergeDoc = function (row) {
      const id = row.documentId || row.id;
      const local = localDocs.find(function (d) { return d.id === id; });
      return Object.assign({}, local || {}, ctx, {
        id: id,
        fileName: row.fileName || (local && local.fileName),
        status: row.reviewerValidationStatus || row.reviewStatus || (local && local.status) || "pending-review"
      });
    };
    const tableBody = rows.length ? rows.map(function (row) {
      const doc = mergeDoc(row);
      const href = FL.evidence.reviewDocHref(doc, reviewBase);
      const fileName = row.fileName || doc.fileName || doc.id;
      const ocrV = row.ocrVerificationStatus || (doc.extractedInfo && doc.extractedInfo["Indicator verification status"]) || "—";
      const displaySt = row.reviewDisplayStatus
        || (doc.status === "approved" && (row.approvalDecisionSource || (doc.extractedInfo && doc.extractedInfo["Approval decision source"])) === "system_auto_approval"
          ? "simulation-auto-accepted"
          : doc.status === "approved"
            ? "simulation-reviewer-validated"
            : doc.status || row.reviewBucket || "pending-review");
      return `<tr>
        <td>${FL.esc(row.academicYear || "—")}</td>
        <td>${FL.esc(row.semester || "—")}</td>
        <td><a class="set-sef-file-link" href="${href}">${FL.esc(fileName)}</a></td>
        <td>${FL.esc(row.ratingRaw || "—")}</td>
        <td>${FL.esc(row.ratingScale != null ? row.ratingScale : "—")}</td>
        <td>${FL.esc(ocrV)}</td>
        <td>${FL.evidence.statusBadge(displaySt === "accepted" ? "approved" : displaySt)}</td>
      </tr>`;
    }).join("") : "";

    host.innerHTML = `${hit ? `<div class="evidence-indicator-head"><h2>${FL.esc(hit.indicator.name)}</h2></div>` : ""}
      <div class="table-wrap set-sef-table-wrap">
        <table class="data set-sef-evidence-table">
          <thead><tr>
            <th>Academic year</th><th>Semester</th><th>Filename</th><th>Overall rating</th>
            <th>Rating scale</th><th>OCR verification</th><th>Reviewer validation</th>
          </tr></thead>
          <tbody>${tableBody || `<tr><td colspan="7" class="sub">No SET/SEF documents uploaded yet.</td></tr>`}</tbody>
        </table>
      </div>
      ${FL.evidence.setSefCalcPanelHtml(block)}`;
    FL.responsive.labelTables(host);
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
          <thead><tr><th>Faculty</th><th>Document</th><th>KRA</th><th>Indicator</th><th>Submitted</th><th>Review</th><th>OCR</th><th>Actions</th></tr></thead>
          <tbody>${docs.map(function (doc) {
            const faculty = FL.store.facultyById(doc.facultyId);
            const hit = doc.indicatorId ? FL.rules.findIndicator(doc.indicatorId) : null;
            const href = reviewBase + "?id=" + encodeURIComponent(doc.id)
              + "&faculty=" + encodeURIComponent(doc.facultyId || "")
              + "&kra=" + encodeURIComponent(doc.kraId || "")
              + "&criterion=" + encodeURIComponent(doc.criterionId || "")
              + "&indicator=" + encodeURIComponent(doc.indicatorId || "");
            const ocr = FL.evidence.ocrStatusMeta(doc);
            const fileName = doc.fileName || doc.name || doc.id;
            return `<tr>
              <td>${FL.esc(faculty ? faculty.name : "—")}</td>
              <td><span title="${FL.esc(fileName)}">${FL.esc(fileName.length > 48 ? fileName.slice(0, 47) + "…" : fileName)}</span></td>
              <td>${FL.esc(doc.kraId || "—")}</td>
              <td>${FL.esc(hit ? hit.indicator.name : doc.indicatorId || "—")}</td>
              <td>${FL.esc(FL.evidence.docTimestamp(doc))}</td>
              <td>${FL.evidence.statusBadge(doc.status)}</td>
              <td>${FL.ui.statusBadge(ocr.badge, ocr.label)}</td>
              <td class="action-cell"><a class="btn btn-ghost btn-small" href="${href}">${isAdmin ? "Monitor" : "Review"}</a></td>
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
