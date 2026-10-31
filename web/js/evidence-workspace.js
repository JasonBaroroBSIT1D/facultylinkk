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
    const tevId = doc.teachingEvaluationId || doc.tevId || "";
    return reviewBase + "?id=" + encodeURIComponent(doc.id || doc.documentId)
      + (doc.facultyId ? "&faculty=" + encodeURIComponent(doc.facultyId) : "")
      + (doc.kraId ? "&kra=" + encodeURIComponent(doc.kraId) : "")
      + (doc.criterionId ? "&criterion=" + encodeURIComponent(doc.criterionId) : "")
      + (doc.indicatorId ? "&indicator=" + encodeURIComponent(doc.indicatorId) : "")
      + (tevId ? "&tev=" + encodeURIComponent(tevId) : "");
  },

  setSefRecordWarningsHtml: function (row) {
    const parts = [];
    if (row.incompleteExtraction) parts.push('<span class="ev-pill ev-pill-warn">Incomplete OCR</span>');
    if (row.duplicatePeriodWarning) parts.push('<span class="ev-pill ev-pill-warn">Duplicate period</span>');
    if (row.missingFields && row.missingFields.length) {
      parts.push('<span class="ev-pill ev-pill-warn">Missing: ' + FL.esc(row.missingFields.join(", ")) + "</span>");
    }
    return parts.length ? parts.join(" ") : "—";
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
    const comp = block.componentDisplay || {};
    const estLabel = comp.displayLabel || (block.provisionalPoints != null ? "Estimated component: " + block.provisionalPoints : "Not yet computable");
    const metrics = [
      ["Component (display)", estLabel],
      ["Unique eligible semesters", fmt(cov.uniqueEligibleSemesters, 0)],
      ["Included periods", fmt(included, 0)],
      ["Accepted periods", fmt(cov.acceptedPeriods, 0)],
      ["Duplicate uploads excluded", fmt(cov.excludedDuplicateRecords, 0)],
      ["Average rating (%)", fmt(block.averageRatingPercent, 4)],
      ["Validated average (%)", fmt(block.validatedAverageRatingPercent, 4)],
      ["Indicator maximum", fmt(cfg.maxPoints, 2)],
      ["Provisional points (calc)", block.provisionalPoints == null ? "Not yet computable" : fmt(block.provisionalPoints, 2)],
      ["Validated points (calc)", block.validatedPoints == null ? "Not yet computable" : fmt(block.validatedPoints, 2)]
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

  setSefUploadCountFromTe: function (indicatorId, payload, block) {
    if (!FL.evidence.isSetSefIndicator(indicatorId)) return null;
    if (block && Array.isArray(block.evaluationRecords)) return block.evaluationRecords.length;
    if (!payload) return null;
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
    if (payload && payload.estimatedPoints != null && payload.estimatedPoints !== "") {
      return String(payload.estimatedPoints);
    }
    const setUp = ((payload.set || {}).coverageSummary || {}).totalUploads || 0;
    const sefUp = ((payload.sef || {}).coverageSummary || {}).totalUploads || 0;
    if (setUp === 0 && sefUp === 0) return "Not assessed";
    const v = payload[key];
    return v == null || v === "" ? "Not yet computable" : String(v);
  },

  formatComponentDisplay: function (block) {
    if (!block || typeof block !== "object") return "—";
    const comp = block.componentDisplay;
    if (comp && comp.displayLabel) return comp.displayLabel;
    if (block.provisionalPoints != null) return "Estimated component: " + block.provisionalPoints;
    if (block.validatedPoints != null) return "Validated component: " + block.validatedPoints;
    return block.scoringNote || "Not yet computable";
  },

  formatComponentScoreValue: function (block) {
    if (!block || typeof block !== "object") return "—";
    const comp = block.componentDisplay;
    if (comp && comp.state === "awaiting_evidence") return "—";
    if (block.provisionalPoints != null && block.provisionalPoints !== "") {
      return FL.evidence.formatSetSefMetric(block.provisionalPoints, 2);
    }
    if (block.validatedPoints != null && block.validatedPoints !== "") {
      return FL.evidence.formatSetSefMetric(block.validatedPoints, 2);
    }
    if (comp && comp.estimatedPoints != null) {
      return FL.evidence.formatSetSefMetric(comp.estimatedPoints, 2);
    }
    return "—";
  },

  formatCriterionAEstimateValue: function (payload) {
    if (!payload || typeof payload !== "object") return "—";
    if (payload.estimatedPoints != null && payload.estimatedPoints !== "") {
      return FL.evidence.formatSetSefMetric(payload.estimatedPoints, 2);
    }
    return "—";
  },

  criterionASummaryHtml: function (payload, options) {
    if (!payload) return "";
    options = options || {};
    const reviewerView = options.reviewerView === true;
    const set = payload.set || {};
    const sef = payload.sef || {};
    const title = "Criterion A — Teaching Effectiveness (SET + SEF)";

    if (reviewerView) {
      const fmtMax = function (v) { return v == null || v === "" ? "—" : String(v); };
      const metrics = [
        ["Estimated Criterion A", FL.evidence.formatCriterionAEstimateValue(payload)],
        ["Estimated SET", FL.evidence.formatComponentScoreValue(set)],
        ["Estimated SEF", FL.evidence.formatComponentScoreValue(sef)],
        ["Maximum Points", fmtMax(payload.criterionMaxPoints)]
      ];
      const metricHtml = metrics.map(function (pair) {
        return FL.evidence.setSefMetricCardHtml(pair[0], pair[1]);
      }).join("");
      return `<section class="criterion-a-summary card-inset" aria-label="Teaching Effectiveness summary">
      <h3 class="set-sef-calc-title">${FL.esc(title)}</h3>
      <div class="set-sef-calc-metrics criterion-a-reviewer-metrics">${metricHtml}</div>
    </section>`;
    }

    const note = payload.summaryNote || "";
    const disp = payload.criterionADisplay || {};
    const fmtMax = function (v) { return v == null || v === "" ? "—" : String(v); };
    const authEst = payload.estimatedPoints != null ? String(payload.estimatedPoints) : (disp.displayLabel || "Not yet computable");
    const expl = disp.explanation ? `<p class="note">${FL.esc(disp.explanation)}</p>` : "";
    const legacyProvRow = `<div><dt>Legacy combined provisional</dt><dd>${FL.esc(payload.combinedProvisionalPoints == null ? "Not yet computable" : String(payload.combinedProvisionalPoints))}</dd></div>`;
    const legacyValRow = `<div><dt>Legacy combined validated</dt><dd>${FL.esc(payload.combinedValidatedPoints == null ? "Not yet computable" : String(payload.combinedValidatedPoints))}</dd></div>`;
    return `<section class="criterion-a-summary card-inset" aria-label="Teaching Effectiveness summary">
      <h3 class="set-sef-calc-title">${FL.esc(title)}</h3>
      ${note ? `<p class="note">${FL.esc(note)}</p>` : ""}
      ${expl}
      <dl class="set-sef-calc-grid">
        <div><dt>Authoritative Criterion A estimate</dt><dd><strong>${FL.esc(authEst)}</strong></dd></div>
        <div><dt>SET component</dt><dd>${FL.esc(FL.evidence.formatComponentDisplay(set))}</dd></div>
        <div><dt>SEF component</dt><dd>${FL.esc(FL.evidence.formatComponentDisplay(sef))}</dd></div>
        ${legacyProvRow}
        ${legacyValRow}
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

  _criterionAFilter: "all",
  _criterionASearch: "",

  criterionAShortDocLabel: function (fileName, maxLen) {
    const name = String(fileName || "Supporting document").trim();
    const limit = maxLen || 28;
    if (name.length <= limit) return name;
    const ext = name.match(/\.[a-z0-9]+$/i);
    const base = ext ? name.slice(0, -(ext[0].length)) : name;
    const suffix = ext ? ext[0] : "";
    const keep = Math.max(8, limit - suffix.length - 1);
    return base.slice(0, keep) + "…" + suffix;
  },

  criterionASemesterSlotBadge: function (row) {
    const status = row.slotStatus || "";
    if (!status) return "";
    const kind = status === "Complete" ? "valid"
      : status === "Pending review" ? "pending"
        : status === "Duplicate" || status === "Outside coverage" ? "invalid"
          : status === "Needs correction" ? "warn"
            : "info";
    return FL.ui.badge(kind, status);
  },

  criterionASemesterCoverageHtml: function (coverage) {
    if (!coverage) return "";
    const renderSlots = function (title, slots) {
      if (!slots || !slots.length) return "";
      const chips = slots.map(function (slot) {
        const label = slot.academicYear && slot.semester
          ? slot.academicYear + " · " + slot.semester
          : "Open slot";
        const st = slot.status || "Missing";
        const kind = st === "Complete" ? "valid"
          : st === "Pending review" ? "pending"
            : st === "Duplicate" || st === "Outside coverage" ? "invalid"
              : st === "Needs correction" ? "warn"
                : "info";
        return `<li class="ca-sem-slot"><span>${FL.esc(label)}</span> ${FL.ui.badge(kind, st)}</li>`;
      }).join("");
      return `<div class="ca-sem-group"><h4>${FL.esc(title)}</h4><ul class="ca-sem-slots">${chips}</ul></div>`;
    };
    return `<section class="ca-semester-coverage card-inset" aria-label="Semester coverage">
      <h3 class="ca-section-subtitle">Eligible semester slots</h3>
      <p class="note">Scoring counts unique SET and SEF semesters up to the published divisor. Duplicate uploads and extra semesters outside coverage are excluded.</p>
      ${renderSlots("SET semesters", coverage.setSemesterSlots)}
      ${renderSlots("SEF semesters", coverage.sefSemesterSlots)}
    </section>`;
  },

  criterionAEvalTableRowHtml: function (row, ctx, reviewBase, isAdmin) {
    const type = (row.evaluationType || "—").toUpperCase();
    const typeClass = type === "SET" ? "ca-type-badge--set" : type === "SEF" ? "ca-type-badge--sef" : "";
    const ui = FL.criterionAWorkspaceUi;
    const period = ui ? ui.formatPeriodLabel(row) : "—";
    const rating = ui ? ui.formatExtractedRating(row) : "—";
    const tevShape = {
      evaluationType: row.evaluationType,
      reviewerValidationStatus: row.reviewerValidationStatus || row.reviewDisplayStatus,
      incompleteExtraction: row.incompleteExtraction,
      extractionStatus: row.extractionStatus
    };
    const reviewed = FL.tevReviewUi && FL.tevReviewUi.isReviewed(tevShape);
    const reviewLabel = reviewed ? "View Review" : "Review";
    const action = `<button type="button" class="ca-table-action ca-table-action--btn" data-ca-tev-review="${FL.esc(row.teachingEvaluationId)}" data-ca-doc-id="${FL.esc(row.documentId)}">${FL.esc(isAdmin ? "View review" : reviewLabel)}</button>`;
    const docHint = row.fileName
      ? `<span class="sr-only">Supporting document ${FL.esc(row.fileName)}</span>`
      : "";
    return `<tr class="ca-eval-row" data-ca-row-id="${FL.esc(row.teachingEvaluationId)}">
      <td class="ca-eval-cell ca-eval-cell--type" data-label="Type">
        <span class="ca-type-badge ca-type-badge--table ${typeClass}">${FL.esc(type)}</span>
      </td>
      <td class="ca-eval-cell ca-eval-cell--period" data-label="Academic Year &amp; Semester">${FL.esc(period)}${docHint}</td>
      <td class="ca-eval-cell ca-eval-cell--rating" data-label="Extracted Rating">${FL.esc(rating)}</td>
      <td class="ca-eval-cell ca-eval-cell--status" data-label="Reviewer Status">${FL.evidence.criterionAStatusPill(row)}${row.slotStatus ? `<div class="ca-eval-scoring-status">${FL.evidence.criterionASemesterSlotBadge(row)}</div>` : ""}${row.scoringExclusionReason ? `<p class="sub ca-eval-exclusion">${FL.esc(row.scoringExclusionReason)}</p>` : ""}</td>
      <td class="ca-eval-cell ca-eval-cell--action" data-label="Action">${action}</td>
    </tr>`;
  },

  criterionAEvalTableHtml: function (rows, ctx, reviewBase, isAdmin) {
    if (!rows.length) {
      return `<div class="ca-empty-state">No evaluations match your filter or search.</div>`;
    }
    const body = rows.map(function (row) {
      return FL.evidence.criterionAEvalTableRowHtml(row, ctx, reviewBase, isAdmin);
    }).join("");
    return `<div class="ca-eval-table-wrap">
      <table class="ca-eval-table">
        <thead>
          <tr>
            <th scope="col">Type</th>
            <th scope="col">Academic Year &amp; Semester</th>
            <th scope="col">Extracted Rating</th>
            <th scope="col">Reviewer Status</th>
            <th scope="col" class="ca-eval-th-action">Action</th>
          </tr>
        </thead>
        <tbody>${body}</tbody>
      </table>
    </div>`;
  },

  criterionAStatusPill: function (row) {
    const ui = FL.tevReviewUi;
    const label = ui
      ? ui.statusLabel({
        evaluationType: row.evaluationType,
        reviewerValidationStatus: row.reviewerValidationStatus || row.reviewDisplayStatus,
        incompleteExtraction: row.incompleteExtraction,
        extractionStatus: row.extractionStatus
      })
      : (row.reviewerValidationStatus || "Pending Review");
    const cls = FL.documents && FL.documents.tevStatusPillClass
      ? FL.documents.tevStatusPillClass(label)
      : "tev-pill tev-pill--pending";
    return `<span class="${cls}">${FL.esc(label)}</span>`;
  },

  criterionAReviewDrawerShellHtml: function (canReview) {
    const readOnlyNote = canReview ? "" : `<p class="note">Preview and inspection only. Assigned reviewers record validation decisions here.</p>`;
    return `<div id="ca-tev-review-drawer" class="tev-drawer ca-tev-drawer" aria-hidden="true" aria-labelledby="ca-tev-drawer-title">
      <button type="button" class="tev-drawer-backdrop" aria-label="Close review panel"></button>
      <div class="tev-drawer-panel" role="dialog" aria-modal="true">
        <header class="tev-drawer-head ca-tev-drawer-head">
          <div class="ca-tev-drawer-head-main">
            <h2 id="ca-tev-drawer-title">Evaluation review</h2>
            <div id="ca-tev-drawer-status-slot" class="ca-tev-drawer-status"></div>
            <p class="sub ca-tev-drawer-meta" id="ca-tev-drawer-subtitle"></p>
          </div>
          <button type="button" class="btn btn-ghost btn-small tev-drawer-close ca-tev-drawer-close" aria-label="Close">×</button>
        </header>
        <div class="tev-drawer-body ca-tev-drawer-body">
          <div class="tev-drawer-split ca-tev-drawer-split">
            <div class="ca-tev-drawer-col ca-tev-drawer-col--form">
            <form class="tev-drawer-form correction-grid" id="ca-tev-drawer-form" onsubmit="return false;">
              <div id="ca-tev-semester-panel" class="ca-drawer-mode-panel">
                <p class="field field-span ca-drawer-readonly-rating"><span>Faculty name</span>
                  <strong id="ca-tev-drawer-faculty-display">—</strong></p>
                <p class="field-span ca-drawer-faculty-note" id="ca-tev-drawer-faculty-note" hidden></p>
                <p class="field field-span ca-drawer-readonly-rating"><span>Extracted rating</span>
                  <strong id="ca-tev-drawer-rating-display">—</strong></p>
                <label class="field"><span>Evaluation type</span>
                  <select id="ca-tev-drawer-type" ${canReview ? "" : "disabled"}>
                    <option value="">— unchanged —</option>
                    <option value="SET">SET (Student evaluation)</option>
                    <option value="SEF">SEF (Supervisor evaluation)</option>
                  </select></label>
                <label class="field"><span>Academic year</span>
                  <input id="ca-tev-drawer-year" type="text" ${canReview ? "" : "readonly"}></label>
                <label class="field"><span>Semester</span>
                  <input id="ca-tev-drawer-sem" type="text" ${canReview ? "" : "readonly"}></label>
                <label class="field"><span>Correct overall rating</span>
                  <input id="ca-tev-drawer-rating" type="text" inputmode="decimal" ${canReview ? "" : "readonly"}></label>
                <label class="field"><span>Rating scale</span>
                  <input id="ca-tev-drawer-scale" type="text" inputmode="decimal" ${canReview ? "" : "readonly"}></label>
                <details class="ca-drawer-tech field-span">
                  <summary>Advanced OCR details</summary>
                  <div id="ca-tev-drawer-tech-slot"></div>
                </details>
              </div>
              <div id="ca-tev-document-panel" class="ca-drawer-mode-panel" hidden>
                <div class="ca-doc-info-inset" id="ca-tev-document-info-slot"></div>
                <div id="ca-tev-document-linked" class="ca-doc-linked-records" hidden></div>
                <details class="ca-drawer-tech field-span" id="ca-tev-document-corrections-wrap">
                  <summary>Correct extracted information</summary>
                  <div id="ca-tev-document-correction-body" class="ca-doc-correction-body"></div>
                </details>
              </div>
              <label class="field field-span" id="ca-tev-shared-remarks-wrap"><span>Reviewer remarks</span>
                <textarea id="ca-tev-drawer-remarks" rows="4" placeholder="Explain your decision or any corrections" ${canReview ? "" : "readonly"}></textarea></label>
              <p class="field-error" id="ca-tev-drawer-error" role="alert"></p>
              <div id="ca-tev-drawer-actions" class="decision-row tev-drawer-actions ca-drawer-actions ca-tev-drawer-footer" role="group" aria-label="Review actions"></div>
              ${readOnlyNote}
            </form>
            </div>
            <aside class="tev-drawer-preview ca-tev-drawer-col ca-tev-drawer-col--preview" aria-label="Original document preview">
              <p class="ca-tev-preview-label">Original document</p>
              <div class="ca-preview-actions" id="ca-tev-drawer-pdf-actions"></div>
              <div class="tev-drawer-preview-frame ca-tev-drawer-preview-frame" id="ca-tev-drawer-preview-frame"></div>
            </aside>
          </div>
        </div>
      </div>
    </div>`;
  },

  criterionAUnifiedWorkspaceHtml: function (session, state, isAdmin, payload, docs, opts) {
    opts = opts || {};
    const workspace = payload && payload.criterionAWorkspace;
    const reviewBase = isAdmin ? "document-view.html" : "document-review.html";
    const canReview = !isAdmin && session && session.role === "reviewer";
    const ctx = {
      facultyId: state.facultyId,
      kraId: state.kraId || "kra1",
      criterionId: state.criterionId || "kra1-a"
    };
    const sources = (workspace && workspace.sourceDocuments) || [];
    const rows = (workspace && workspace.evaluationRecords) || [];
    const totals = (workspace && workspace.totals) || {};
    const semesterCoverageHtml = FL.evidence.criterionASemesterCoverageHtml(
      workspace && workspace.semesterCoverage
    );
    const filter = FL.evidence._criterionAFilter || "all";
    const search = FL.evidence._criterionASearch || "";
    const ui = FL.criterionAWorkspaceUi;
    const childVal = totals.childValidation || {};
    const summary = ui ? ui.summaryCounts(childVal, rows) : { total: 0, reviewed: 0, pending: 0 };
    const filteredRows = ui
      ? ui.sortEvaluationRecords(ui.filterRecords(rows, filter, search))
      : rows;
    const docById = function (id) {
      return (docs || []).find(function (d) { return d.id === id; });
    };
    const attention = ui ? ui.documentsNeedingAttention(sources, rows, docById) : [];
    const showSearch = rows.length >= 4;
    const filterChip = function (key, label) {
      const active = filter === key ? " is-active" : "";
      return `<button type="button" class="tev-filter-chip${active}" data-ca-filter="${FL.esc(key)}">${FL.esc(label)}</button>`;
    };
    let discrepancyNote = "";
    sources.forEach(function (s) {
      const c = s.childValidationSummary || {};
      const pending = (c.pending || 0) + (c.incomplete || 0);
      if (s.parentWorkflowApproved && pending > 0) {
        discrepancyNote = `<div class="alert alert-warning ca-sync-note" role="status">
          Some semester records still need your review even though a supporting PDF shows as processed.
          Counts below reflect each SET/SEF semester, not PDF approval alone.
        </div>`;
      }
    });
    const metric = function (label, value) {
      return `<div class="ca-metric-card">
        <span class="ca-metric-value">${FL.esc(String(value))}</span>
        <span class="ca-metric-label">${FL.esc(label)}</span>
      </div>`;
    };
    const tableBlock = rows.length
      ? FL.evidence.criterionAEvalTableHtml(filteredRows, ctx, reviewBase, isAdmin)
      : `<div class="ca-empty-state">No semester evaluations extracted yet. Check Documents Needing Attention below.</div>`;
    const attentionHtml = attention.length && filter === "all" && !search
      ? `<section class="ca-attention" aria-label="Documents needing attention">
          <h4 class="ca-section-subtitle">Documents needing attention</h4>
          <p class="note">Classification, ownership, OCR, or extraction issues — open the same review modal without leaving this workspace.</p>
          <ul class="ca-attention-list">${attention.map(function (s) {
            const localDoc = docById(s.documentId);
            const issue = ui ? ui.attentionIssueLabel(s, localDoc) : "Needs review";
            return `<li class="ca-attention-item">
              <div>
                <strong>${FL.esc(FL.evidence.criterionAShortDocLabel(s.fileName, 40))}</strong>
                <span class="sub">${FL.esc(issue)} · OCR ${FL.esc(s.ocrStatus || "—")}</span>
              </div>
              <button type="button" class="btn btn-ghost btn-small" data-ca-doc-attention="${FL.esc(s.documentId)}">View document</button>
            </li>`;
          }).join("")}</ul>
        </section>`
      : "";

    return `<section class="criterion-a-unified" aria-label="Teaching evaluations">
      <header class="ca-unified-head">
        <h3 class="ca-main-title">Teaching evaluations</h3>
      </header>
      ${discrepancyNote}
      ${semesterCoverageHtml}
      <div class="ca-metric-row" role="group" aria-label="Evaluation overview">
        ${metric("Total Evaluations", summary.total)}
        ${metric("Reviewed", summary.reviewed)}
        ${metric("Pending Review", summary.pending)}
      </div>
      <div class="ca-toolbar">
        <div class="tev-filters ca-filters" role="toolbar" aria-label="Filter evaluations">
          ${filterChip("all", "All")}
          ${filterChip("set", "SET")}
          ${filterChip("sef", "SEF")}
          ${filterChip("pending", "Pending Review")}
          ${filterChip("reviewed", "Reviewed")}
        </div>
        ${showSearch ? `<label class="ca-search field">
          <span class="sr-only">Search evaluations</span>
          <input type="search" id="ca-eval-search" placeholder="Search year, semester, or rating…" value="${FL.esc(search)}">
        </label>` : ""}
      </div>
      ${tableBlock}
      ${attentionHtml}
      ${opts.skipDrawer ? "" : FL.evidence.criterionAReviewDrawerShellHtml(canReview)}
    </section>`;
  },

  ensureCriterionADrawerOnBody: function (canReview) {
    FL.evidence.pruneDuplicateCriterionADrawers();
    if (document.getElementById("ca-tev-review-drawer")) return;
    const wrap = document.createElement("div");
    wrap.innerHTML = FL.evidence.criterionAReviewDrawerShellHtml(canReview);
    const drawer = wrap.firstElementChild;
    if (drawer) document.body.appendChild(drawer);
    FL.evidence.bindCriterionADrawerChrome();
  },

  pruneDuplicateCriterionADrawers: function () {
    const nodes = document.querySelectorAll("#ca-tev-review-drawer");
    if (nodes.length <= 1) return;
    let keeper = null;
    nodes.forEach(function (node) {
      if (node.parentElement === document.body) keeper = node;
    });
    if (!keeper) keeper = nodes[nodes.length - 1];
    nodes.forEach(function (node) {
      if (node !== keeper) node.remove();
    });
  },

  mountCriterionADrawerToBody: function () {
    FL.evidence.pruneDuplicateCriterionADrawers();
    let drawer = document.getElementById("ca-tev-review-drawer");
    if (!drawer) return null;
    if (drawer.parentElement !== document.body) {
      document.body.appendChild(drawer);
    }
    FL.evidence.bindCriterionADrawerChrome();
    return drawer;
  },

  bindCriterionADrawerChrome: function () {
    const drawer = document.getElementById("ca-tev-review-drawer");
    if (!drawer || drawer.dataset.chromeBound === "1") return;
    drawer.dataset.chromeBound = "1";
    drawer.addEventListener("click", function (ev) {
      if (ev.target.closest(".tev-drawer-close, .tev-drawer-backdrop")) {
        FL.evidence.closeCriterionAReviewDrawer();
      }
    });
  },

  renderCriterionADrawerActions: function (cfg) {
    const host = document.getElementById("ca-tev-drawer-actions");
    if (!host) return;
    cfg = cfg || {};
    if (!cfg.canReview) {
      host.innerHTML = "";
      host.hidden = true;
      return;
    }
    host.hidden = false;
    const parts = [];
    const pushBtn = function (classes, attr, value, label) {
      parts.push(
        "<button type=\"button\" class=\"btn " + classes + "\" " + attr + "=\"" + FL.esc(value) + "\">"
          + FL.esc(label) + "</button>"
      );
    };
    if (cfg.mode === "document") {
      pushBtn("btn-warning", "data-ca-doc-decision", "revision", "Request Revision");
      pushBtn("btn-danger", "data-ca-doc-decision", "reject", "Reject");
      pushBtn("btn-ghost", "data-ca-doc-decision", "save-metadata", "Save Corrections");
    } else {
      const ui = FL.tevReviewUi;
      const status = cfg.statusLabel || (ui && cfg.row ? ui.statusLabel({
        evaluationType: cfg.row.evaluationType,
        reviewerValidationStatus: cfg.row.reviewerValidationStatus || cfg.row.reviewDisplayStatus,
        incompleteExtraction: cfg.row.incompleteExtraction,
        extractionStatus: cfg.row.extractionStatus
      }) : "Pending Review");
      const pending = status === "Pending Review" || status === "Incomplete Extraction";
      const needsRevision = status === "Needs Revision";
      const finalized = status === "Validated" || status === "Rejected";
      if (pending || needsRevision) {
        pushBtn("btn-primary", "data-ca-tev-decision", "approve", "Validate");
        pushBtn("btn-warning", "data-ca-tev-decision", "revision", "Request Revision");
        pushBtn("btn-danger", "data-ca-tev-decision", "reject", "Reject");
      }
      if (pending || needsRevision || finalized) {
        pushBtn("btn-ghost", "data-ca-tev-decision", "save", "Save Corrections");
      }
    }
    parts.push("<button type=\"button\" class=\"btn btn-ghost tev-drawer-close\">Cancel</button>");
    host.innerHTML = parts.join("");
  },

  _lockCaDrawerPageScroll: function () {
    if (document.body.style.position === "fixed") return;
    const y = window.scrollY || 0;
    FL.evidence._caDrawerScrollY = y;
    document.body.style.position = "fixed";
    document.body.style.top = "-" + y + "px";
    document.body.style.left = "0";
    document.body.style.right = "0";
    document.body.style.width = "100%";
  },

  _unlockCaDrawerPageScroll: function () {
    document.body.style.position = "";
    document.body.style.top = "";
    document.body.style.left = "";
    document.body.style.right = "";
    document.body.style.width = "";
    if (FL.evidence._caDrawerScrollY != null) {
      const restore = FL.evidence._caDrawerScrollY;
      FL.evidence._caDrawerScrollY = null;
      window.scrollTo(0, restore);
    }
  },

  bindCriterionAWorkspace: function (session, state, isAdmin, payload, docs, onRefresh) {
    const workspace = payload && payload.criterionAWorkspace;
    const records = (workspace && workspace.evaluationRecords) || [];
    FL.evidence._caWorkspaceCache = {
      session: session,
      state: state,
      records: records,
      docs: docs || [],
      payload: payload,
      onRefresh: onRefresh,
      isAdmin: isAdmin
    };
    const slot = document.querySelector(".criterion-a-unified");
    if (!slot) return;
    slot.querySelectorAll("[data-ca-filter]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        FL.evidence._criterionAFilter = btn.getAttribute("data-ca-filter") || "all";
        if (typeof onRefresh === "function") onRefresh(true);
      });
    });
    const searchInput = slot.querySelector("#ca-eval-search");
    if (searchInput) {
      searchInput.addEventListener("input", function () {
        FL.evidence._criterionASearch = searchInput.value || "";
        if (typeof onRefresh === "function") onRefresh(true);
      });
    }
    const canReview = !isAdmin && session && session.role === "reviewer";
    if (!slot.dataset.caDelegatedClick) {
      slot.dataset.caDelegatedClick = "1";
      slot.addEventListener("click", function (ev) {
        const tevBtn = ev.target.closest("[data-ca-tev-review]");
        if (tevBtn) {
          FL.evidence.openCriterionAReviewDrawer(
            tevBtn.getAttribute("data-ca-tev-review"),
            tevBtn.getAttribute("data-ca-doc-id"),
            canReview
          );
          return;
        }
        const docBtn = ev.target.closest("[data-ca-doc-attention]");
        if (docBtn) {
          ev.preventDefault();
          FL.evidence.openCriterionADocumentReviewDrawer(docBtn.getAttribute("data-ca-doc-attention"), canReview);
        }
      });
    }
    FL.evidence.bindCriterionAReviewActions(canReview);
    FL.evidence.bindCriterionADocumentReviewActions(canReview);
    FL.evidence.ensureCriterionADrawerOnBody(canReview);
    FL.evidence.mountCriterionADrawerToBody();
    if (!FL.evidence._caEscapeBound) {
      FL.evidence._caEscapeBound = true;
      document.addEventListener("keydown", function (ev) {
        if (ev.key !== "Escape") return;
        const openDrawer = document.getElementById("ca-tev-review-drawer");
        if (openDrawer && openDrawer.classList.contains("is-open")) {
          FL.evidence.closeCriterionAReviewDrawer();
        }
      });
    }
  },

  revokeCaPreviewBlob: function () {
    const revokedUrl = FL.evidence._caPreviewObjectUrl;
    if (revokedUrl) {
      URL.revokeObjectURL(revokedUrl);
      FL.evidence._caPreviewObjectUrl = null;
    }
    const docId = FL.evidence._caPreviewDocId;
    if (docId) {
      const cache = FL.evidence._caWorkspaceCache || {};
      const doc = (cache.docs || []).find(function (d) { return d.id === docId; });
      if (doc && doc._objectUrl) {
        if (!revokedUrl || doc._objectUrl === revokedUrl) {
          try { URL.revokeObjectURL(doc._objectUrl); } catch (revokeErr) { /* already revoked */ }
        }
        delete doc._objectUrl;
      }
    }
    FL.evidence._caPreviewDocId = null;
  },

  closeCriterionAReviewDrawer: function () {
    const drawer = document.getElementById("ca-tev-review-drawer");
    if (!drawer) return;
    drawer.classList.remove("is-open");
    drawer.setAttribute("aria-hidden", "true");
    document.body.classList.remove("tev-drawer-open", "ca-tev-drawer-open");
    FL.evidence._unlockCaDrawerPageScroll();
    const form = document.getElementById("ca-tev-drawer-form");
    if (form) {
      form.dataset.activeTevId = "";
      form.dataset.activeDocId = "";
      form.dataset.reviewMode = "";
    }
    FL.evidence.revokeCaPreviewBlob();
    FL.evidence._caReviewSubmitInFlight = false;
  },

  setCriterionADrawerMode: function (mode) {
    const semesterPanel = document.getElementById("ca-tev-semester-panel");
    const documentPanel = document.getElementById("ca-tev-document-panel");
    const remarksWrap = document.getElementById("ca-tev-shared-remarks-wrap");
    const isDoc = mode === "document";
    if (semesterPanel) semesterPanel.hidden = isDoc;
    if (documentPanel) documentPanel.hidden = !isDoc;
    if (remarksWrap) remarksWrap.hidden = false;
    const title = document.getElementById("ca-tev-drawer-title");
    if (title) title.textContent = isDoc ? "Document review" : "Evaluation review";
  },

  loadCriterionAPdfPreview: function (docId, session) {
    const preview = document.getElementById("ca-tev-drawer-preview-frame");
    const actions = document.getElementById("ca-tev-drawer-pdf-actions");
    if (!preview) return Promise.resolve();
    if (FL.evidence._caPreviewDocId && FL.evidence._caPreviewDocId !== docId) {
      FL.evidence.revokeCaPreviewBlob();
    }
    FL.evidence._caPreviewDocId = docId;
    preview.innerHTML = "<p class=\"ca-preview-loading\" role=\"status\">Loading document preview…</p>";
    const cache = FL.evidence._caWorkspaceCache || {};
    let doc = (cache.docs || []).find(function (d) { return d.id === docId; });
    const resolveDoc = function () {
      if (doc && doc.fileApiPath) return Promise.resolve(doc);
      return FL.store.refreshLiveDocument(session, docId).then(function (fresh) {
        if (fresh) {
          doc = fresh;
          const idx = (cache.docs || []).findIndex(function (d) { return d.id === docId; });
          if (idx >= 0) cache.docs[idx] = fresh;
        }
        return doc;
      });
    };
    return resolveDoc().then(function (d) {
      if (!d || !d.fileApiPath) {
        preview.innerHTML = "<p class=\"ca-preview-error\">This document file is not available for preview.</p>";
        return;
      }
      const name = d.fileName || d.name || "document";
      if (actions) {
        actions.innerHTML = `
          <button type="button" class="btn btn-ghost btn-small" data-ca-pdf-open>Open full document</button>
          <button type="button" class="btn btn-ghost btn-small" data-ca-pdf-download>Download</button>`;
        actions.querySelector("[data-ca-pdf-open]").addEventListener("click", function () {
          FL.documents.hydrateAuthenticatedFile(d, { previewDocId: docId }).then(function (hydrated) {
            const url = FL.documents.inlineFileUrl(hydrated);
            if (url) window.open(url, "_blank", "noopener");
            else FL.ui.toast("Could not open the document.", "danger");
          }).catch(function (err) {
            FL.ui.toast(err.message || "Could not open the document.", "danger");
          });
        });
        actions.querySelector("[data-ca-pdf-download]").addEventListener("click", function () {
          FL.documents.downloadAuthenticatedFile(d, name).catch(function (err) {
            FL.ui.toast(err.message || "Download failed.", "danger");
          });
        });
      }
      return FL.documents.hydrateAuthenticatedFile(d, { previewDocId: docId }).then(function (hydrated) {
        const url = FL.documents.inlineFileUrl(hydrated);
        if (!url) {
          preview.innerHTML = "<p class=\"ca-preview-error\">Preview could not be prepared.</p>";
          return;
        }
        FL.evidence._caPreviewObjectUrl = hydrated._objectUrl;
        preview.innerHTML = "<iframe title=\"PDF preview\" src=\"" + FL.esc(url) + "#toolbar=0\" class=\"tev-drawer-iframe ca-tev-drawer-iframe\"></iframe>";
      });
    }).catch(function (error) {
      const msg = error.message || "Preview failed.";
      preview.innerHTML = "<div class=\"ca-preview-error\"><p>" + FL.esc(msg) + "</p>"
        + "<button type=\"button\" class=\"btn btn-ghost btn-small\" data-ca-preview-retry>Retry</button></div>";
      const retry = preview.querySelector("[data-ca-preview-retry]");
      if (retry) {
        retry.addEventListener("click", function () {
          FL.evidence.loadCriterionAPdfPreview(docId, session);
        });
      }
    });
  },

  openCriterionAReviewDrawer: function (tevId, docId, canReview) {
    const ui = FL.criterionAWorkspaceUi;
    const cache = FL.evidence._caWorkspaceCache || {};
    const row = (cache.records || []).find(function (r) {
      return r.teachingEvaluationId === tevId;
    });
    if (!row) return;
    const drawer = FL.evidence.mountCriterionADrawerToBody();
    if (!drawer) return;
    FL.evidence.setCriterionADrawerMode("semester");
    const form = document.getElementById("ca-tev-drawer-form");
    if (form) {
      form.dataset.reviewMode = "semester";
      form.dataset.activeTevId = tevId;
      form.dataset.activeDocId = docId;
    }
    document.getElementById("ca-tev-drawer-type").value = row.evaluationType === "SET" || row.evaluationType === "SEF" ? row.evaluationType : "";
    document.getElementById("ca-tev-drawer-year").value = row.academicYear || "";
    document.getElementById("ca-tev-drawer-sem").value = row.semester || "";
    document.getElementById("ca-tev-drawer-rating").value = row.ratingRaw || "";
    document.getElementById("ca-tev-drawer-scale").value = row.ratingScale != null ? String(row.ratingScale) : "";
    document.getElementById("ca-tev-drawer-remarks").value = row.reviewerRemarks || "";
    const period = (row.academicYear || "Year not listed") + " · " + (row.semester || "Semester not listed");
    const sub = document.getElementById("ca-tev-drawer-subtitle");
    if (sub) sub.textContent = period;
    const facultyDisplay = document.getElementById("ca-tev-drawer-faculty-display");
    const facultyNote = document.getElementById("ca-tev-drawer-faculty-note");
    if (facultyDisplay) {
      if (ui) {
        const fMeta = ui.facultyNameDisplayMeta(row);
        const verifyLabel = fMeta.verificationLabel || (fMeta.needsVerification ? "Needs Manual Review" : "Name Matched");
        if (verifyLabel && verifyLabel !== "Name Matched" && FL.ui && FL.ui.badge) {
          const tone = verifyLabel === "Name Mismatch" ? "invalid" : "pending";
          facultyDisplay.innerHTML = FL.ui.badge(tone, verifyLabel)
            + " <span class=\"ca-drawer-faculty-extracted\">" + FL.esc(ui.formatFacultyNameLabel(row)) + "</span>";
        } else {
          facultyDisplay.textContent = ui.formatFacultyNameLabel(row);
        }
        if (facultyNote) {
          if (fMeta.note) {
            facultyNote.textContent = fMeta.note;
            facultyNote.hidden = false;
            facultyNote.className = fMeta.needsVerification
              ? "field-span ca-drawer-faculty-note alert alert-warning"
              : "field-span ca-drawer-faculty-note note";
          } else {
            facultyNote.hidden = true;
            facultyNote.textContent = "";
            facultyNote.className = "field-span ca-drawer-faculty-note";
          }
        }
      } else {
        facultyDisplay.textContent = row.facultyName || "Not detected";
        if (facultyNote) facultyNote.hidden = true;
      }
    }
    const ratingDisplay = document.getElementById("ca-tev-drawer-rating-display");
    if (ratingDisplay) {
      const ratingLabel = ui ? ui.formatExtractedRating(row) : (row.ratingRaw != null && row.ratingRaw !== "" ? String(row.ratingRaw) : "Not extracted");
      ratingDisplay.textContent = ratingLabel === "—" ? "Not extracted" : ratingLabel;
    }
    const statusSlot = document.getElementById("ca-tev-drawer-status-slot");
    if (statusSlot) statusSlot.innerHTML = FL.evidence.criterionAStatusPill(row);
    const tech = document.getElementById("ca-tev-drawer-tech-slot");
    if (tech && FL.documents && FL.documents.tevTechnicalDetailsHtml) {
      tech.innerHTML = FL.documents.tevTechnicalDetailsHtml({
        id: tevId,
        extractionStatus: row.extractionStatus,
        ocrVerificationStatus: row.ocrVerificationStatus,
        sourceSectionRef: row.sourceSectionRef,
        missingFields: row.missingFields,
        duplicatePeriodWarning: row.duplicatePeriodWarning
      });
    }
    const session = cache.session || FL.store.resolveReviewerSession(null);
    const uiStatus = FL.tevReviewUi ? FL.tevReviewUi.statusLabel({
      evaluationType: row.evaluationType,
      reviewerValidationStatus: row.reviewerValidationStatus || row.reviewDisplayStatus,
      incompleteExtraction: row.incompleteExtraction,
      extractionStatus: row.extractionStatus
    }) : "Pending Review";
    FL.evidence.renderCriterionADrawerActions({
      mode: "semester",
      canReview: canReview,
      row: row,
      statusLabel: uiStatus
    });
    FL.evidence.loadCriterionAPdfPreview(docId, session);
    const formCol = drawer.querySelector(".ca-tev-drawer-col--form");
    if (formCol) formCol.scrollTop = 0;
    FL.evidence._lockCaDrawerPageScroll();
    drawer.classList.add("is-open");
    drawer.setAttribute("aria-hidden", "false");
    document.body.classList.add("tev-drawer-open", "ca-tev-drawer-open");
  },

  openCriterionADocumentReviewDrawer: function (docId, canReview) {
    const cache = FL.evidence._caWorkspaceCache || {};
    const ui = FL.criterionAWorkspaceUi;
    const drawer = FL.evidence.mountCriterionADrawerToBody();
    if (!drawer || !docId) return;
    FL.evidence.setCriterionADrawerMode("document");
    FL.evidence.renderCriterionADrawerActions({ mode: "document", canReview: canReview });
    const form = document.getElementById("ca-tev-drawer-form");
    if (form) {
      form.dataset.reviewMode = "document";
      form.dataset.activeDocId = docId;
      form.dataset.activeTevId = "";
    }
    const errEl = document.getElementById("ca-tev-drawer-error");
    if (errEl) errEl.textContent = "";
    document.getElementById("ca-tev-drawer-remarks").value = "";
    const statusSlot = document.getElementById("ca-tev-drawer-status-slot");
    const sub = document.getElementById("ca-tev-drawer-subtitle");
    if (sub) sub.textContent = "";
    const session = cache.session || FL.store.resolveReviewerSession(null);
    const resolveDoc = function () {
      let doc = (cache.docs || []).find(function (d) { return d.id === docId; });
      if (doc && doc.documentInformation) return Promise.resolve(doc);
      return FL.store.refreshLiveDocument(session, docId).then(function (fresh) {
        if (fresh) {
          const idx = (cache.docs || []).findIndex(function (d) { return d.id === docId; });
          if (idx >= 0) cache.docs[idx] = fresh;
          else if (cache.docs) cache.docs.push(fresh);
          doc = fresh;
        }
        return doc;
      });
    };
    resolveDoc().then(function (doc) {
      if (!doc) {
        if (errEl) errEl.textContent = "Document could not be loaded.";
        return;
      }
      const sources = (cache.payload && cache.payload.criterionAWorkspace && cache.payload.criterionAWorkspace.sourceDocuments) || [];
      const sourceRow = sources.find(function (s) { return s.documentId === docId; });
      const infoSlot = document.getElementById("ca-tev-document-info-slot");
      if (infoSlot && FL.documents && FL.documents.documentInformationHtml) {
        const block = doc.documentInformation || {};
        infoSlot.innerHTML = FL.documents.documentInformationHtml(doc, block);
      }
      if (statusSlot) {
        const st = doc.reviewDisplayStatus || doc.status || "pending-review";
        statusSlot.innerHTML = FL.evidence.statusBadge(st);
      }
      if (sub) {
        const fileLabel = FL.evidence.criterionAShortDocLabel(doc.fileName || doc.name || doc.id, 56);
        sub.textContent = fileLabel;
      }
      const linked = document.getElementById("ca-tev-document-linked");
      const linkedRows = (cache.records || []).filter(function (r) { return r.documentId === docId; });
      if (linked && linkedRows.length) {
        linked.hidden = false;
        linked.innerHTML = "<h4 class=\"ca-section-subtitle\">Extracted semester records</h4>"
          + "<p class=\"note\">Open a row to validate that semester independently.</p><ul class=\"ca-doc-linked-list\">"
          + linkedRows.map(function (r) {
            const period = ui ? ui.formatPeriodLabel(r) : (r.academicYear || "—");
            const type = r.evaluationType || "Evaluation";
            return `<li><button type="button" class="btn btn-ghost btn-small" data-ca-tev-review="${FL.esc(r.teachingEvaluationId)}" data-ca-doc-id="${FL.esc(docId)}">${FL.esc(type)} · ${FL.esc(period)}</button></li>`;
          }).join("") + "</ul>";
      } else if (linked) {
        linked.hidden = true;
        linked.innerHTML = "";
      }
      const corrBody = document.getElementById("ca-tev-document-correction-body");
      const corrWrap = document.getElementById("ca-tev-document-corrections-wrap");
      if (corrBody && FL.documents && FL.documents.extractionCorrectionHtml) {
        corrBody.innerHTML = FL.documents.extractionCorrectionHtml(doc, canReview);
        const inlineSave = corrBody.querySelector("#save-extraction");
        if (inlineSave) inlineSave.remove();
        if (corrWrap) corrWrap.hidden = !(canReview && corrBody.textContent.trim());
      }
      FL.evidence._caActiveDocument = doc;
      FL.evidence.renderCriterionADrawerActions({ mode: "document", canReview: canReview });
      FL.evidence.loadCriterionAPdfPreview(docId, session);
    }).catch(function (error) {
      if (errEl) errEl.textContent = error.message || "Could not load document.";
    });
    const formCol = drawer.querySelector(".ca-tev-drawer-col--form");
    if (formCol) formCol.scrollTop = 0;
    FL.evidence._lockCaDrawerPageScroll();
    drawer.classList.add("is-open");
    drawer.setAttribute("aria-hidden", "false");
    document.body.classList.add("tev-drawer-open", "ca-tev-drawer-open");
  },

  submitCriterionADocumentMetadataCorrection: function (session, doc) {
    const error = document.getElementById("corr-error");
    const errDrawer = document.getElementById("ca-tev-drawer-error");
    const cache = FL.evidence._caWorkspaceCache || {};
    if (!FL.documents || !FL.validation || !doc) {
      return Promise.reject(new Error("Correction is not available."));
    }
    if (error) error.textContent = "";
    if (errDrawer) errDrawer.textContent = "";
    const reasonEl = document.getElementById("corr-reason");
    const reason = (reasonEl && reasonEl.value || "").trim();
    if (reason.length < 8) {
      const msg = "Enter a brief reason for the correction (at least 8 characters).";
      if (error) error.textContent = msg;
      if (errDrawer) errDrawer.textContent = msg;
      return Promise.reject(new Error(msg));
    }
    const fields = FL.validation.fields(doc);
    const baseline = {
      facultyName: (fields.authorValue || "").trim(),
      extractedTitle: (fields.titleValue || "").trim(),
      academicYear: (fields.dateValue || "").trim(),
      academicTerm: (FL.validation.infoValue(doc, "Academic term") || "").trim()
    };
    const payload = { reason: reason };
    const faculty = (document.getElementById("corr-faculty").value || "").trim();
    const title = (document.getElementById("corr-title").value || "").trim();
    const year = (document.getElementById("corr-date").value || "").trim();
    const term = (document.getElementById("corr-term").value || "").trim();
    if (faculty && faculty !== baseline.facultyName) payload.facultyName = faculty;
    if (title && title !== baseline.extractedTitle) payload.extractedTitle = title;
    if (year && year !== baseline.academicYear) payload.academicYear = year;
    if (term && term !== baseline.academicTerm) payload.academicTerm = term;
    const ratingEl = document.getElementById("corr-rating");
    if (ratingEl) {
      const rating = (ratingEl.value || "").trim();
      const baseRating = (ratingEl.defaultValue || "").trim();
      if (rating && rating !== baseRating) payload.evaluationRating = rating;
    }
    const evalTypeInput = document.getElementById("corr-eval-type");
    if (evalTypeInput) {
      const et = (evalTypeInput.value || "").trim();
      if (et && et !== (evalTypeInput.defaultValue || "").trim()) payload.evaluationType = et;
    }
    const scaleInput = document.getElementById("corr-scale");
    if (scaleInput) {
      const sc = (scaleInput.value || "").trim();
      if (sc && sc !== (scaleInput.defaultValue || "").trim()) payload.ratingScale = sc;
    }
    const evidence = document.getElementById("corr-evidence");
    if (evidence && evidence.checked) payload.attestSupportingEvidence = true;
    if (!payload.attestSupportingEvidence && Object.keys(payload).length === 1) {
      const msg = "Change at least one extracted field before saving.";
      if (error) error.textContent = msg;
      if (errDrawer) errDrawer.textContent = msg;
      return Promise.reject(new Error(msg));
    }
    return FL.store.correctDocumentMetadata(doc.id, payload, session).then(function (saved) {
      if (saved && typeof saved === "object") Object.assign(doc, saved);
      FL.evidence._caActiveDocument = doc;
      FL.ui.toast("Extracted information updated.", "ok");
      const refreshFn = cache.onRefresh || FL.evidence._refreshCriterionATeaching;
      if (typeof refreshFn === "function") return Promise.resolve(refreshFn(false));
    });
  },

  bindCriterionADocumentReviewActions: function (canReview) {
    if (!canReview || FL.evidence._caDocReviewActionsBound) return;
    FL.evidence._caDocReviewActionsBound = true;
    document.addEventListener("click", function (ev) {
      const btn = ev.target.closest("#ca-tev-review-drawer [data-ca-doc-decision]");
      if (!btn) return;
      const form = document.getElementById("ca-tev-drawer-form");
      if (!form || form.dataset.reviewMode !== "document") return;
      const cache = FL.evidence._caWorkspaceCache || {};
      const docId = form.dataset.activeDocId;
      const doc = FL.evidence._caActiveDocument || (cache.docs || []).find(function (d) { return d.id === docId; });
      if (!doc || !docId) return;
      if (FL.evidence._caReviewSubmitInFlight) return;
      const decision = btn.getAttribute("data-ca-doc-decision");
      const errEl = document.getElementById("ca-tev-drawer-error");
      if (errEl) errEl.textContent = "";
      const remarks = (document.getElementById("ca-tev-drawer-remarks").value || "").trim();
      const session = FL.store.resolveReviewerSession(cache.session);
      if (decision === "revision" || decision === "reject") {
        if (remarks.length < 8) {
          if (errEl) errEl.textContent = "Add remarks (at least 8 characters) for revision or rejection.";
          return;
        }
        const apiDecision = decision === "revision" ? "revision" : "reject";
        FL.evidence._caReviewSubmitInFlight = true;
        FL.evidence._setCriterionADrawerActionsDisabled(true);
        FL.store.submitDocumentReview(doc, apiDecision, remarks, session).then(function () {
          FL.evidence.closeCriterionAReviewDrawer();
          FL.ui.toast(apiDecision === "reject" ? "Document rejected." : "Revision requested.", "ok");
          const refreshFn = cache.onRefresh || FL.evidence._refreshCriterionATeaching;
          if (typeof refreshFn === "function") return Promise.resolve(refreshFn(false));
        }).catch(function (error) {
          if (errEl) errEl.textContent = error.message || "Could not save decision.";
          FL.ui.toast(error.message || "Could not save decision.", "danger");
        }).then(function () {
          FL.evidence._caReviewSubmitInFlight = false;
          FL.evidence._setCriterionADrawerActionsDisabled(false);
        });
        return;
      }
      if (decision === "save-metadata") {
        FL.evidence._caReviewSubmitInFlight = true;
        FL.evidence._setCriterionADrawerActionsDisabled(true);
        FL.evidence.submitCriterionADocumentMetadataCorrection(session, doc).catch(function (error) {
          const corrErr = document.getElementById("corr-error");
          if (errEl && !(corrErr && corrErr.textContent)) {
            errEl.textContent = error.message || "The correction was not saved.";
          }
          FL.ui.toast(error.message || "The correction was not saved.", "danger");
        }).then(function () {
          FL.evidence._caReviewSubmitInFlight = false;
          FL.evidence._setCriterionADrawerActionsDisabled(false);
        });
      }
    });
  },

  _setCriterionADrawerActionsDisabled: function (disabled) {
    const host = document.getElementById("ca-tev-drawer-actions");
    if (!host) return;
    host.querySelectorAll("button").forEach(function (b) {
      b.disabled = !!disabled;
    });
  },

  bindCriterionAReviewActions: function (canReview) {
    if (!canReview || FL.evidence._caReviewActionsBound) return;
    FL.evidence._caReviewActionsBound = true;
    document.addEventListener("click", function (ev) {
      const btn = ev.target.closest("#ca-tev-review-drawer [data-ca-tev-decision]");
      if (!btn) return;
      const cache = FL.evidence._caWorkspaceCache || {};
      const form = document.getElementById("ca-tev-drawer-form");
      if (!form || form.dataset.reviewMode === "document") return;
      const decision = btn.getAttribute("data-ca-tev-decision");
      const tevId = form && form.dataset.activeTevId;
      const docId = form && form.dataset.activeDocId;
      if (!tevId || !docId) return;
      if (FL.evidence._caReviewSubmitInFlight) return;
      const list = cache.records || [];
      const idx = list.findIndex(function (r) {
        return (r.teachingEvaluationId || r.id) === tevId;
      });
      if (idx < 0) return;
      const errEl = document.getElementById("ca-tev-drawer-error");
      if (errEl) errEl.textContent = "";
      const baseline = list[idx];
      const remarks = (document.getElementById("ca-tev-drawer-remarks").value || "").trim();
      const payload = { remarks: remarks, reason: remarks };
      const typeVal = (document.getElementById("ca-tev-drawer-type").value || "").trim();
      const yearVal = (document.getElementById("ca-tev-drawer-year").value || "").trim();
      const semVal = (document.getElementById("ca-tev-drawer-sem").value || "").trim();
      const ratingVal = (document.getElementById("ca-tev-drawer-rating").value || "").trim();
      const scaleVal = (document.getElementById("ca-tev-drawer-scale").value || "").trim();
      if (typeVal && typeVal !== (baseline.evaluationType || "")) payload.evaluationType = typeVal;
      if (yearVal && yearVal !== (baseline.academicYear || "")) payload.academicYear = yearVal;
      if (semVal && semVal !== (baseline.semester || "")) payload.semester = semVal;
      if (ratingVal && ratingVal !== (baseline.ratingRaw || "")) payload.ratingRaw = ratingVal;
      if (scaleVal && String(baseline.ratingScale != null ? baseline.ratingScale : "") !== scaleVal) {
        payload.ratingScale = scaleVal;
      }
      if (decision !== "save") payload.decision = decision;
      if ((decision === "reject" || decision === "revision") && remarks.length < 8) {
        if (errEl) errEl.textContent = "Add remarks (at least 8 characters) for revision or rejection.";
        return;
      }
      const hasFieldChange = payload.evaluationType || payload.academicYear || payload.semester
        || payload.ratingRaw || payload.ratingScale;
      if ((decision === "save" || hasFieldChange) && remarks.length < 8) {
        if (errEl) errEl.textContent = "Add remarks explaining corrections (at least 8 characters).";
        return;
      }
      if (decision === "save" && !hasFieldChange) {
        if (errEl) errEl.textContent = "Change a field or choose Validate, Request revision, or Reject.";
        return;
      }
      const toastOk = {
        approve: "Evaluation validated.",
        reject: "Evaluation rejected.",
        revision: "Revision requested.",
        save: "Corrections saved."
      };
      const session = FL.store.resolveReviewerSession(cache.session);
      FL.evidence._caReviewSubmitInFlight = true;
      FL.evidence._setCriterionADrawerActionsDisabled(true);
      FL.store.submitTeachingEvaluationReview(session, docId, tevId, payload).then(function (data) {
        FL.evidence.closeCriterionAReviewDrawer();
        FL.ui.toast(toastOk[decision] || "Review saved.", "ok");
        const refreshFn = typeof cache.onRefresh === "function"
          ? cache.onRefresh
          : FL.evidence._refreshCriterionATeaching;
        if (typeof refreshFn === "function") {
          return Promise.resolve(refreshFn(false)).catch(function (refreshErr) {
            if (typeof console !== "undefined" && console.warn) {
              console.warn("Workspace refresh after validation failed:", refreshErr);
            }
            FL.ui.toast("Your decision was saved, but the workspace could not refresh. Reload if status looks stale.", "warning");
          });
        }
      }).catch(function (error) {
        const msg = error.message || "Could not save review.";
        if (errEl) errEl.textContent = msg;
        FL.ui.toast(msg, "danger");
      }).then(function () {
        FL.evidence._caReviewSubmitInFlight = false;
        FL.evidence._setCriterionADrawerActionsDisabled(false);
      });
    });
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
          { label: "Source PDFs (total)", value: stats.totalDocuments, iconKey: "documents", accent: "" },
          { label: "Source PDFs pending", value: stats.pendingReview, iconKey: "pending", accent: "warn" },
          { label: "Source PDFs approved", value: stats.approvedEvidence, iconKey: "approved", accent: "ok" },
          { label: "SET/SEF records pending", value: stats.evaluationRecordsPending, iconKey: "pending", accent: "warn" },
          { label: "SET/SEF records validated", value: stats.evaluationRecordsValidated, iconKey: "approved", accent: "ok" }
        ]
      : [
          { label: "Assigned faculty", value: stats.assignedFaculty ?? stats.facultyWithDocuments, iconKey: "faculty", accent: "teal" },
          { label: "Source PDFs pending", value: stats.pendingReview, iconKey: "pending", accent: "warn" },
          { label: "Source PDFs approved", value: stats.approvedEvidence, iconKey: "approved", accent: "ok" },
          { label: "Needs revision (PDFs)", value: stats.needsRevision, iconKey: "revision", accent: "warn" }
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
    if (state.criterionId === "kra1-a" && FL.store.usesLiveDocuments()) {
      const loadFaculty = state.facultyId;
      const loadCriterion = state.criterionId;
      const fetchSeq = (FL.evidence._teFetchSeq = (FL.evidence._teFetchSeq || 0) + 1);
      host.innerHTML = `<h2 class="evidence-section-title">${FL.esc(criterion.name)}</h2>
        <div id="criterion-a-summary-slot">${FL.ui.loading("Loading Teaching Effectiveness summary…")}</div>
        <div id="criterion-a-section10-slot">${FL.ui.loading("Loading Section 10 eligibility…")}</div>
        <div id="criterion-a-workspace-slot">${FL.ui.loading("Loading supporting documents…")}</div>`;
      const slot = function () { return document.getElementById("criterion-a-summary-slot"); };
      const s10Slot = function () { return document.getElementById("criterion-a-section10-slot"); };
      const editableS10 = !isAdmin && session.role === "reviewer";
      let paintCriterionWorkspace;
      const refreshTeachingEffectiveness = function () {
        return FL.store.fetchTeachingEffectiveness(session, loadFaculty).then(function (payload) {
          if (fetchSeq !== FL.evidence._teFetchSeq) return payload;
          if (loadFaculty !== state.facultyId || loadCriterion !== state.criterionId) return payload;
          FL.store.pruneSetSefDocumentsFromTeachingPayload(loadFaculty, payload);
          const s = slot();
          if (s) s.innerHTML = FL.evidence.criterionASummaryHtml(payload, { reviewerView: !isAdmin });
          paintCriterionWorkspace(payload);
          return payload;
        });
      };
      paintCriterionWorkspace = function (tePayload, repaintOnly) {
        const wsSlot = document.getElementById("criterion-a-workspace-slot");
        if (!wsSlot) return;
        const scrollY = window.scrollY || 0;
        const canReviewWs = !isAdmin && session && session.role === "reviewer";
        const skipDrawer = !!document.getElementById("ca-tev-review-drawer");
        wsSlot.innerHTML = FL.evidence.criterionAUnifiedWorkspaceHtml(
          session, state, isAdmin, tePayload, docs, { skipDrawer: skipDrawer }
        );
        if (!skipDrawer) FL.evidence.ensureCriterionADrawerOnBody(canReviewWs);
        FL.evidence.pruneDuplicateCriterionADrawers();
        FL.evidence.bindCriterionAWorkspace(session, state, isAdmin, tePayload, docs, function (localRepaint) {
          if (localRepaint && tePayload) {
            paintCriterionWorkspace(tePayload, true);
            return;
          }
          refreshTeachingEffectiveness().catch(function (refreshErr) {
            if (typeof console !== "undefined" && console.warn) {
              console.warn("Teaching effectiveness workspace refresh failed:", refreshErr);
            }
            FL.ui.toast("Your decision was saved, but the list could not be refreshed. Reload if counts look stale.", "warning");
          });
        });
        if (repaintOnly) window.scrollTo(0, scrollY);
      };
      FL.evidence._refreshCriterionATeaching = refreshTeachingEffectiveness;
      const paintS10 = function (elig) {
        const el = s10Slot();
        if (!el || fetchSeq !== FL.evidence._teFetchSeq) return;
        el.innerHTML = FL.evidence.section10PanelHtml(elig, editableS10);
        FL.evidence.bindSection10Panel(session, loadFaculty, editableS10, onS10Saved);
      };
      const onS10Saved = function () {
        FL.store.fetchEvaluationEligibility(session, loadFaculty).then(function (updated) {
          paintS10(updated);
          refreshTeachingEffectiveness();
        });
      };
      Promise.all([
        FL.store.loadFacultyDocuments(session, loadFaculty),
        refreshTeachingEffectiveness(),
        FL.store.fetchEvaluationEligibility(session, loadFaculty).then(paintS10)
      ]).catch(function () {
        if (fetchSeq !== FL.evidence._teFetchSeq) return;
        const s = slot();
        if (s) s.innerHTML = "";
        const s10 = s10Slot();
        if (s10) s10.innerHTML = "";
        paintCriterionWorkspace(null);
      });
      return;
    }
    host.innerHTML = `<h2 class="evidence-section-title">${FL.esc(criterion.name)}</h2>
      <div id="criterion-a-summary-slot"></div>
      <div id="criterion-a-section10-slot"></div>
      <div id="criterion-a-workspace-slot">${FL.evidence.criterionAUnifiedWorkspaceHtml(session, state, isAdmin, null, docs)}</div>`;
  },

  _paintIndicatorDocs: function (session, state, isAdmin) {
    if (state.criterionId === "kra1-a" && FL.evidence.isSetSefIndicator(state.indicatorId)) {
      state.indicatorId = "";
      FL.evidence.pushLocation(state);
      FL.evidence._paintCriteria(session, state, isAdmin);
      return;
    }
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
    const rows = (block && (block.evaluationRecords || block.documents)) || [];
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
      doc.teachingEvaluationId = row.teachingEvaluationId || row.id;
      const href = FL.evidence.reviewDocHref(doc, reviewBase);
      const fileName = row.fileName || doc.fileName || doc.id;
      const ocrV = row.extractionStatus || row.ocrVerificationStatus
        || (doc.extractedInfo && doc.extractedInfo["SET/SEF extraction status"])
        || (doc.extractedInfo && doc.extractedInfo["Indicator verification status"]) || "—";
      const displaySt = row.reviewerValidationStatus
        || row.reviewDisplayStatus
        || (row.incompleteExtraction ? "incomplete-extraction" : null)
        || row.reviewBucket
        || "pending-review";
      const evalType = row.evaluationType || "—";
      return `<tr>
        <td>${FL.esc(evalType)}</td>
        <td>${FL.esc(row.academicYear || "—")}</td>
        <td>${FL.esc(row.semester || "—")}</td>
        <td><a class="set-sef-file-link" href="${href}">${FL.esc(fileName)}</a>${row.sourceSectionRef ? `<div class="sub">${FL.esc(row.sourceSectionRef)}</div>` : ""}</td>
        <td>${FL.esc(row.ratingRaw || "—")}</td>
        <td>${FL.esc(row.ratingScale != null ? row.ratingScale : "—")}</td>
        <td>${FL.esc(ocrV)}</td>
        <td>${FL.evidence.statusBadge(displaySt === "accepted" ? "approved" : displaySt)}</td>
        <td>${FL.evidence.setSefRecordWarningsHtml(row)}</td>
      </tr>`;
    }).join("") : "";

    const srcDocs = (block && block.sourceDocuments) || [];
    const srcHtml = srcDocs.length
      ? `<div class="set-sef-source-docs card-inset"><h3 class="evidence-section-title">Source PDFs</h3><ul class="set-sef-source-list">${srcDocs.map(function (s) {
          const href = FL.evidence.reviewDocHref(Object.assign({}, ctx, { id: s.documentId, fileName: s.fileName }), reviewBase);
          const proc = s.processing || {};
          return `<li><a href="${href}">${FL.esc(s.fileName || s.documentId)}</a>
            <div class="sub">${FL.esc(s.summaryLine || proc.composition || "—")} · OCR: ${FL.esc(proc.ocrStatus || "—")}</div>
            ${s.estimatedPointsExplanation ? `<div class="sub">${FL.esc(s.estimatedPointsExplanation)}</div>` : ""}</li>`;
        }).join("")}</ul></div>`
      : "";

    host.innerHTML = `${hit ? `<div class="evidence-indicator-head"><h2>${FL.esc(hit.indicator.name)}</h2></div>` : ""}
      ${srcHtml}
      <p class="note">Each row below is one extracted SET or SEF semester (child evaluation record). Parent PDF approval or simulation auto-accept does not validate these rows.</p>
      <div class="table-wrap set-sef-table-wrap">
        <table class="data set-sef-evidence-table">
          <thead><tr>
            <th>Type</th><th>Academic year</th><th>Semester</th><th>Source file / section</th><th>Overall rating</th>
            <th>Rating scale</th><th>OCR status</th><th>Reviewer validation</th><th>Flags</th>
          </tr></thead>
          <tbody>${tableBody || `<tr><td colspan="9" class="sub">No SET/SEF evaluation records yet.</td></tr>`}</tbody>
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
