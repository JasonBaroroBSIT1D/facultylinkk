window.FL = window.FL || {};

FL.esc = function (value) {
  return String(value == null ? "" : value).replace(/[&<>"']/g, function (char) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char];
  });
};

FL.formatWhen = function (value) {
  if (!value) return "—";
  const dateOnly = /^\d{4}-\d{2}-\d{2}$/.test(value);
  const date = dateOnly ? new Date(value + "T00:00:00") : new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("en-PH", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: dateOnly ? undefined : "numeric",
    minute: dateOnly ? undefined : "2-digit"
  });
};

FL.splitWhen = function (value) {
  const date = /^\d{4}-\d{2}-\d{2}$/.test(value) ? new Date(value + "T00:00:00") : new Date(value);
  if (Number.isNaN(date.getTime())) return { date: value || "—", time: "—" };
  return {
    date: date.toLocaleDateString("en-PH", { year: "numeric", month: "short", day: "numeric" }),
    time: date.toLocaleTimeString("en-PH", { hour: "numeric", minute: "2-digit" })
  };
};

/** Human-readable stamp for document cards (date · time). */
FL.formatDocStamp = function (value) {
  if (!value) return "—";
  const parts = FL.splitWhen(value);
  if (!parts.time || parts.time === "—") return parts.date;
  return parts.date + " · " + parts.time;
};

FL.ui = {
  /** Compact date/time for data tables (single line desktop; clean two-line when narrow). */
  tableDateTimeHtml: function (value) {
    if (!value) return "—";
    const parts = FL.splitWhen(value);
    const title = FL.formatDocStamp(value);
    if (!parts.time || parts.time === "—") {
      return (
        '<span class="fl-table-datetime fl-table-datetime--date-only" title="' +
        FL.esc(title) +
        '">' +
        FL.esc(parts.date) +
        "</span>"
      );
    }
    return (
      '<span class="fl-table-datetime" title="' +
      FL.esc(title) +
      '"><span class="fl-table-datetime-date">' +
      FL.esc(parts.date) +
      '</span><span class="fl-table-datetime-sep" aria-hidden="true"> · </span><span class="fl-table-datetime-time">' +
      FL.esc(parts.time) +
      "</span></span>"
    );
  },

  statIcon: function (key) {
    const map = {
      faculty: "users",
      documents: "file-text",
      pending: "clock",
      approved: "circle-check",
      revision: "rotate-ccw",
      validation: "list-checks",
      reviewers: "user-check"
    };
    return FL.navIcons.icon(map[key] || "file-text");
  },

  pageHeader: function (options) {
    const opts = options || {};
    const actions = opts.actions ? `<div class="head-actions">${opts.actions}</div>` : "";
    return `<header class="portal-head page-head">
      <div>
        <p class="eyebrow">${FL.esc(opts.eyebrow || "FacultyLink")}</p>
        <h1>${FL.esc(opts.title || "")}</h1>
        ${opts.lede ? `<p class="lede">${FL.esc(opts.lede)}</p>` : ""}
      </div>
      ${actions}
    </header>`;
  },

  metricGrid: function (cards) {
    const list = cards || [];
    return `<div class="evidence-stats portal-metrics">${list.map(function (c) {
      const accent = c.accent ? " is-accent-" + c.accent : "";
      const val = c.value == null ? "—" : c.value;
      const hint = c.hint ? `<small>${FL.esc(c.hint)}</small>` : "";
      const inner = `<span class="evidence-stat-icon" aria-hidden="true">${FL.ui.statIcon(c.iconKey || "documents")}</span>
        <div class="evidence-stat-body">
          <span>${FL.esc(c.label)}</span>
          <strong>${FL.esc(String(val))}</strong>
          ${hint}
        </div>`;
      if (c.href) {
        return `<a class="evidence-stat evidence-stat-link${accent}" href="${FL.esc(c.href)}">${inner}</a>`;
      }
      return `<div class="evidence-stat${accent}">${inner}</div>`;
    }).join("")}</div>`;
  },

  badge: function (kind, label) {
    const map = {
      valid: "badge-valid",
      invalid: "badge-invalid",
      pending: "badge-pending",
      rejected: "badge-rejected",
      info: "badge-info",
      revision: "badge-pending"
    };
    return `<span class="badge ${map[kind] || "badge-info"}">${FL.esc(label)}</span>`;
  },

  statusBadge: function (status) {
    const map = {
      approved: ["valid", "Approved"],
      "review-complete": ["valid", "Review complete"],
      "approved-by-reviewer": ["valid", "Approved by reviewer"],
      "simulation-auto-accepted": ["valid", "Auto-accepted for simulation"],
      "incomplete-extraction": ["pending", "Incomplete extraction"],
      "simulation-reviewer-validated": ["valid", "Reviewer-validated for simulation"],
      "auto-approved": ["valid", "Auto-accepted for simulation"],
      "system-approved": ["valid", "System approved"],
      valid: ["valid", "Valid"],
      "pending-review": ["pending", "Pending review"],
      revision: ["revision", "Revision requested"],
      rejected: ["rejected", "Rejected"],
      invalid: ["invalid", "Invalid"],
      "reviewer-required": ["pending", "Reviewer validation required"],
      "ignored-duplicate": ["info", "Duplicate ignored"],
      processing: ["info", "Processing"],
      completed: ["valid", "Completed"],
      failed: ["invalid", "Failed"],
      pending: ["pending", "Pending"],
      unclassified: ["pending", "Cannot classify"],
      classified: ["valid", "Classified"],
      priority: ["info", "Classified by priority"],
      clear: ["valid", "No duplicate"],
      duplicate: ["rejected", "Duplicate"],
      complete: ["valid", "Complete"],
      missing: ["invalid", "Missing"],
      "On track": ["valid", "On track"],
      "Needs attention": ["pending", "Needs attention"],
      Incomplete: ["invalid", "Incomplete"],
      open: ["valid", "Open"],
      upcoming: ["info", "Upcoming"],
      closed: ["info", "Closed"],
      draft: ["pending", "Not published"]
    };
    const item = map[status] || ["info", status || "—"];
    return FL.ui.badge(item[0], item[1]);
  },

  empty: function (title, text) {
    return `<div class="empty"><strong>${FL.esc(title)}</strong><p>${FL.esc(text)}</p></div>`;
  },

  emptyWithRetry: function (title, text, retryId) {
    return `
      <div class="empty">
        <strong>${FL.esc(title)}</strong>
        <p>${FL.esc(text)}</p>
        <p><button type="button" class="btn btn-primary" id="${FL.esc(retryId)}">Retry</button></p>
      </div>`;
  },

  loading: function (title, text) {
    return `
      <div class="loading-block" role="status">
        <span class="spinner" aria-hidden="true"></span>
        <div>
          <strong>${FL.esc(title)}</strong>
          <p>${FL.esc(text || "Preparing this view.")}</p>
        </div>
      </div>`;
  },

  progress: function (value, max, label) {
    const safeMax = max || 1;
    const width = Math.max(0, Math.min(100, (value / safeMax) * 100));
    return `
      <div class="progress-line">
        <div class="progress-meta"><span>${FL.esc(label || "")}</span><span>${FL.esc(String(value))} / ${FL.esc(String(max))}</span></div>
        <div class="track" aria-hidden="true"><span style="width:${width}%"></span></div>
      </div>`;
  },

  toast: function (message, kind) {
    let host = document.getElementById("toasts");
    if (!host) {
      host = document.createElement("div");
      host.id = "toasts";
      host.className = "toasts";
      document.body.appendChild(host);
    }
    const item = document.createElement("div");
    item.className = "toast " + (kind || "info");
    item.textContent = message;
    host.appendChild(item);
    setTimeout(function () { item.remove(); }, 4200);
  },

  modal: function (options) {
    const existing = document.getElementById("modal-root");
    if (existing) existing.remove();
    const root = document.createElement("div");
    root.id = "modal-root";
    root.className = "modal-root";
    root.innerHTML = `
      <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <h2 id="modal-title">${FL.esc(options.title)}</h2>
        <div class="modal-body">${options.body}</div>
        <div class="modal-actions">
          <button class="btn btn-ghost" type="button" data-modal="cancel">${FL.esc(options.cancelLabel || "Cancel")}</button>
          ${options.confirmLabel ? `<button class="btn ${options.danger ? "btn-danger" : "btn-primary"}" type="button" data-modal="confirm">${FL.esc(options.confirmLabel)}</button>` : ""}
        </div>
      </div>`;
    document.body.appendChild(root);
    const close = function (result) {
      root.remove();
      if (options.onClose) options.onClose(result);
    };
    root.addEventListener("click", function (event) {
      if (event.target === root) close(false);
    });
    root.querySelector("[data-modal='cancel']").addEventListener("click", function () { close(false); });
    const confirm = root.querySelector("[data-modal='confirm']");
    if (confirm) {
      confirm.addEventListener("click", function () {
        if (confirm.disabled) return;
        if (!options.onConfirm) {
          close(true);
          return;
        }
        const result = options.onConfirm(root, confirm);
        if (result === false) return;
        if (result && typeof result.then === "function") {
          result.then(function (allowClose) {
            if (allowClose !== false) close(true);
          }).catch(function () {
            /* stay open; onConfirm restores button state */
          });
          return;
        }
        close(true);
      });
    }
    const field = root.querySelector("input, textarea, select");
    if (field) field.focus();
  },

  closeModal: function () {
    const root = document.getElementById("modal-root");
    if (root) root.remove();
  },

  setModalConfirmBusy: function (confirmBtn, busy, busyHtml, idleLabel, modalRoot) {
    if (!confirmBtn) return;
    if (!confirmBtn.dataset.idleLabel) {
      confirmBtn.dataset.idleLabel = confirmBtn.textContent.trim();
    }
    confirmBtn.disabled = !!busy;
    confirmBtn.setAttribute("aria-busy", busy ? "true" : "false");
    if (busy) {
      confirmBtn.innerHTML = busyHtml;
    } else {
      confirmBtn.textContent = idleLabel || confirmBtn.dataset.idleLabel || "Confirm";
    }
    if (modalRoot) {
      const cancel = modalRoot.querySelector("[data-modal='cancel']");
      if (cancel) cancel.disabled = !!busy;
    }
  }
};

FL.compliance = function (facultyId) {
  const cached = FL.store.evidenceComplianceByFaculty && FL.store.evidenceComplianceByFaculty[facultyId];
  if (cached) {
    const sem = cached.semesterEvaluations || {};
    return {
      submitted: cached.submittedDocuments != null ? cached.submittedDocuments : 0,
      validated: sem.validated != null ? sem.validated : 0,
      validatedDocumentsWorkflow: cached.validatedDocumentsWorkflow || 0,
      missing: (sem.pending || 0) + (sem.incomplete || 0) + (sem.needsRevision || 0),
      revision: sem.needsRevision || 0,
      rejected: sem.rejected || 0,
      status: cached.status || "Incomplete",
      statusLabel: cached.statusLabel || cached.status || "Incomplete",
      requirementsComplete: !!cached.requirementsComplete,
      semesterTotal: sem.total || 0,
      documentsPendingReview: cached.documentsPendingReview || 0,
      progressLabel: cached.progressLabel || "",
      notes: cached.notes || [],
      ratio: sem.total ? (sem.validated || 0) / sem.total : 0,
      fromServer: true
    };
  }

  const docs = FL.store.documents.filter(function (doc) { return doc.facultyId === facultyId; });
  let validatedDocs = 0;
  let missing = 0;
  let revision = 0;
  let semTotal = 0;
  let semValidated = 0;
  let pdfPending = 0;
  docs.forEach(function (doc) {
    const result = FL.validation.evaluate(doc);
    const ctx = doc.setSefParentContext || {};
    const child = ctx.allChildValidationSummary
      || (doc.teachingEvaluationSummary && doc.teachingEvaluationSummary.childValidationSummary)
      || null;
    if (child && child.total > 0) {
      semTotal += child.total;
      semValidated += child.validated || 0;
      const wf = doc.documentWorkflowStatus || doc.status;
      if (wf === "pending-review" || wf === "reviewer-required" || wf === "pending_review") {
        pdfPending += 1;
      }
    } else if (result.overall === "valid" && doc.status === "approved" && result.duplicateStatus !== "duplicate") {
      validatedDocs += 1;
    }
    if (result.overall === "invalid" || result.overall === "reviewer-required" || result.evidenceStatus === "missing") {
      missing += 1;
    }
    if (doc.status === "revision") revision += 1;
  });

  let status = "On track";
  let statusLabel = "On track";
  if (semTotal > 0) {
    if (semValidated === semTotal && pdfPending > 0) {
      status = "Needs attention";
      statusLabel = "Semester Evaluations Validated — Documents Pending Review";
    } else if (semValidated >= semTotal && pdfPending === 0) {
      status = "On track";
      statusLabel = "Requirements Complete";
    } else if (semValidated > 0) {
      status = "Needs attention";
      statusLabel = "Needs attention";
    } else {
      status = "Incomplete";
      statusLabel = "Incomplete";
    }
  } else if (!docs.length || validatedDocs === 0) {
    status = "Incomplete";
    statusLabel = "Incomplete";
  } else if (missing || revision || validatedDocs < docs.length) {
    status = "Needs attention";
    statusLabel = "Needs attention";
  }

  return {
    submitted: docs.length,
    validated: semTotal > 0 ? semValidated : validatedDocs,
    validatedDocumentsWorkflow: validatedDocs,
    missing: missing,
    revision: revision,
    status: status,
    statusLabel: statusLabel,
    semesterTotal: semTotal,
    documentsPendingReview: pdfPending,
    progressLabel: semTotal
      ? semValidated + " of " + semTotal + " semester evaluations validated"
      : validatedDocs + " of " + docs.length + " documents validated (workflow)",
    ratio: semTotal ? semValidated / semTotal : (docs.length ? validatedDocs / docs.length : 0)
  };
};
