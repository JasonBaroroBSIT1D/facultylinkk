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
      return `<div class="evidence-stat${accent}">
        <span class="evidence-stat-icon" aria-hidden="true">${FL.ui.statIcon(c.iconKey || "documents")}</span>
        <div class="evidence-stat-body">
          <span>${FL.esc(c.label)}</span>
          <strong>${FL.esc(String(val))}</strong>
          ${hint}
        </div>
      </div>`;
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
  const docs = FL.store.documents.filter(function (doc) { return doc.facultyId === facultyId; });
  let validated = 0;
  let missing = 0;
  let revision = 0;
  docs.forEach(function (doc) {
    const result = FL.validation.evaluate(doc);
    if (result.overall === "valid" && doc.status === "approved" && result.duplicateStatus !== "duplicate") validated += 1;
    if (result.overall === "invalid" || result.overall === "reviewer-required" || result.evidenceStatus === "missing") missing += 1;
    if (doc.status === "revision") revision += 1;
  });
  let status = "On track";
  if (!docs.length || validated === 0) status = "Incomplete";
  else if (missing || revision || validated < docs.length) status = "Needs attention";
  return {
    submitted: docs.length,
    validated: validated,
    missing: missing,
    revision: revision,
    status: status,
    ratio: docs.length ? validated / docs.length : 0
  };
};
