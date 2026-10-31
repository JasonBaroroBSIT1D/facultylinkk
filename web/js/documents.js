window.FL = window.FL || {};

FL.documents = {
  scoped: function (session) {
    if (session.role === "administrator") return FL.store.documents.slice();
    const facultyIds = {};
    FL.store.assignedFacultyForReviewer(session).forEach(function (person) {
      facultyIds[person.id] = true;
    });
    if (!Object.keys(facultyIds).length) {
      FL.store.faculty.forEach(function (person) {
        if (person.reviewerId === session.userId) facultyIds[person.id] = true;
      });
    }
    return FL.store.documents.filter(function (doc) {
      return facultyIds[doc.facultyId] || doc.reviewerId === session.userId;
    });
  },

  needsAction: function (doc) {
    if (doc.status === "draft") return doc.hasFile !== false;
    if (doc.status === "invalid" || doc.status === "revision" || doc.status === "reviewer-required") return true;
    if (doc.status === "pending-review" || doc.status === "system-approved") return true;
    const oversight = doc.reviewerOversightStatus || (doc.extractedInfo && doc.extractedInfo["Reviewer oversight status"]) || "";
    if (oversight === "Awaiting Reviewer Check" || oversight === "Requires Review") return true;
    return false;
  },

  processingStatusLabel: function (doc) {
    const info = doc.extractedInfo || {};
    return info["Processing branch"] || info["Scoring status"] || doc.scoringStatus || "";
  },

  provisionalScore: function (doc) {
    const raw = doc.extractedInfo && doc.extractedInfo["Provisional score"];
    const value = Number(raw);
    return Number.isFinite(value) ? value : null;
  },

  isSetSefSemesterDocument: function (doc) {
    return doc.indicatorId === "kra1-a-student" || doc.indicatorId === "kra1-a-supervisor";
  },

  isCriterionATeachingDocument: function (doc) {
    if (!doc) return false;
    if (doc.criterionId === "kra1-a") return true;
    if (doc.indicatorId === "kra1-a-teaching-evidence") return true;
    if (doc.teachingEvaluations && doc.teachingEvaluations.length) return true;
    const info = doc.extractedInfo || {};
    return Boolean(
      info["Document evaluation composition"]
        || info["SET record count"]
        || info["Multi-semester document"] === "yes"
    );
  },

  invalidFacultyNameToken: function (name) {
    const lower = String(name || "").trim().toLowerCase();
    if (!lower || lower.length < 3) return true;
    const blocked = {
      rating: true, ratings: true, evaluation: true, evaluations: true,
      summary: true, individual: true, student: true, supervisor: true,
      teaching: true, faculty: true, name: true, semester: true, average: true
    };
    if (blocked[lower]) return true;
    if (lower.indexOf("rating") >= 0 && lower.indexOf("faculty") < 0) return true;
    return false;
  },

  facultyNameOnDocument: function (doc) {
    const block = doc.documentInformation;
    if (block && block.facultyName) {
      const name = String(block.facultyName).trim();
      if (name === "Needs Verification") return name;
      if (block.facultyNameSource === "profile") return name;
      if (name && name !== "—") return name;
    }
    const info = doc.extractedInfo || {};
    const status = (info["Faculty name extraction status"] || "").toLowerCase();
    const raw = (info["Faculty name on document"] || info["Faculty name"] || info["Extracted names"] || "").trim();
    if (status === "not_detected" || !raw) return "Not detected";
    if (FL.documents.invalidFacultyNameToken(raw)) return "Not detected";
    return raw;
  },

  documentInformationHtml: function (doc, block) {
    block = block || doc.documentInformation || {};
    const uploaded = block.dateUploaded
      ? FL.formatDocStamp(block.dateUploaded)
      : FL.formatDocStamp(doc.submittedAt || doc.uploadedAt || "");
    const verifyLabel = block.nameVerificationLabel || (block.needsVerification ? "Name Mismatch" : "Name Matched");
    const verifyMsg = block.nameVerificationMessage || block.facultyNameNote || "";
    let mismatch = "";
    if (verifyLabel === "Name Mismatch" || block.needsVerification) {
      mismatch = `<div class="alert alert-warning" role="status">${FL.esc(
        verifyMsg
          || "Faculty Name Mismatch — The document identifies a different faculty from the account owner."
      )}</div>`;
    } else if (verifyMsg) {
      mismatch = `<p class="note">${FL.esc(verifyMsg)}</p>`;
    }
    const onDocName = block.facultyNameOnDocument || block.documentNameOnFile || block.facultyName || "Not detected";
    const verifyBadge = verifyLabel === "Name Matched"
      ? FL.ui.badge("valid", verifyLabel)
      : verifyLabel === "Name Not Detected" || verifyLabel === "Needs Manual Review"
        ? FL.ui.badge("pending", verifyLabel)
        : FL.ui.badge("invalid", verifyLabel);
    const docType = block.documentType && block.documentType !== "—"
      ? FL.esc(String(block.documentType))
      : "—";
    return `
      <div class="card-head"><h2>Document information</h2></div>
      ${mismatch}
      <div class="kv-grid">
        ${FL.documents.kvRow("Account owner", FL.esc(block.uploadedBy || block.accountOwnerName || "—"), false)}
        ${FL.documents.kvRow("Faculty name on document", FL.esc(onDocName), onDocName === "Not detected")}
        ${FL.documents.kvRow("Name verification", verifyBadge, false)}
        ${FL.documents.kvRow("Date uploaded", uploaded, uploaded === "—")}
        ${FL.documents.kvRow("KRA", FL.esc(block.kraLabel || "—"), false)}
        ${FL.documents.kvRow("Criterion", FL.esc(block.criterionLabel || "—"), false)}
        ${FL.documents.kvRow("Document type", docType, docType === "—")}
        ${FL.documents.kvRow("OCR status", FL.esc(block.ocrStatus || FL.documents.ocrStatusLabel(doc)), false)}
        ${FL.documents.kvRow("Review status", FL.esc(block.reviewStatus || doc.status || "Pending Review"), false)}
      </div>`;
  },

  tevReviewerProgressLabel: function (doc) {
    const list = doc.teachingEvaluations || [];
    if (!list.length || !FL.tevReviewUi) return "—";
    const counts = FL.tevReviewUi.summaryCounts(list);
    return counts.reviewed + " of " + counts.total + " semester records reviewed";
  },

  setSefMetadataHtml: function (doc) {
    if (!FL.documents.isSetSefSemesterDocument(doc)) return "";
    const ctx = doc.setSefParentContext;
    const ctxBlock = ctx && typeof ctx === "object"
      ? `<section class="card-inset" aria-label="Parent PDF vs semester validation">
          <h3 class="review-subhead">Source PDF processing</h3>
          <p class="note">${FL.esc(ctx.summaryLine || ctx.composition || "—")}</p>
          ${ctx.processing ? `<p class="sub">OCR: ${FL.esc(ctx.processing.ocrStatus || "—")} · Workflow: ${FL.esc(ctx.processing.documentWorkflowStatus || doc.documentWorkflowStatus || doc.status || "—")}</p>` : ""}
          ${ctx.estimatedPointsExplanation ? `<p class="note">${FL.esc(ctx.estimatedPointsExplanation)}</p>` : ""}
          ${ctx.note ? `<p class="sub">${FL.esc(ctx.note)}</p>` : ""}
        </section>`
      : "";
    const info = doc.extractedInfo && typeof doc.extractedInfo === "object" ? doc.extractedInfo : {};
    const selected = doc.indicatorId && FL.rules.findIndicator(doc.indicatorId);
    const selectedLabel = selected ? selected.indicator.name : (doc.indicatorId || "—");
    const verification = String(info["Indicator verification status"] || "").trim() || "UNDETERMINED";
    const verificationKind = verification === "MATCH"
      ? "valid"
      : verification === "POSSIBLE_MISMATCH"
        ? "invalid"
        : verification === "PROCESSING_FAILED"
          ? "invalid"
          : "pending";
    const extractionStatus = info["SET/SEF extraction status"] || (doc.ocr && doc.ocr.status === "completed" ? "—" : "pending");
    const missing = info["Missing extraction fields"] || "";
    const rating = info["Extracted rating"] || "";
    const scale = info["Rating scale"] || "";
    return `${ctxBlock}
      <h3 class="review-subhead">SET / SEF extraction</h3>
      <div class="kv-grid kv-grid--two">
        ${FL.documents.kvRow("Faculty-selected indicator", FL.esc(selectedLabel), false)}
        ${FL.documents.kvRow("Detected evaluation type", info["Evaluation type"] ? FL.esc(String(info["Evaluation type"])) : "—", !info["Evaluation type"])}
        ${FL.documents.kvRow("Faculty name on document", (function () {
          const n = FL.documents.facultyNameOnDocument(doc);
          return n === "Not detected" ? FL.ui.badge("invalid", "Not detected") : FL.esc(n);
        })(), FL.documents.facultyNameOnDocument(doc) === "Not detected")}
        ${FL.documents.kvRow("Academic year", info["Academic year"] ? FL.esc(String(info["Academic year"])) : "—", !info["Academic year"])}
        ${FL.documents.kvRow("Semester", info["Semester"] ? FL.esc(String(info["Semester"])) : "—", !info["Semester"])}
        ${FL.documents.kvRow("Overall rating", rating ? FL.esc(String(rating)) : "—", !rating)}
        ${FL.documents.kvRow("Rating scale", scale ? FL.esc(String(scale)) : "—", !scale)}
        ${FL.documents.kvRow("Extraction status", FL.esc(String(extractionStatus)), extractionStatus === "failed")}
        ${FL.documents.kvRow("Indicator verification", FL.ui.badge(verificationKind, verification.replace(/_/g, " ")), verification !== "MATCH")}
      </div>
      ${missing ? `<p class="note">Missing or unresolved fields: ${FL.esc(String(missing))}</p>` : ""}
      ${info["Extraction error"] ? `<div class="alert alert-warning">${FL.esc(String(info["Extraction error"]))}</div>` : ""}`;
  },

  setSefAutoValidationHtml: function (doc) {
    if (!FL.documents.isSetSefSemesterDocument(doc)) return "";
    const av = doc.autoValidation || (doc.extractedInfo && doc.extractedInfo.autoValidation);
    if (!av || typeof av !== "object") return "";
    const checks = av.checks || {};
    const rows = [
      ["ocr_complete", "OCR completed"],
      ["metadata_validation", "Metadata validation"],
      ["evaluation_period_eligibility", "Evaluation-period eligibility"],
      ["ocr_extraction_quality", "OCR extraction quality"],
      ["file_accessible", "Original file preserved"]
    ];
    const list = rows.map(function (pair) {
      const row = checks[pair[0]];
      if (!row) return "";
      const mark = row.ok ? "✓" : "✗";
      const cls = row.ok ? "is-ok" : "is-fail";
      return `<li class="${cls}"><span aria-hidden="true">${mark}</span> <strong>${FL.esc(pair[1])}:</strong> ${FL.esc(row.message || "")}</li>`;
    }).join("");
    const source = av.decisionSource || doc.approvalDecisionSource || "—";
    const display = doc.reviewDisplayStatus
      || (source === "system_auto_approval" ? "simulation-auto-accepted" : doc.status);
    const showAuto = display === "simulation-auto-accepted" && doc.status === "approved";
    const withheld = (av.withheldReasons || []).length
      ? `<p class="note"><strong>Manual review required:</strong> ${FL.esc(av.withheldReasons.join(" "))}</p>`
      : "";
    return `
      <section class="card-inset auto-validation-panel" aria-label="Simulation auto-validation details">
        <h3 class="review-subhead">Simulation auto-validation</h3>
        <p class="note subtle">Auto-acceptance supports FacultyLink rank-upgrade simulation only. It is not official document authentication or CHED certification.</p>
        <div class="kv-grid kv-grid--two">
          ${FL.documents.kvRow("Review display status", FL.ui.statusBadge(showAuto ? "simulation-auto-accepted" : (display === "simulation-reviewer-validated" ? "simulation-reviewer-validated" : (doc.status || "pending-review"))), false)}
          ${FL.documents.kvRow("Decision source", FL.esc(String(source)), false)}
          ${FL.documents.kvRow("Policy version", av.policyVersion ? FL.esc(String(av.policyVersion)) : "—", false)}
          ${FL.documents.kvRow("Assessed at", av.assessedAt ? FL.esc(FL.formatDocStamp(av.assessedAt)) : "—", false)}
          ${FL.documents.kvRow("Approved at", av.approvedAt ? FL.esc(FL.formatDocStamp(av.approvedAt)) : "—", !av.approvedAt)}
        </div>
        ${list ? `<ul class="kra-publish-checks">${list}</ul>` : ""}
        ${withheld}
      </section>`;
  },

  periodSimulationDisplay: function (doc) {
    if (typeof doc.periodSimulationScore === "number") {
      return {
        score: doc.periodSimulationScore,
        filled: doc.evaluationPeriodFilled || (doc.extractedInfo && doc.extractedInfo["Evaluation period filled"]) || ""
      };
    }
    const info = doc.extractedInfo || {};
    const raw = info["SET period simulation score"] || info["SEF period simulation score"];
    const filled = info["Evaluation period filled"] || doc.evaluationPeriodFilled || "";
    if (raw && String(raw).trim()) {
      const score = Number(raw);
      if (Number.isFinite(score)) return { score: score, filled: filled };
    }
    if ((doc.indicatorId === "kra1-a-student" || doc.indicatorId === "kra1-a-supervisor") && filled) {
      return { score: null, filled: filled };
    }
    return null;
  },

  effectiveSimulationScore: function (doc) {
    if (typeof doc.effectiveSimulationScore === "number") return doc.effectiveSimulationScore;
    const info = doc.extractedInfo || {};
    if (info["Scoring status"] === "Score unavailable") return null;
    if (doc.status === "rejected" || doc.status === "invalid" || doc.status === "revision") return null;
    if (doc.status === "approved" && doc.review && typeof doc.review.finalScore === "number") {
      return doc.review.finalScore;
    }
    if (typeof doc.reviewerScore === "number") return doc.reviewerScore;
    if (info["Simulation eligible"] === "yes") {
      const system = Number(info["System-calculated score"] || info["Provisional score"]);
      return Number.isFinite(system) ? system : null;
    }
    return null;
  },

  simulationScoreSource: function (doc) {
    return doc.simulationScoreSource || (doc.extractedInfo && doc.extractedInfo["Simulation score source"]) || "Unavailable";
  },

  oversightStatusLabel: function (doc) {
    return doc.reviewerOversightStatus || (doc.extractedInfo && doc.extractedInfo["Reviewer oversight status"]) || "";
  },

  creditedPoints: function (doc) {
    if (doc.status === "approved" && doc.review && typeof doc.review.finalScore === "number") {
      return doc.review.finalScore;
    }
    if ((doc.status === "approved" || doc.status === "system-approved") && typeof doc.databasePoints === "number") {
      return doc.databasePoints;
    }
    return 0;
  },

  reviewJumpItems: function () {
    return [
      { href: "#document-area", label: "Document" },
      { href: "#ocr-area", label: "Extracted" },
      { href: "#classification", label: "Classification" },
      { href: "#rule", label: "DBM–CHED" },
      { href: "#validation", label: "Validation" },
      { href: "#scoring", label: "Scoring" },
      { href: "#contribution", label: "Contribution" },
      { href: "#workflow", label: "Workflow" },
      { href: "#decision", label: "Decision" }
    ];
  },

  reviewContextBackHref: function (doc, canDecide) {
    const params = new URLSearchParams(window.location.search);
    const facultyId = params.get("faculty") || doc.facultyId || "";
    const kraId = params.get("kra") || doc.kraId || "";
    const criterionId = params.get("criterion") || doc.criterionId || "";
    const indicatorId = params.get("indicator") || doc.indicatorId || "";
    if (facultyId && (indicatorId || kraId)) {
      const back = new URLSearchParams();
      back.set("faculty", facultyId);
      if (kraId) back.set("kra", kraId);
      if (criterionId) back.set("criterion", criterionId);
      if (indicatorId) back.set("indicator", indicatorId);
      return "documents.html?" + back.toString();
    }
    return canDecide ? "documents.html?filter=pending-review" : "documents.html";
  },

  reviewContextBackLabel: function (doc) {
    const params = new URLSearchParams(window.location.search);
    const indicatorId = params.get("indicator") || doc.indicatorId || "";
    if (indicatorId && FL.rules.findIndicator(indicatorId)) {
      return "Back to " + FL.rules.findIndicator(indicatorId).indicator.name;
    }
    return "Back to documents";
  },

  compactWorkflowHtml: function (doc, scored) {
    const ocrKey = FL.documents.ocrStatusLabel(doc);
    const info = doc.extractedInfo || {};
    const uploaded = !!(doc.fileUrl || doc.hasFile !== false);
    const ocrComplete = ocrKey === "completed";
    const ocrActive = ocrKey === "processing" || ocrKey === "pending";
    const ocrFailed = ocrKey === "failed";
    const isSetSef = FL.documents.isSetSefSemesterDocument(doc);
    const verification = String(info["Indicator verification status"] || "").trim();
    const verificationDone = isSetSef && ocrComplete && verification && verification !== "PROCESSING_FAILED";
    const verificationLabel = verification ? verification.replace(/_/g, " ") : (ocrComplete && isSetSef ? "Undetermined" : "—");
    const decided = doc.status === "approved" || doc.status === "system-approved" || doc.status === "rejected" || doc.status === "revision";
    const decisionLabel = doc.status === "approved" || doc.status === "system-approved"
      ? "Approved"
      : doc.status === "rejected"
        ? "Rejected"
        : doc.status === "revision"
          ? "Revision requested"
          : doc.status === "pending-review"
            ? "Pending review"
            : String(doc.status || "Pending").replace(/-/g, " ");
    const scoringOverall = scored && scored.validation ? scored.validation.overall : "";
    const scoringLabel = scoringOverall === "valid"
      ? "Eligible"
      : scoringOverall === "invalid"
        ? "Ineligible"
        : ocrComplete
          ? "Reviewer check"
          : "Waiting";
    function step(label, state) {
      return `<li class="review-step review-step--${state}"><span class="review-step-dot" aria-hidden="true"></span><span>${FL.esc(label)}</span></li>`;
    }
    return `
      <div class="review-status-strip card" aria-label="Processing status">
        <ol class="review-steps">
          ${step("File uploaded", uploaded ? "done" : "wait")}
          ${step(ocrFailed ? "OCR failed" : "OCR completed", ocrFailed ? "error" : ocrComplete ? "done" : ocrActive ? "current" : "wait")}
          ${isSetSef ? step("Indicator check: " + verificationLabel, verificationDone ? (verification === "MATCH" ? "done" : "warn") : ocrComplete ? "current" : "wait") : ""}
          ${step("Reviewer decision: " + (typeof decisionLabel === "string" ? decisionLabel : "Pending"), decided ? "done" : "current")}
          ${step("Scoring: " + scoringLabel, doc.status === "approved" || doc.status === "system-approved" ? "done" : "wait")}
        </ol>
      </div>`;
  },

  reviewSummaryHtml: function (doc, scored, faculty) {
    if (doc.documentInformation && typeof doc.documentInformation === "object") {
      let html = FL.documents.documentInformationHtml(doc, doc.documentInformation);
      if (FL.documents.isCriterionATeachingDocument(doc)) {
        const progress = FL.documents.tevReviewerProgressLabel(doc);
        if (progress && progress !== "—") {
          html += `<div class="kv-grid kv-grid--compact"><div class="kv-row">${FL.documents.kvRow("Semester review progress", FL.esc(progress), false)}</div></div>`;
        }
      }
      return html;
    }
    const block = {
      facultyName: FL.documents.facultyNameOnDocument(doc),
      kraLabel: doc.kraId || "—",
      criterionLabel: doc.criterionId || "—",
      documentType: "—",
      ocrStatus: FL.documents.ocrStatusLabel(doc),
      dateUploaded: doc.submittedAt || doc.uploadedAt
    };
    return FL.documents.documentInformationHtml(doc, block);
  },

  bindReviewTabs: function (preferredTab) {
    const tabs = document.querySelectorAll(".review-tabs [role=tab]");
    const panels = document.querySelectorAll(".review-tab-panel");
    if (!tabs.length) return;
    function activate(id) {
      FL.documents._reviewActiveTab = id;
      tabs.forEach(function (tab) {
        const on = tab.getAttribute("data-tab") === id;
        tab.setAttribute("aria-selected", on ? "true" : "false");
        tab.tabIndex = on ? 0 : -1;
      });
      panels.forEach(function (panel) {
        const on = panel.getAttribute("data-tab-panel") === id;
        panel.hidden = !on;
        panel.classList.toggle("is-active", on);
      });
    }
    const initial = preferredTab || "review";
    activate(initial);
    tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        activate(tab.getAttribute("data-tab"));
      });
      tab.addEventListener("keydown", function (event) {
        const list = Array.prototype.slice.call(tabs);
        const index = list.indexOf(tab);
        if (event.key === "ArrowRight") {
          event.preventDefault();
          list[(index + 1) % list.length].focus();
          activate(list[(index + 1) % list.length].getAttribute("data-tab"));
        } else if (event.key === "ArrowLeft") {
          event.preventDefault();
          list[(index - 1 + list.length) % list.length].focus();
          activate(list[(index - 1 + list.length) % list.length].getAttribute("data-tab"));
        }
      });
    });
  },

  kvRow: function (label, valueHtml, missing) {
    return `<div class="kv-row"><div class="kv-label">${FL.esc(label)}</div><div class="kv-value${missing ? " is-missing" : ""}">${valueHtml}</div></div>`;
  },

  identityDisplayHtml: function (doc, identityValue, identityStatus) {
    if (!identityValue) {
      return FL.ui.badge("invalid", "Not extracted");
    }
    const lower = String(identityStatus || "").toLowerCase();
    if (lower.indexOf("matched") >= 0 && lower.indexOf("does not") < 0) {
      return `${FL.esc(String(identityValue))} ${FL.ui.badge("valid", "Verified")}`;
    }
    if (lower.indexOf("does not match") >= 0 || lower.indexOf("invalid") >= 0) {
      return `${FL.esc(String(identityValue))} ${FL.ui.badge("invalid", "Mismatch")}`;
    }
    if (identityStatus) {
      return `${FL.esc(String(identityValue))} <span class="note">${FL.esc(String(identityStatus))}</span>`;
    }
    return FL.esc(String(identityValue));
  },

  ocrScoringSnapshotKeys: function (doc) {
    const found = doc.indicatorId ? FL.rules.findIndicator(doc.indicatorId) : null;
    const rating = found && found.indicator.formula && found.indicator.formula.type === "rating";
    const keys = [
      "Assigned KRA",
      "Criterion",
      "Automatically identified indicator",
      "Classification confidence",
      "Extracted rating",
      "Provisional score",
      "Base points",
      "Document type"
    ];
    if (!rating) keys.push("Contribution percent");
    return keys;
  },

  kraLabel: function (doc) {
    if (!doc.indicatorId) {
      const found = FL.validation.classify(doc);
      return found.detected ? found.detected.label : "Unclassified";
    }
    const rule = FL.rules.findIndicator(doc.indicatorId);
    return rule ? rule.kra.code + " — " + rule.kra.name : "—";
  },

  href: function (id) {
    const page = document.body.dataset.role === "administrator" ? "document-view.html" : "document-review.html";
    return page + "?id=" + encodeURIComponent(id);
  },

  renderTable: function (session, options) {
    const page = document.getElementById("page");
    page.innerHTML = `
      <div class="page-head">
        <div>
          <p class="eyebrow">${FL.esc(options.eyebrow)}</p>
          <h1>${FL.esc(options.title)}</h1>
          <p class="lede">${FL.esc(options.lede)}</p>
        </div>
      </div>
      <div class="toolbar">
        <label class="search"><span class="sr-only">Search documents</span>
          <input id="doc-search" type="search" placeholder="Search faculty, document ID, name, KRA, or status">
        </label>
        <label class="filter"><span>KRA</span>
          <select id="doc-kra"><option value="">All KRAs</option>${FL.rules.kras.map(function (kra) {
            return `<option value="${FL.esc(kra.id)}">${FL.esc(kra.code)}</option>`;
          }).join("")}<option value="none">Unclassified</option></select>
        </label>
        <label class="filter"><span>Status</span>
          <select id="doc-status">
            <option value="">All statuses</option>
            <option value="pending-review">Pending review</option>
            <option value="reviewer-required">Reviewer validation required</option>
            <option value="invalid">Invalid</option>
            <option value="revision">Revision requested</option>
            <option value="system-approved">System approved</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="ignored-duplicate">Duplicate ignored</option>
          </select>
        </label>
      </div>
      <div class="card"><div class="table-wrap" id="doc-table"></div></div>`;
    const draw = function () {
      const query = document.getElementById("doc-search").value.trim().toLowerCase();
      const kra = document.getElementById("doc-kra").value;
      const status = document.getElementById("doc-status").value;
      let rows = options.rows.slice();
      rows = rows.filter(function (doc) {
        if (status && doc.status !== status) return false;
        const rule = doc.indicatorId ? FL.rules.findIndicator(doc.indicatorId) : null;
        const kraId = rule ? rule.kra.id : "none";
        if (kra && kraId !== kra) return false;
        if (!query) return true;
        const faculty = FL.store.facultyById(doc.facultyId);
        const blob = [doc.id, doc.name, faculty ? faculty.name : "", FL.documents.kraLabel(doc), doc.status].join(" ").toLowerCase();
        return blob.indexOf(query) !== -1;
      });
      const host = document.getElementById("doc-table");
      if (!rows.length) {
        host.innerHTML = FL.ui.empty(options.emptyTitle, options.emptyText);
        return;
      }
      host.innerHTML = `
        <table class="data">
          <thead><tr>
            <th>Document ID</th><th>Faculty</th><th>Document</th><th>KRA</th><th>OCR</th><th>Validation</th><th>Score</th><th>Reviewer</th><th>Date</th><th></th>
          </tr></thead>
          <tbody>
            ${rows.map(function (doc) {
              const faculty = FL.store.facultyById(doc.facultyId);
              const reviewer = FL.store.userById(doc.reviewerId);
              const scored = FL.scoring.scoreDocument(doc);
              const ocrSt = FL.documents.ocrStatusLabel(doc);
              const ocr = ocrSt === "completed" ? "Completed" : ocrSt === "processing" ? "Processing" : ocrSt === "failed" ? "Failed" : "Pending";
              const effective = FL.documents.effectiveSimulationScore(doc);
              const period = FL.documents.periodSimulationDisplay(doc);
              const source = FL.documents.simulationScoreSource(doc);
              const scoreCell = doc.status === "ignored-duplicate"
                ? "—"
                : period && period.score != null
                  ? `<div>SET period ${FL.esc(String(period.score))}</div><div class="sub">${FL.esc(period.filled || "6/6")} semesters · rank simulation</div>`
                  : period && period.filled
                    ? `<div class="sub">Period ${FL.esc(period.filled)}</div><div class="sub">Complete all semesters for SET simulation</div>`
                    : effective == null
                      ? `<span class="sub">Score unavailable</span>`
                      : `<div>Simulation ${FL.esc(String(effective))}</div><div class="sub">${FL.esc(source)}</div>`;
              return `<tr>
                <td>${FL.esc(doc.id)}</td>
                <td>${FL.esc(faculty ? faculty.name : "—")}</td>
                <td>${FL.esc(doc.name)}</td>
                <td>${FL.esc(FL.documents.kraLabel(doc))}</td>
                <td>${FL.ui.statusBadge(ocr === "Completed" ? "completed" : ocr === "Processing" ? "processing" : ocr === "Failed" ? "failed" : "pending")}</td>
                <td>${FL.ui.statusBadge(scored.validation.overall === "valid" ? "valid" : scored.validation.overall === "invalid" ? "invalid" : "reviewer-required")}</td>
                <td>${scoreCell}</td>
                <td>${FL.esc(reviewer ? reviewer.name : "—")}</td>
                <td>${FL.esc(FL.formatWhen(doc.dateSubmitted))}</td>
                <td><a class="btn btn-small btn-primary" href="${FL.documents.href(doc.id)}">${FL.esc(options.action)}</a></td>
              </tr>`;
            }).join("")}
          </tbody>
        </table>`;
    };
    document.getElementById("doc-search").addEventListener("input", draw);
    document.getElementById("doc-kra").addEventListener("change", draw);
    document.getElementById("doc-status").addEventListener("change", draw);
    draw();
  },

  renderReview: function (session, canDecide) {
    const params = new URLSearchParams(window.location.search);
    const page = document.getElementById("page");
    const docId = params.get("id");
    page.innerHTML = FL.ui.loading("Document loading");
    const loadDoc = FL.store.usesLiveDocuments()
      ? FL.store.refreshLiveDocument(session, docId)
      : Promise.resolve(FL.store.documentById(docId));
    loadDoc.then(function (doc) {
      if (!doc || (session.role === "reviewer" && !FL.documents.scoped(session).some(function (item) { return item.id === doc.id; }))) {
        page.innerHTML = FL.ui.empty("Missing document", "The document record was not found, or it is not assigned to you.");
        return;
      }
      const tevFocus = params.get("tev");
      if (tevFocus) doc._highlightTev = tevFocus;
      return FL.documents.hydrateAuthenticatedFile(doc).finally(function () {
        FL.documents.paintReview(session, doc, canDecide);
      });
    }).catch(function (error) {
      page.innerHTML = FL.ui.empty("Could not load document", error.message || "Try again later.");
    });
  },

  _ocrPollTimer: null,
  _reviewActiveTab: "review",

  ocrStatusLabel: function (doc) {
    const status = doc.ocr && doc.ocr.status;
    if (status === "completed") return "completed";
    if (status === "processing") return "processing";
    if (status === "failed") return "failed";
    return "pending";
  },

  paintReview: function (session, doc, canDecide) {
    const faculty = FL.store.facultyById(doc.facultyId);
    const reviewer = FL.store.userById(doc.reviewerId);
    const scored = FL.scoring.scoreDocument(doc);
    const validation = scored.validation;
    const back = FL.documents.reviewContextBackHref(doc, canDecide);
    const backLabel = FL.documents.reviewContextBackLabel(doc);
    const activeTab = FL.documents._reviewActiveTab || "review";
    const toolbar = doc.fileUrl
      ? `<div class="doc-toolbar">
          <button class="btn btn-small btn-primary" type="button" id="open-doc">Open in new tab</button>
          <a class="btn btn-small btn-ghost" href="${FL.esc(doc.fileUrl)}" download="${FL.esc(doc.fileName || "document")}">Download</a>
        </div>`
      : "";
    const page = document.getElementById("page");
    page.innerHTML = `
      <div class="review-page">
      <header class="review-header card">
        <div class="review-header-main">
          <div class="review-header-icon" aria-hidden="true">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" stroke="currentColor" stroke-width="1.5"/>
              <path d="M14 3v5h5M9 13h6M9 17h6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </div>
          <div>
            <p class="eyebrow">Document review</p>
            <h1 class="review-title">${FL.esc(doc.name)}</h1>
            <p class="review-meta">${FL.esc(doc.id)} · ${FL.esc(faculty ? faculty.name : "Faculty")}${reviewer ? " · Reviewer " + FL.esc(reviewer.name) : ""}</p>
          </div>
        </div>
        <div class="review-header-actions">
          ${FL.ui.statusBadge(doc.status)}
          <a class="btn btn-ghost" href="${FL.esc(back)}">${FL.esc(backLabel)}</a>
        </div>
      </header>
      ${FL.documents.compactWorkflowHtml(doc, scored)}
      ${FL.documents.teachingEvaluationsPanelHtml(doc, canDecide)}
      <div class="review-tabs" role="tablist" aria-label="Document review sections">
        <button type="button" role="tab" id="review-tab-btn-review" data-tab="review" aria-controls="review-tab-panel-review" aria-selected="true">Review</button>
        <button type="button" role="tab" id="review-tab-btn-ocr" data-tab="ocr" aria-controls="review-tab-panel-ocr" aria-selected="false" tabindex="-1">OCR Details</button>
        <button type="button" role="tab" id="review-tab-btn-scoring" data-tab="scoring" aria-controls="review-tab-panel-scoring" aria-selected="false" tabindex="-1">Scoring &amp; Official Rules</button>
      </div>
      <div class="review-tab-panel is-active" id="review-tab-panel-review" data-tab-panel="review" role="tabpanel" aria-labelledby="review-tab-btn-review">
        <div class="review-grid review-grid--review-tab">
          <section class="card review-section document-stage" id="document-area">
            <div class="card-head card-head--toolbar">
              <div>
                <h2>Original document</h2>
                <p class="sub">${FL.esc(doc.fileName)} · ${FL.esc(doc.fileType || "File")} · ${FL.esc(FL.formatWhen(doc.dateSubmitted))}</p>
              </div>
              ${toolbar}
            </div>
            <div class="preview preview-clean" id="preview">
              ${FL.documents.originalFileHtml(doc)}
            </div>
          </section>
          <aside class="review-aside">
            <section class="card review-section review-summary-card">
              ${FL.documents.reviewSummaryHtml(doc, scored, faculty)}
            </section>
            <section class="card review-section review-decision" id="decision">
              ${FL.documents.decisionHtml(doc, canDecide)}
            </section>
          </aside>
        </div>
      </div>
      <div class="review-tab-panel" id="review-tab-panel-ocr" data-tab-panel="ocr" role="tabpanel" aria-labelledby="review-tab-btn-ocr" hidden>
        <section class="card review-section" id="ocr-area">
          <div class="card-head"><h2>OCR extraction details</h2>${FL.ui.statusBadge(FL.documents.ocrStatusLabel(doc))}</div>
          <p class="note">Compare extracted fields and text with the original document on the Review tab.</p>
          ${FL.documents.ocrHtml(doc, scored, session, canDecide, { tabMode: true })}
          <details class="review-collapse review-correction-panel">
            <summary>Correct extracted information</summary>
            <div class="review-collapse-body">
              ${FL.documents.extractionCorrectionHtml(doc, canDecide)}
            </div>
          </details>
        </section>
      </div>
      <div class="review-tab-panel" id="review-tab-panel-scoring" data-tab-panel="scoring" role="tabpanel" aria-labelledby="review-tab-btn-scoring" hidden>
        <section class="card review-section" id="scoring">${FL.documents.scoreHtml(scored, doc, canDecide)}</section>
        <details class="review-collapse card review-section">
          <summary>Applicable DBM–CHED rule &amp; indicator</summary>
          <div class="review-collapse-body" id="rule">${FL.documents.ruleHtml(scored, canDecide, doc)}</div>
        </details>
        <details class="review-collapse card review-section">
          <summary>Document validation</summary>
          <div class="review-collapse-body" id="validation">${FL.documents.validationHtml(doc, validation, canDecide, { includeCorrection: false })}</div>
        </details>
        <details class="review-collapse card review-section">
          <summary>KRA classification reference</summary>
          <div class="review-collapse-body" id="classification">${FL.documents.classificationHtml(doc, validation)}</div>
        </details>
        <details class="review-collapse card review-section">
          <summary>Contribution allocation</summary>
          <div class="review-collapse-body" id="contribution">${FL.documents.contributionHtml(scored, doc)}</div>
        </details>
      </div>
      </div>`;
    FL.documents.bindReviewTabs(activeTab);
    FL.documents.bindZoom();
    const openOriginal = function (event) {
      if (event) {
        event.preventDefault();
        event.stopPropagation();
      }
      if (doc.fileApiPath || doc.fileUrl) {
        FL.documents.hydrateAuthenticatedFile(doc).then(function (hydrated) {
          const url = FL.documents.inlineFileUrl(hydrated);
          if (url) window.open(url, "_blank", "noopener");
          else FL.ui.toast("Could not open the document file.", "danger");
        }).catch(function (err) {
          FL.ui.toast(err.message || "Could not open the document file.", "danger");
        });
        return;
      }
      FL.ui.modal({
        title: doc.fileName,
        body: `<p>${FL.esc(doc.fileType)} · ${FL.esc(doc.fileSize)}</p><p class="note">The original file is not available on the server for this record.</p>`,
        cancelLabel: "Close"
      });
    };
    const openDocBtn = document.getElementById("open-doc");
    if (openDocBtn) openDocBtn.addEventListener("click", openOriginal);
    const secondaryOpen = document.getElementById("open-doc-secondary");
    if (secondaryOpen) secondaryOpen.addEventListener("click", openOriginal);
    const copyOcr = document.getElementById("ocr-copy");
    if (copyOcr) {
      copyOcr.addEventListener("click", function () {
        const block = document.getElementById("ocr-excerpt");
        const text = block ? block.textContent : "";
        if (navigator.clipboard && text) {
          navigator.clipboard.writeText(text).then(function () {
            FL.ui.toast("Extracted text copied.", "ok");
          });
        }
      });
    }
    const retryOcr = document.getElementById("ocr-retry");
    if (retryOcr) {
      retryOcr.addEventListener("click", function () {
        FL.store.retryDocumentOcr(session, doc.id).then(function (fresh) {
          Object.assign(doc, fresh);
          FL.ui.toast("OCR retry queued.", "ok");
          FL.documents.paintReview(session, doc, canDecide);
        }).catch(function (error) {
          FL.ui.toast(error.message || "OCR retry failed.", "danger");
        });
      });
    }
    if (FL.documents._ocrPollTimer) {
      clearInterval(FL.documents._ocrPollTimer);
      FL.documents._ocrPollTimer = null;
    }
    if (FL.store.usesLiveDocuments() && doc.ocr && (doc.ocr.status === "pending" || doc.ocr.status === "processing")) {
      FL.documents._ocrPollTimer = setInterval(function () {
        FL.store.refreshLiveDocument(session, doc.id).then(function (fresh) {
          if (!fresh || !fresh.ocr) return;
          if (fresh.ocr.status === doc.ocr.status && fresh.ocr.completedAt === (doc.ocr && doc.ocr.completedAt)) return;
          Object.assign(doc, fresh);
          FL.documents.paintReview(session, doc, canDecide);
        });
      }, 4000);
    }
    const select = document.getElementById("indicator-select");
    if (select) {
      select.addEventListener("change", function () {
        doc.indicatorId = select.value || null;
        FL.store.saveDocument(doc, session).then(function () {
          FL.documents.paintReview(session, doc, canDecide);
        }).catch(function (error) {
          FL.ui.toast(error.message || "The indicator was not saved.", "danger");
        });
      });
    }
    if (canDecide) {
      const decisionScore = document.getElementById("decision-score");
      const refreshPreview = function (value) {
        const preview = FL.documents.scorePreview(doc, Number(value));
        const percentEl = document.getElementById("decision-preview-percent");
        const finalEl = document.getElementById("decision-preview-final");
        if (percentEl) percentEl.textContent = preview.percent == null ? "—" : preview.percent + "%";
        if (finalEl) finalEl.textContent = preview.finalScore == null ? "—" : String(preview.finalScore);
      };
      if (decisionScore) {
        decisionScore.addEventListener("input", function () {
          refreshPreview(decisionScore.value);
        });
        refreshPreview(decisionScore.value);
      }
      FL.documents.bindDecision(session, doc);
      FL.documents.bindExtractionCorrection(session, doc, canDecide);
      FL.documents.bindTeachingEvaluationPanel(session, doc, canDecide);
      FL.documents.bindTeachingEvaluationActions(session, doc, canDecide);
    }
    if (doc._highlightTev) {
      const tevId = doc._highlightTev;
      delete doc._highlightTev;
      FL.documents.openTeachingEvaluationDrawer(session, doc, canDecide, tevId);
      const row = document.querySelector('[data-tev-row-id="' + tevId + '"]');
      if (row) row.scrollIntoView({ block: "nearest", behavior: "smooth" });
    } else if (doc._tevDrawerOpen) {
      FL.documents.openTeachingEvaluationDrawer(session, doc, canDecide, doc._tevDrawerOpen);
    }
  },

  inlineFileUrl: function (doc) {
    if (doc._objectUrl) return doc._objectUrl;
    if (FL.store.usesLiveDocuments() && doc.fileApiPath) {
      return "";
    }
    if (!doc.fileUrl) return "";
    const join = doc.fileUrl.indexOf("?") >= 0 ? "&" : "?";
    return doc.fileUrl + join + "disposition=inline";
  },

  fileApiPathWithDisposition: function (doc, disposition) {
    if (!doc || !doc.fileApiPath) return "";
    const join = doc.fileApiPath.indexOf("?") >= 0 ? "&" : "?";
    return doc.fileApiPath + join + "disposition=" + (disposition || "inline");
  },

  hydrateAuthenticatedFile: function (doc, options) {
    options = options || {};
    if (!FL.store.usesLiveDocuments() || !doc.fileApiPath) {
      return Promise.resolve(doc);
    }
    const livePreviewId = options.previewDocId || null;
    if (doc._objectUrl) {
      const stillActive = livePreviewId
        && FL.evidence
        && FL.evidence._caPreviewObjectUrl === doc._objectUrl
        && FL.evidence._caPreviewDocId === livePreviewId;
      if (stillActive) return Promise.resolve(doc);
      try { URL.revokeObjectURL(doc._objectUrl); } catch (revokeErr) { /* ignore */ }
      delete doc._objectUrl;
    }
    const path = FL.documents.fileApiPathWithDisposition(doc, "inline");
    return FL.apiClient.adminRequestBlob("GET", path).then(function (blob) {
      if (!blob || blob.size < 16) {
        throw Object.assign(new Error("The document file could not be loaded for preview."), { status: 502 });
      }
      const isPdfName = (doc.fileName || doc.name || "").toLowerCase().endsWith(".pdf");
      const isPdfType = (blob.type || "").indexOf("pdf") >= 0;
      function attachBlobUrl(pdfBlob) {
        if (doc._objectUrl) {
          try { URL.revokeObjectURL(doc._objectUrl); } catch (revokeErr) { /* ignore */ }
        }
        doc._objectUrl = URL.createObjectURL(pdfBlob);
        return doc;
      }
      if (isPdfName || isPdfType) {
        return blob.slice(0, 4).arrayBuffer().then(function (buf) {
          const bytes = new Uint8Array(buf);
          if (bytes.length < 4 || bytes[0] !== 0x25 || bytes[1] !== 0x50 || bytes[2] !== 0x44 || bytes[3] !== 0x46) {
            throw Object.assign(new Error("The server did not return a valid PDF for preview."), { status: 502 });
          }
          const pdfBlob = blob.type === "application/pdf" ? blob : new Blob([blob], { type: "application/pdf" });
          return attachBlobUrl(pdfBlob);
        });
      }
      return attachBlobUrl(blob);
    });
  },

  loadDocumentPdfPreview: function (doc, frameEl) {
    if (!frameEl) return Promise.resolve();
    frameEl.innerHTML = "<p class=\"ca-preview-loading\" role=\"status\">Loading document preview…</p>";
    return FL.documents.hydrateAuthenticatedFile(doc).then(function (hydrated) {
      const url = FL.documents.inlineFileUrl(hydrated);
      const isPdf = (hydrated.fileName || "").toLowerCase().endsWith(".pdf")
        || (hydrated.mimeType || "").indexOf("pdf") >= 0;
      if (url && isPdf) {
        frameEl.innerHTML = "<iframe title=\"PDF preview\" src=\"" + FL.esc(url)
          + "\" class=\"tev-drawer-iframe\"></iframe>";
        return;
      }
      if (url) {
        frameEl.innerHTML = "<p class=\"note\">Preview is limited for this file type. Use the Document tab below.</p>";
        return;
      }
      frameEl.innerHTML = "<p class=\"note\">No inline preview is available. Use the Document tab below for the original file.</p>";
    }).catch(function (error) {
      frameEl.innerHTML = "<p class=\"ca-preview-error\">" + FL.esc(error.message || "Preview failed.") + "</p>";
    });
  },

  downloadAuthenticatedFile: function (doc, fileName) {
    if (!FL.store.usesLiveDocuments() || !doc.fileApiPath) {
      return Promise.reject(new Error("Download is not available for this document."));
    }
    const path = FL.documents.fileApiPathWithDisposition(doc, "attachment");
    return FL.apiClient.adminRequestBlob("GET", path).then(function (blob) {
      const name = fileName || doc.fileName || doc.name || "document.pdf";
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = name;
      a.rel = "noopener";
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(function () { URL.revokeObjectURL(url); }, 5000);
    });
  },

  /* Zoom buttons for image previews on tablet and phone (pinch zoom also works). */
  bindZoom: function () {
    const frame = document.querySelector(".original-file-frame--zoom");
    if (!frame) return;
    const image = frame.querySelector("img");
    const level = document.querySelector(".zoom-tools .zoom-level");
    let percent = 100;
    const apply = function () {
      percent = Math.max(100, Math.min(400, percent));
      image.style.width = percent + "%";
      if (level) level.textContent = percent + "%";
    };
    document.querySelectorAll(".zoom-tools [data-zoom]").forEach(function (button) {
      button.addEventListener("click", function () {
        const action = button.getAttribute("data-zoom");
        if (action === "in") percent += 25;
        else if (action === "out") percent -= 25;
        else percent = 100;
        apply();
      });
    });
  },

  bindJumpNav: function () {
    const links = document.querySelectorAll(".jump a[href^='#']");
    links.forEach(function (link) {
      link.addEventListener("click", function (event) {
        event.preventDefault();
        links.forEach(function (item) { item.classList.remove("is-active"); });
        link.classList.add("is-active");
        const id = link.getAttribute("href").slice(1);
        const target = document.getElementById(id);
        if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    });
  },

  originalFileHtml: function (doc) {
    if (!doc.fileUrl) {
      return `<div class="preview-page"><p class="note">Original file is not stored for this record. Use the extracted summary on the right.</p></div>`;
    }
    const lower = String(doc.fileName || "").toLowerCase();
    const mime = String(doc.mimeType || "").toLowerCase();
    const inlineUrl = FL.esc(FL.documents.inlineFileUrl(doc));
    const isImage = mime.indexOf("image/") === 0 || /\.(png|jpe?g|gif|webp|bmp|tif|tiff)$/.test(lower);
    const isPdf = mime.indexOf("pdf") >= 0 || /\.pdf$/.test(lower);
    if (isImage) {
      const zoomTools = `<span class="zoom-tools" role="group" aria-label="Zoom document"><button class="btn btn-small btn-ghost" type="button" data-zoom="out" aria-label="Zoom out">−</button><span class="zoom-level" aria-live="polite">100%</span><button class="btn btn-small btn-ghost" type="button" data-zoom="in" aria-label="Zoom in">+</button><button class="btn btn-small btn-ghost" type="button" data-zoom="fit">Fit</button></span>`;
      return `<div class="original-file"><div class="original-file-actions">${zoomTools}</div><div class="original-file-frame original-file-frame--doc original-file-frame--zoom"><img src="${inlineUrl}" alt="${FL.esc(doc.fileName || "Uploaded document")}"></div></div>`;
    }
    if (isPdf) {
      const src = inlineUrl + "#toolbar=0&navpanes=0&scrollbar=1&view=FitH";
      return `<div class="original-file original-file--pdf"><div class="original-file-frame original-file-frame--doc original-file-frame--pdf"><iframe title="Original PDF preview" src="${src}"></iframe></div></div>`;
    }
    const excerpt = (doc.extractedInfo && (doc.extractedInfo["OCR excerpt"] || doc.extractedInfo.OCR)) || (doc.ocr && doc.ocr.content) || "";
    return `<div class="original-file"><div class="original-file-placeholder"><p class="note">Inline preview is not available for this file type. Use Open in new tab or Download from the toolbar above.</p>${excerpt ? `<div class="ocr-content">${FL.esc(String(excerpt).slice(0, 1200))}</div>` : ""}</div></div>`;
  },

  ocrHtml: function (doc, scored, session, canDecide, opts) {
    opts = opts || {};
    const status = FL.documents.ocrStatusLabel(doc);
    if (status === "processing") {
      return FL.ui.loading("Extracting text", "Extracting text from the uploaded document.");
    }
    if (status === "pending") {
      return FL.ui.loading("Waiting for OCR", "Waiting for OCR processing.");
    }
    if (status === "failed") {
      const err = (doc.ocr && doc.ocr.error) || (doc.extractedInfo && doc.extractedInfo["OCR error"]) || "Text extraction failed.";
      const retryBtn = FL.store.usesLiveDocuments()
        ? `<button class="btn btn-small btn-ghost" type="button" id="ocr-retry">Retry OCR</button>`
        : "";
      return `<div class="alert alert-warning"><p>${FL.esc(String(err))}</p><p class="note">Text extraction failed. The original document remains available for manual review.</p>${retryBtn}</div>`;
    }
    const info = doc.extractedInfo && typeof doc.extractedInfo === "object" ? doc.extractedInfo : {};
    const excerpt = ((doc.ocr && doc.ocr.content) || info["OCR excerpt"] || info.OCR || "").trim();
    const conf = doc.ocr && doc.ocr.confidence != null ? `${Number(doc.ocr.confidence).toFixed(1)}%` : (info["OCR confidence"] || "—");
    const identityLabel = info["Identity field label"] || "Faculty / named party";
    const identityValue = info["Extracted names"] || info["Extracted author(s)"] || (doc.ocr.authors && doc.ocr.authors.join(", ")) || "";
    const identityStatus = info["Identity verification"] || "";
    const titleValue = info["Extracted title"] || doc.ocr.title || "";
    const periodValue = info["Extracted date"] || info["Academic year"] || doc.ocr.date || "";
    const provisional = FL.documents.provisionalScore(doc);
    const credited = FL.documents.creditedPoints(doc);
    const officialMax = scored && scored.indicator ? (scored.historical ? scored.officialMax : scored.indicator.maxPoints) : null;
    const snapshotKeys = FL.documents.ocrScoringSnapshotKeys(doc);
    const used = {};
    snapshotKeys.forEach(function (key) { used[key] = true; });
    const metaRows = Object.keys(info).filter(function (key) {
      return !used[key] && key.indexOf("OCR original") !== 0 && key !== "Submission history" && String(info[key] || "").trim();
    }).slice(0, 12).map(function (key) {
      return FL.documents.kvRow(key, FL.esc(String(info[key])), false);
    }).join("");
    const snapshotRows = snapshotKeys.filter(function (key) {
      return String(info[key] || "").trim();
    }).map(function (key) {
      return FL.documents.kvRow(key, FL.esc(String(info[key])), false);
    }).join("");
    const method = info["Extraction method"] || info["OCR method"] || (doc.ocr && doc.ocr.method) || "—";
    const extractionStatus = info["SET/SEF extraction status"] || (status === "completed" ? "complete" : status);
    const scoreStrip = opts.tabMode
      ? ""
      : `<div class="score-mini-row">
        <div class="score-mini">
          <div class="score-mini-label">Provisional score</div>
          <div class="score-mini-value is-provisional">${provisional == null ? "—" : FL.esc(String(provisional))}</div>
        </div>
        <div class="score-mini">
          <div class="score-mini-label">Official maximum</div>
          <div class="score-mini-value">${officialMax == null ? "—" : FL.esc(String(officialMax))}</div>
        </div>
        <div class="score-mini">
          <div class="score-mini-label">Credited points</div>
          <div class="score-mini-value is-credited">${FL.esc(String(credited))}</div>
        </div>
      </div>`;
    return `
      ${FL.documents.setSefMetadataHtml(doc)}
      ${FL.documents.setSefAutoValidationHtml(doc)}
      <div class="kv-grid kv-grid--two">
        ${FL.documents.kvRow("Document title", titleValue ? FL.esc(titleValue) : FL.ui.badge("invalid", "Missing"), !titleValue)}
        ${FL.documents.kvRow(identityLabel, FL.documents.identityDisplayHtml(doc, identityValue, identityStatus), !identityValue)}
        ${FL.documents.kvRow("Academic year / period", periodValue ? FL.esc(String(periodValue)) : "—", !periodValue)}
        ${FL.documents.kvRow("Extraction method", FL.esc(String(method)), false)}
        ${FL.documents.kvRow("Extraction status", FL.esc(String(extractionStatus)), false)}
        ${identityStatus ? FL.documents.kvRow("Identity verification", FL.esc(String(identityStatus)), false) : ""}
      </div>
      ${scoreStrip}
      ${snapshotRows && !opts.tabMode ? `<h3 class="review-subhead">Scoring snapshot</h3><div class="kv-grid">${snapshotRows}</div>` : ""}
      ${metaRows ? `<h3 class="review-subhead">Other extracted metadata</h3><div class="kv-grid">${metaRows}</div>` : ""}
      <div class="review-ocr-meta"><span>OCR confidence: ${FL.esc(String(conf))}</span>${excerpt ? `<button class="btn btn-small btn-ghost" type="button" id="ocr-copy">Copy extracted text</button>` : ""}</div>
      <h3 class="review-subhead">Extracted text</h3>
      <div class="review-excerpt review-excerpt--tab" id="ocr-excerpt">${excerpt ? FL.esc(excerpt) : "No readable text was detected in this document."}</div>`;
  },

  classificationHtml: function (doc, validation) {
    const info = doc.extractedInfo && typeof doc.extractedInfo === "object" ? doc.extractedInfo : {};
    const storedIndicator = info["Automatically identified indicator"] || "";
    const storedKra = info["Detected KRA"] || "";
    const storedConfidence = info["Classification confidence"] || "";
    const hasStored = !!(storedIndicator || storedKra || info["Review reasons"] || info["OCR quality"]);
    const detected = hasStored ? null : validation.classification.detected;
    const kra = detected ? FL.rules.findKra(detected.kraId) : null;
    let status = hasStored ? (info["Review reasons"] ? "reviewer-required" : "classified") : validation.classification.status;
    const rows = FL.rules.kras.map(function (item) {
      const rule = FL.rules.classification.find(function (entry) { return entry.kraId === item.id; });
      return { kra: item, rule: rule };
    });
    const decision = hasStored
      ? `<dl class="facts compact">
          <div><dt>Stored indicator</dt><dd>${storedIndicator ? FL.esc(storedIndicator) : "—"}</dd></div>
          <div><dt>Stored detected KRA</dt><dd>${storedKra ? FL.esc(String(storedKra)) : "—"}</dd></div>
          <div><dt>Stored classification confidence</dt><dd>${storedConfidence !== "" ? FL.esc(String(storedConfidence)) : "—"}</dd></div>
          <div><dt>OCR quality</dt><dd>${FL.esc(info["OCR quality"] || "—")}</dd></div>
          <div><dt>OCR confidence</dt><dd>${FL.esc(info["OCR confidence"] || "—")}</dd></div>
        </dl>
        ${info["Review reasons"] ? `<div class="alert alert-warning">${FL.esc(String(info["Review reasons"]))}</div>` : ""}
        <p class="note">These values were stored when the document was processed. The keyword table is a reference and is not a second classification of the excerpt.</p>`
      : `<dl class="facts compact">
          <div><dt>Detected KRA</dt><dd>${kra ? FL.esc(kra.code + " — " + kra.name) : "None"}</dd></div>
          <div><dt>Classification status</dt><dd>${FL.esc(status === "classified" ? "Classified" : status === "priority" ? "Keyword tie-break applied" : status === "unclassified" ? "Cannot classify" : "Waiting for OCR")}</dd></div>
          <div><dt>Applicable keyword rule</dt><dd>${detected ? FL.esc(detected.keywords.join(", ")) + (kra ? " · " + kra.code : "") : "No keyword rule matched"}</dd></div>
        </dl>`;
    return `
      <div class="card-head"><h2>KRA classification</h2>${FL.ui.statusBadge(status === "pending" ? "pending" : status)}</div>
      <p>Faculty select only the KRA and criterion at upload. FacultyLink uses OCR and DBM–CHED rules to identify the indicator within that criterion.</p>
      ${decision}
      <div class="table-wrap"><table class="data">
        <thead><tr><th>Official KRA</th><th>Keywords</th><th>If several match</th></tr></thead>
        <tbody>${rows.map(function (row) {
          const on = detected && row.rule && detected.kraId === row.rule.kraId;
          const labels = { 1: "Chosen first", 2: "Chosen second", 3: "Chosen third", 4: "Chosen fourth" };
          const order = row.rule ? (labels[row.rule.priority] || ("Order " + row.rule.priority)) : "—";
          return `<tr class="${on ? "is-selected" : ""}"><td>${FL.esc(row.kra.code + " — " + row.kra.name)}</td><td>${row.rule ? FL.esc(row.rule.keywords.join(", ")) : "—"}</td><td>${FL.esc(order)}</td></tr>`;
        }).join("")}</tbody>
      </table></div>`;
  },

  ruleHtml: function (scored, canDecide, doc) {
    const options = FL.rules.kras.map(function (kra) {
      return `<optgroup label="${FL.esc(kra.code + " — " + kra.name)}">${kra.criteria.map(function (criterion) {
        return criterion.indicators.map(function (indicator) {
          const selected = indicator.id === doc.indicatorId ? " selected" : "";
          return `<option value="${FL.esc(indicator.id)}"${selected}>${FL.esc(indicator.name)}</option>`;
        }).join("");
      }).join("")}</optgroup>`;
    }).join("");
    const autoName = doc.extractedInfo && doc.extractedInfo["Automatically identified indicator"];
    const autoNote = autoName
      ? `<p class="note">Automatically identified: ${FL.esc(autoName)}. Reviewers may correct the indicator before accepting.</p>`
      : "";
    const picker = canDecide ? `
      <label class="field"><span>Match or correct Annex I indicator</span>
        <select id="indicator-select"><option value="">Not matched</option>${options}</select>
      </label>` : "";
    if (!scored.indicator) {
      return `<div class="card-head"><h2>Applicable DBM–CHED rule</h2></div>${autoNote}${picker}<div class="alert alert-warning">No Annex I indicator is matched. The reviewer matches the documentary evidence to a criterion before points are assigned.</div>`;
    }
    const indicator = scored.indicator;
    const points = indicator.pointsLabel || (indicator.points == null ? "—" : String(indicator.points));
    return `
      <div class="card-head"><h2>Applicable DBM–CHED rule</h2></div>
      ${autoNote}
      ${picker}
      <dl class="facts">
        <div><dt>KRA</dt><dd>${FL.esc(scored.kra.code + " — " + scored.kra.name)}</dd></div>
        <div><dt>Criterion</dt><dd>${FL.esc(scored.criterion.name)}</dd></div>
        <div><dt>Indicator</dt><dd>${FL.esc(indicator.name)}</dd></div>
        <div><dt>Points</dt><dd>${FL.esc(points)}</dd></div>
        <div><dt>Maximum points</dt><dd>${FL.esc(String(indicator.maxPoints))}${scored.criterion.bonus ? " (bonus criterion)" : ""}</dd></div>
        <div><dt>Documentary evidence</dt><dd>${indicator.evidence.map(FL.esc).join("; ")}</dd></div>
        <div><dt>Contribution</dt><dd>${FL.esc(FL.documents.contributionNote(indicator))}</dd></div>
        <div><dt>Applicable conditions</dt><dd>${indicator.conditions.map(FL.esc).join(" ")}</dd></div>
      </dl>`;
  },

  contributionNote: function (indicator) {
    if (indicator.contribution === "declared") return "Co-claimants declare a contribution percentage. Final Score = Base Points × Contribution Percentage.";
    if (indicator.contribution === "sole") return "Sole author, inventor, or developer. The full base points are credited.";
    if (indicator.contribution === "fixed") return "Annex I states this point value for the role.";
    return "Contribution allocation is not used for this indicator.";
  },

  usesContributorPercent: function (indicator) {
    return !!(indicator && indicator.contribution === "declared");
  },

  indicatorFormulaText: function (indicator) {
    if (!indicator) return FL.scoring.formula;
    if (indicator.pointsLabel) return indicator.pointsLabel;
    if (indicator.formula && indicator.formula.type === "rating") {
      return "Points = (evaluation rating ÷ 100) × " + indicator.formula.multiplier + ". No authorship contribution percentage applies.";
    }
    if (FL.documents.usesContributorPercent(indicator)) return FL.scoring.formula;
    return FL.documents.contributionNote(indicator);
  },

  defaultAssignedScore: function (doc) {
    if (doc.review && typeof doc.review.assignedScore === "number") return doc.review.assignedScore;
    if (FL.documents.isSetSefSemesterDocument(doc)) return 0;
    const provisional = FL.documents.provisionalScore(doc);
    return provisional == null ? "" : provisional;
  },

  decisionScorePreviewHtml: function (doc, preview, officialMax) {
    const found = doc.indicatorId ? FL.rules.findIndicator(doc.indicatorId) : null;
    const showContribution = found && FL.documents.usesContributorPercent(found.indicator);
    const contributionBlock = showContribution
      ? `<div><span>Contribution</span><strong id="decision-preview-percent">${preview.percent == null ? "—" : FL.esc(String(preview.percent)) + "%"}</strong></div>
          <div><span>Credited points after contribution</span><strong id="decision-preview-final">${preview.finalScore == null ? "—" : FL.esc(String(preview.finalScore))}</strong></div>`
      : `<div><span>Credited points (if approved)</span><strong id="decision-preview-final">${preview.finalScore == null ? "—" : FL.esc(String(preview.finalScore))}</strong></div>`;
    return `
        <div class="score-preview">
          <div><span>Official maximum</span><strong>${FL.esc(String(officialMax))}</strong></div>
          ${contributionBlock}
        </div>`;
  },

  metadataCorrectionBlocked: function (doc) {
    if (doc.canCorrectMetadata === false) {
      return doc.metadataCorrectionBlockedReason || "Metadata correction is not available for this document.";
    }
    if (doc.status === "approved" || doc.status === "system-approved" || doc.status === "rejected") {
      if (doc.status === "rejected") {
        return "Rejected documents cannot be corrected here. Use the review workflow if the decision should change.";
      }
      return "This document is already approved. Reopen it through the authorized review workflow before correcting extracted information.";
    }
    if (doc.decidedAt) {
      return "This document already has a reviewer decision. Reopen it before correcting extracted information.";
    }
    return "";
  },

  extractionCorrectionHtml: function (doc, canDecide) {
    if (!canDecide) return "";
    const blocked = FL.documents.metadataCorrectionBlocked(doc);
    if (blocked) {
      return `
      <h3 class="block-label">Correct extracted information</h3>
      <div class="alert alert-warning">${FL.esc(blocked)}</div>`;
    }
    const info = doc.extractedInfo || {};
    const fields = FL.validation.fields(doc);
    const found = doc.indicatorId ? FL.rules.findIndicator(doc.indicatorId) : null;
    const isRating = found && found.indicator.formula && found.indicator.formula.type === "rating";
    const multiEvidence = found && found.indicator.evidence && found.indicator.evidence.length > 1;
    const log = info["Reviewer correction log"];
    return `
      <h3 class="block-label">Correct extracted information</h3>
      <p class="note">Use this when OCR missed values that are visible in the original document. Original OCR values are kept for audit. This does not change the uploaded file.</p>
      <div class="correction-grid">
        <label class="field"><span>Faculty / identity name</span>
          <input id="corr-faculty" type="text" value="${FL.esc(fields.authorValue)}" placeholder="As shown on the document"></label>
        <label class="field"><span>Document title</span>
          <input id="corr-title" type="text" value="${FL.esc(fields.titleValue)}" placeholder="Title on the document"></label>
        <label class="field"><span>Academic year / date</span>
          <input id="corr-date" type="text" value="${FL.esc(fields.dateValue)}" placeholder="e.g. AY 2023-2024"></label>
        <label class="field"><span>Academic term</span>
          <input id="corr-term" type="text" value="${FL.esc(FL.validation.infoValue(doc, "Academic term"))}" placeholder="Semester"></label>
        ${isRating ? `<label class="field"><span>Evaluation type</span>
          <input id="corr-eval-type" type="text" value="${FL.esc(FL.validation.infoValue(doc, "Evaluation type"))}" placeholder="SET or SEF"></label>
        <label class="field"><span>Overall rating</span>
          <input id="corr-rating" type="text" inputmode="decimal" value="${FL.esc(fields.ratingValue)}" placeholder="e.g. 95"></label>
        <label class="field"><span>Rating scale</span>
          <input id="corr-scale" type="text" inputmode="decimal" value="${FL.esc(FL.validation.infoValue(doc, "Rating scale"))}" placeholder="e.g. 100"></label>` : ""}
        <label class="field field-span"><span>Reason for correction</span>
          <textarea id="corr-reason" rows="3" placeholder="Explain what you verified in the original document"></textarea></label>
        ${multiEvidence ? `<label class="field field-span"><span><input id="corr-evidence" type="checkbox"> Supporting documents verified</span>
          <span class="note">Required for indicators that list more than one Annex A evidence item. Check only if the original submission includes them.</span></label>` : ""}
      </div>
      <p class="field-error" id="corr-error"></p>
      <button class="btn btn-primary" type="button" id="save-extraction">Correct extracted information</button>
      ${log ? `<p class="note">Prior reviewer corrections are recorded in the audit log for this document.</p>` : ""}`;
  },

  bindExtractionCorrection: function (session, doc, canDecide) {
    if (!canDecide) return;
    const button = document.getElementById("save-extraction");
    if (!button) return;
    const error = document.getElementById("corr-error");
    const user = FL.store.userById(session.userId);
    const fields = FL.validation.fields(doc);
    const baseline = {
      facultyName: (fields.authorValue || "").trim(),
      extractedTitle: (fields.titleValue || "").trim(),
      academicYear: (fields.dateValue || "").trim(),
      academicTerm: (FL.validation.infoValue(doc, "Academic term") || "").trim()
    };
    const ratingInput = document.getElementById("corr-rating");
    if (ratingInput) baseline.evaluationRating = (ratingInput.defaultValue || ratingInput.value || "").trim();
    const evalTypeEl = document.getElementById("corr-eval-type");
    if (evalTypeEl) baseline.evaluationType = (evalTypeEl.defaultValue || evalTypeEl.value || "").trim();
    const scaleEl = document.getElementById("corr-scale");
    if (scaleEl) baseline.ratingScale = (scaleEl.defaultValue || scaleEl.value || "").trim();
    button.addEventListener("click", function () {
      error.textContent = "";
      const reason = (document.getElementById("corr-reason").value || "").trim();
      if (reason.length < 8) {
        error.textContent = "Enter a brief reason for the correction (at least 8 characters).";
        return;
      }
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
        if (rating && rating !== baseline.evaluationRating) payload.evaluationRating = rating;
      }
      const evalTypeInput = document.getElementById("corr-eval-type");
      if (evalTypeInput) {
        const et = (evalTypeInput.value || "").trim();
        if (et && et !== baseline.evaluationType) payload.evaluationType = et;
      }
      const scaleInput = document.getElementById("corr-scale");
      if (scaleInput) {
        const sc = (scaleInput.value || "").trim();
        if (sc && sc !== baseline.ratingScale) payload.ratingScale = sc;
      }
      const evidence = document.getElementById("corr-evidence");
      if (evidence && evidence.checked) payload.attestSupportingEvidence = true;
      if (!payload.attestSupportingEvidence && Object.keys(payload).length === 1) {
        error.textContent = "Change at least one extracted field or attest supporting evidence before saving.";
        return;
      }
      button.disabled = true;
      FL.store.correctDocumentMetadata(doc.id, payload, session).then(function (saved) {
        if (saved && typeof saved === "object") {
          Object.keys(saved).forEach(function (key) { doc[key] = saved[key]; });
        }
        return FL.audit.record(user, "Corrected extracted information", doc.id, payload.reason);
      }).then(function () {
        FL.ui.toast("Extracted information updated. Validation and provisional score were recalculated.", "ok");
        FL.documents.paintReview(session, doc, canDecide);
      }).catch(function (err) {
        error.textContent = err.message || "The correction was not saved.";
      }).finally(function () {
        button.disabled = false;
      });
    });
  },

  validationHtml: function (doc, validation, canDecide, options) {
    options = options || {};
    if (doc.ocr && (doc.ocr.status === "processing" || doc.ocr.status === "pending")) {
      return `<div class="card-head"><h2>Document validation</h2></div>${FL.ui.loading("Validation-result loading", "Validation starts after OCR extraction.")}`;
    }
    const field = function (ok, label, detail) {
      return `<li>${FL.ui.statusBadge(ok ? "valid" : "invalid")} ${FL.esc(label)}${detail ? " — " + FL.esc(detail) : ""}</li>`;
    };
    const reqItem = function (item) {
      const tone = item.kind === "invalid" ? "invalid" : item.kind === "missing_evidence" ? "pending" : "pending";
      return `<li>${FL.ui.statusBadge(tone)} ${FL.esc(item.label)} — ${FL.esc(item.message)}</li>`;
    };
    const klass = validation.classification;
    const f = validation.fields;
    return `
      <div class="card-head"><h2>Document validation</h2>${FL.ui.statusBadge(validation.overall === "valid" ? "valid" : validation.overall === "invalid" ? "invalid" : "reviewer-required")}</div>
      ${validation.reasons.length ? `<div class="alert ${validation.overall === "invalid" ? "alert-danger" : "alert-warning"}">${validation.reasons.map(FL.esc).join(" ")}</div>` : ""}
      <h3 class="block-label">Required fields (extracted)</h3>
      <ul class="check-list">
        ${field(f.title, "Title", f.titleValue || "missing from OCR")}
        ${field(f.author, "Identity / author", f.authorValue || "missing from OCR")}
        ${field(f.date, "Date / academic period", f.dateValue || "missing from OCR")}
        ${f.ratingValue ? field(!!f.ratingValue, "Evaluation rating", f.ratingValue) : ""}
      </ul>
      ${validation.requirements && validation.requirements.length ? `<h3 class="block-label">Indicator and evidence checks</h3><ul class="check-list">${validation.requirements.map(reqItem).join("")}</ul>` : ""}
      <h3 class="block-label">KRA classification</h3>
      <dl class="facts compact">
        <div><dt>KRA</dt><dd>${(doc.extractedInfo && doc.extractedInfo["Detected KRA"]) ? FL.esc(String(doc.extractedInfo["Detected KRA"])) : (klass.detected ? FL.esc(klass.detected.label) : "—")}</dd></div>
        <div><dt>Criterion</dt><dd>${doc.indicatorId && FL.rules.findIndicator(doc.indicatorId) ? FL.esc(FL.rules.findIndicator(doc.indicatorId).criterion.name) : "—"}</dd></div>
        <div><dt>Indicator</dt><dd>${(doc.extractedInfo && doc.extractedInfo["Automatically identified indicator"]) ? FL.esc(doc.extractedInfo["Automatically identified indicator"]) : (doc.indicatorId && FL.rules.findIndicator(doc.indicatorId) ? FL.esc(FL.rules.findIndicator(doc.indicatorId).indicator.name) : "—")}</dd></div>
        <div><dt>Classification result</dt><dd>${(doc.extractedInfo && doc.extractedInfo["Classification confidence"] !== undefined && doc.extractedInfo["Classification confidence"] !== "") ? FL.esc("Stored confidence " + doc.extractedInfo["Classification confidence"]) : FL.ui.statusBadge(klass.status === "pending" ? "pending" : klass.status)}</dd></div>
      </dl>
      <h3 class="block-label">Evidence package</h3>
      <dl class="facts compact">
        <div><dt>Package ID</dt><dd>${doc.packageId ? FL.esc(doc.packageId) : "—"}</dd></div>
        <div><dt>Requirement slot</dt><dd>${doc.requirementIndex != null && doc.requirementIndex !== "" ? FL.esc(String(doc.requirementIndex)) : "—"}</dd></div>
        <div><dt>Package completeness</dt><dd>${doc.extractedInfo && doc.extractedInfo["Package completeness"] ? FL.esc(doc.extractedInfo["Package completeness"]) : "—"}</dd></div>
      </dl>
      ${function () {
        const raw = doc.extractedInfo && doc.extractedInfo["Evidence checklist"];
        if (!raw) return "";
        let items = [];
        try { items = JSON.parse(raw); } catch (e) { return ""; }
        if (!Array.isArray(items) || !items.length) return "";
        return `<h3 class="block-label">Per-item evidence checklist</h3><ul class="check-list">${items.map(function (item) {
          const tone = item.state === "system_verified" || item.state === "reviewer_verified" ? "valid" : item.state === "missing" ? "invalid" : "pending";
          return `<li>${FL.ui.statusBadge(tone)} ${FL.esc(item.label || "")} <span class="muted">(${FL.esc(item.state || "")})</span></li>`;
        }).join("")}</ul>`;
      }()}
      <h3 class="block-label">Documentary evidence</h3>
      <p>${FL.ui.statusBadge(validation.evidenceStatus)} ${validation.evidenceMissing.length ? FL.esc(validation.evidenceMissing[0]) : (doc.extractedInfo && doc.extractedInfo["Missing evidence items"] ? FL.esc(doc.extractedInfo["Missing evidence items"]) : "The required evidence for the matched indicator is attached.")}</p>
      <h3 class="block-label">Duplicate check</h3>
      <p>${FL.ui.statusBadge(validation.duplicateStatus)} File hash ${FL.esc(doc.hash || "—")}${validation.duplicateOf ? ". Matches " + FL.esc(validation.duplicateOf) + "." : ""}</p>
      <h3 class="block-label">Overall validation</h3>
      <p>${validation.overall === "valid" ? FL.ui.badge("valid", "Valid") : validation.overall === "invalid" ? FL.ui.badge("invalid", "Invalid") : FL.ui.badge("pending", "Reviewer validation required")}</p>
      ${options.includeCorrection ? FL.documents.extractionCorrectionHtml(doc, canDecide) : ""}`;
  },

  accumulated: function (doc) {
    const found = doc.indicatorId ? FL.rules.findIndicator(doc.indicatorId) : null;
    if (!found) return { criterion: 0, kra: 0, max: null };
    const aggregate = FL.scoring.aggregateFaculty(doc.facultyId);
    const kra = aggregate.kras.find(function (item) { return item.id === found.kra.id; });
    const criterion = kra && kra.criteria.find(function (item) { return item.id === found.criterion.id; });
    return {
      criterion: criterion ? criterion.earned : 0,
      kra: kra ? kra.credited : 0,
      max: found.indicator.maxPoints
    };
  },

  award: function (doc, assigned) {
    const found = doc.indicatorId ? FL.rules.findIndicator(doc.indicatorId) : null;
    if (!found) return { error: "Match an Annex I indicator before assigning a score." };
    const indicator = found.indicator;
    const max = indicator.maxPoints;
    if (FL.documents.isSetSefSemesterDocument(doc)) {
      if (!Number.isFinite(assigned) || assigned < 0) {
        return { error: "Use 0 for semester confirmation. SET/SEF indicator points come from the evaluation-period average, not each PDF." };
      }
      if (assigned > 0) {
        return {
          error: "This upload is one semester of SET/SEF. Enter 0 to confirm the semester record. "
            + "Aggregated SET and SEF indicator scores come from published Admin configuration across eligible semesters — do not enter the full indicator maximum on a single semester record."
        };
      }
      const period = FL.documents.periodSimulationDisplay(doc);
      return {
        found: found,
        percent: 100,
        finalScore: 0,
        duplicateIndicator: false,
        setSefSemesterConfirmation: true,
        review: {
          indicatorId: indicator.id,
          kraId: found.kra.id,
          criterionId: found.criterion.id,
          officialPoints: typeof indicator.points === "number" ? indicator.points : (indicator.formula ? indicator.formula.multiplier : null),
          officialLabel: indicator.pointsLabel || "",
          officialMax: max,
          contributionPercent: 100,
          assignedScore: 0,
          finalScore: 0,
          periodAggregationScore: period && period.score != null ? period.score : null,
          periodCoverage: period ? period.filled : ""
        }
      };
    }
    if (!Number.isFinite(assigned) || assigned < 0 || assigned > max) {
      return { error: "Enter a score from 0 through the official maximum of " + max + "." };
    }
    let percent = 100;
    if (indicator.contribution === "declared") {
      const subject = FL.scoring.subjectContribution(doc);
      if (!subject || typeof subject.percent !== "number") {
        return { error: "A declared contribution percentage is required before this score can be approved." };
      }
      percent = subject.percent;
    }
    if (percent < 0 || percent > 100) return { error: "Contribution percentage must be from 0 through 100." };
    const finalScore = FL.scoring.round(assigned * (percent / 100));
    if (finalScore > max) return { error: "The score after contribution cannot exceed the official maximum of " + max + "." };
    let replaced = 0;
    let duplicateIndicator = false;
    FL.store.documents.forEach(function (other) {
      if (other.id === doc.id || other.facultyId !== doc.facultyId || other.status !== "approved") return;
      const otherId = (other.review && other.review.indicatorId) || other.indicatorId;
      if (otherId !== indicator.id) return;
      duplicateIndicator = true;
      if (other.review && typeof other.review.finalScore === "number") replaced = Math.max(replaced, other.review.finalScore);
    });
    if (doc.status === "approved" && doc.review && doc.review.criterionId === found.criterion.id && typeof doc.review.finalScore === "number") {
      replaced = Math.max(replaced, doc.review.finalScore);
    }
    const totals = FL.documents.accumulated(doc);
    const room = FL.scoring.round(Math.max(0, found.criterion.maxPoints - (totals.criterion - replaced)));
    if (finalScore > room) {
      return { error: "This score would exceed the criterion maximum of " + found.criterion.maxPoints + ". Approved points already accumulated: " + totals.criterion + "." };
    }
    return {
      found: found,
      percent: percent,
      finalScore: finalScore,
      duplicateIndicator: duplicateIndicator,
      review: {
        indicatorId: indicator.id,
        kraId: found.kra.id,
        criterionId: found.criterion.id,
        officialPoints: typeof indicator.points === "number" ? indicator.points : (indicator.formula ? indicator.formula.multiplier : null),
        officialLabel: indicator.pointsLabel || "",
        officialMax: max,
        contributionPercent: percent,
        assignedScore: assigned,
        finalScore: finalScore
      }
    };
  },

  scorePreview: function (doc, assigned) {
    const found = doc.indicatorId ? FL.rules.findIndicator(doc.indicatorId) : null;
    if (!found) return { percent: null, finalScore: null, max: null };
    let percent = 100;
    if (found.indicator.contribution === "declared") {
      const subject = FL.scoring.subjectContribution(doc);
      percent = subject && typeof subject.percent === "number" ? subject.percent : null;
    }
    const max = found.indicator.maxPoints;
    if (!Number.isFinite(assigned) || assigned < 0) return { percent: percent, finalScore: null, max: max };
    if (percent === null) return { percent: null, finalScore: null, max: max };
    return { percent: percent, finalScore: FL.scoring.round(assigned * (percent / 100)), max: max };
  },

  scoreHtml: function (scored, doc, canDecide) {
    if (doc.ocr && doc.ocr.status === "processing") return `<div class="card-head"><h2>KRA scoring</h2></div>${FL.ui.loading("Score loading", "The score is prepared after extraction and rule matching.")}`;
    if (!scored.indicator) {
      return `<div class="card-head"><h2>KRA scoring</h2></div><div class="alert alert-warning">Match an Annex I indicator before a score is assigned. The official maximum, evidence, and contribution rules appear with that indicator.</div>`;
    }
    const totals = FL.documents.accumulated(doc);
    const officialMax = scored.historical ? scored.officialMax : scored.indicator.maxPoints;
    const provisional = FL.documents.provisionalScore(doc);
    const effective = FL.documents.effectiveSimulationScore(doc);
    const period = FL.documents.periodSimulationDisplay(doc);
    const scoreSource = FL.documents.simulationScoreSource(doc);
    const oversight = FL.documents.oversightStatusLabel(doc);
    const credited = FL.documents.creditedPoints(doc);
    const reviewerAssigned = doc.review && typeof doc.review.assignedScore === "number" ? doc.review.assignedScore : null;
    const showContributor = FL.documents.usesContributorPercent(scored.indicator);
    const duplicateNote = canDecide && doc.status !== "approved" && FL.store.documents.some(function (other) {
      if (other.id === doc.id || other.facultyId !== doc.facultyId || other.status !== "approved") return false;
      const otherId = (other.review && other.review.indicatorId) || other.indicatorId;
      return otherId === scored.indicator.id;
    });
    return `
      <div class="card-head"><h2>KRA scoring</h2>${FL.ui.statusBadge(doc.status)}</div>
      <p class="note">Read-only summary. Enter the reviewer-assigned score on the Review tab.</p>
      <div class="score-summary-strip">
        <div class="score-mini">
          <div class="score-mini-label">Simulation score</div>
          <div class="score-mini-value is-credited">${period && period.score != null ? "SET period " + FL.esc(String(period.score)) : effective == null ? "Score unavailable" : FL.esc(String(effective))}</div>
        </div>
        <div class="score-mini">
          <div class="score-mini-label">Score source</div>
          <div class="score-mini-value">${FL.esc(scoreSource)}</div>
        </div>
        <div class="score-mini">
          <div class="score-mini-label">Official max</div>
          <div class="score-mini-value">${FL.esc(String(officialMax))}</div>
        </div>
      </div>
      ${oversight ? `<p class="note">${FL.esc(oversight)} · Rank simulation uses the effective score above; this is not final DBM–CHED approval.</p>` : ""}
      <p class="formula">${FL.esc(FL.documents.indicatorFormulaText(scored.indicator))}</p>
      <dl class="facts">
        <div><dt>Assigned KRA</dt><dd>${FL.esc(scored.kra.code + " — " + scored.kra.name)}</dd></div>
        <div><dt>Criterion</dt><dd>${FL.esc(scored.criterion.name)}</dd></div>
        <div><dt>Identified indicator</dt><dd>${FL.esc(scored.indicator.name)}</dd></div>
        <div><dt>System-calculated score</dt><dd>${provisional == null ? "—" : FL.esc(String(provisional))}</dd></div>
        <div><dt>Effective simulation score</dt><dd><strong>${effective == null ? "Score unavailable" : FL.esc(String(effective))}</strong> (${FL.esc(scoreSource)})</dd></div>
        <div><dt>Official indicator maximum</dt><dd><strong>${FL.esc(String(officialMax))}</strong></dd></div>
        <div><dt>Official credited points</dt><dd><strong>${FL.esc(String(credited))}</strong>${doc.status === "approved" || doc.status === "system-approved" ? "" : " <span class=\"note\">Separate from simulation until reviewer validates.</span>"}</dd></div>
        ${reviewerAssigned != null ? `<div><dt>Reviewer-assigned score</dt><dd>${FL.esc(String(reviewerAssigned))}</dd></div>` : ""}
        ${doc.status === "approved" && showContributor ? `<div><dt>Credited after contribution</dt><dd><strong>${scored.finalScore === null || scored.finalScore === undefined ? "—" : FL.esc(String(scored.finalScore))}</strong></dd></div>` : ""}
        <div><dt>Faculty accumulated score</dt><dd>${FL.esc(String(totals.criterion))} in this criterion · ${FL.esc(String(totals.kra))} in this KRA</dd></div>
      </dl>
      ${duplicateNote ? `<div class="alert alert-warning">Another approved document already uses this indicator. You can still approve this document. Only the highest score for this indicator counts in the faculty total.</div>` : ""}
      <p class="note">${scored.historical ? "This approved score is kept as it was recorded. A later change to the official KRA configuration does not change it." : "Confirm or adjust the reviewer-assigned score in the Reviewer decision section. Credited points update only after approval."}</p>`;
  },

  contributionHtml: function (scored, doc) {
    if (!scored.indicator) {
      return `<div class="card-head"><h2>Contribution</h2></div><p>Contribution is shown after an indicator is matched. For a collaborative output, authors declare their percentages in the prescribed certification. FacultyLink does not assign a percentage.</p>`;
    }
    if (scored.indicator.contribution !== "declared") {
      return `<div class="card-head"><h2>Contribution</h2></div><p>${FL.esc(FL.documents.contributionNote(scored.indicator))}</p><p class="formula">${FL.esc(FL.scoring.formula)}</p>`;
    }
    if (!scored.rows.length) {
      return `<div class="card-head"><h2>Contribution</h2></div>${FL.ui.empty("No contribution certification", "The prescribed author or inventor certification is not attached, so a contribution percentage cannot be applied.")}`;
    }
    return `
      <div class="card-head"><h2>Contribution</h2></div>
      <p>Percentages are the shares declared by the claimants. Base points ${FL.esc(String(scored.basePoints))}.</p>
      <div class="table-wrap"><table class="data">
        <thead><tr><th>Author</th><th>Contribution</th><th>Computed points</th></tr></thead>
        <tbody>${scored.rows.map(function (row) {
          return `<tr class="${row.subject ? "is-selected" : ""}"><td>${FL.esc(row.author)}</td><td>${FL.esc(String(row.percent))}%</td><td>${row.computed === null ? "—" : FL.esc(String(row.computed))}</td></tr>`;
        }).join("")}</tbody>
      </table></div>
      <p class="formula">${FL.esc(scored.basePoints + " × " + scored.contributionPercent + "% = " + scored.finalScore)}</p>`;
  },

  workflowHtml: function (doc, scored) {
    const info = doc.extractedInfo || {};
    const branch = info["Processing branch"] || "";
    let current = 8;
    if (!doc.ocr || doc.ocr.status !== "completed") current = 1;
    else if (branch === "Incomplete" || scored.validation.overall === "invalid") current = 3;
    else if (branch === "Needs verification" || branch === "Requires review") current = 6;
    else if (branch === "Complete and valid" || info["Simulation eligible"] === "yes") current = 5;
    else if (doc.status === "approved" || doc.status === "validated" || doc.status === "system-approved") current = 8;
    else current = 4;
    return `
      <section class="card review-section" id="workflow">
        <div class="card-head"><h2>Document processing workflow</h2></div>
        <ol class="workflow">
          ${FL.rules.workflow.map(function (step, index) {
            const state = index < current ? "done" : index === current ? "current" : "wait";
            return `<li class="${state}"><span>${index + 1}</span>${FL.esc(step)}</li>`;
          }).join("")}
        </ol>
      </section>`;
  },

  _tevRecordFilter: "all",

  tevStatusPillClass: function (label) {
    if (label === "Validated") return "tev-pill tev-pill--validated";
    if (label === "Needs Revision") return "tev-pill tev-pill--revision";
    if (label === "Rejected") return "tev-pill tev-pill--rejected";
    if (label === "Incomplete Extraction") return "tev-pill tev-pill--incomplete";
    return "tev-pill tev-pill--pending";
  },

  tevTechnicalDetailsHtml: function (tev) {
    const flags = [];
    if (tev.duplicatePeriodWarning) flags.push("Duplicate period warning");
    if (tev.missingFields && tev.missingFields.length) {
      flags.push("Missing fields: " + tev.missingFields.join(", "));
    }
    return `<details class="tev-tech-details">
      <summary>Technical details</summary>
      <dl class="set-sef-calc-grid tev-tech-grid">
        <div><dt>Record ID</dt><dd>${FL.esc(tev.id || tev.teachingEvaluationId || "—")}</dd></div>
        <div><dt>Extraction status</dt><dd>${FL.esc(tev.extractionStatus || "—")}</dd></div>
        <div><dt>OCR verification</dt><dd>${FL.esc(tev.ocrVerificationStatus || "—")}</dd></div>
        <div><dt>Source section</dt><dd>${FL.esc(tev.sourceSectionRef || "—")}</dd></div>
        ${tev.extractionFlags && tev.extractionFlags.length
          ? `<div class="field-span"><dt>Extraction flags</dt><dd>${FL.esc(tev.extractionFlags.join(", "))}</dd></div>` : ""}
        ${flags.length ? `<div class="field-span"><dt>Warnings</dt><dd>${FL.esc(flags.join(" · "))}</dd></div>` : ""}
      </dl>
    </details>`;
  },

  teachingEvaluationDrawerShellHtml: function (canDecide) {
    const actions = canDecide ? `
      <p class="field-error" id="tev-drawer-error" role="alert"></p>
      <div class="decision-row tev-drawer-actions">
        <button class="btn btn-primary" type="button" data-tev-decision="approve">Validate</button>
        <button class="btn btn-warning" type="button" data-tev-decision="revision">Request revision</button>
        <button class="btn btn-danger" type="button" data-tev-decision="reject">Reject</button>
        <button class="btn btn-ghost" type="button" data-tev-decision="save">Save corrections</button>
      </div>` : `<p class="note">You do not have permission to change reviewer decisions on this document.</p>`;
    return `<div id="tev-review-drawer" class="tev-drawer" aria-hidden="true" aria-labelledby="tev-drawer-title">
      <button type="button" class="tev-drawer-backdrop" aria-label="Close review panel"></button>
      <div class="tev-drawer-panel" role="dialog" aria-modal="true">
        <header class="tev-drawer-head">
          <div>
            <p class="eyebrow">Semester evaluation</p>
            <h2 id="tev-drawer-title">Review SET/SEF record</h2>
            <p class="sub" id="tev-drawer-subtitle"></p>
          </div>
          <button type="button" class="btn btn-ghost btn-small tev-drawer-close" aria-label="Close">Close</button>
        </header>
        <div class="tev-drawer-body">
          <div class="tev-drawer-split">
            <form class="tev-drawer-form correction-grid" id="tev-drawer-form" onsubmit="return false;">
              <label class="field"><span>Evaluation type</span>
                <select id="tev-drawer-type" ${canDecide ? "" : "disabled"}>
                  <option value="">— unchanged —</option>
                  <option value="SET">SET</option>
                  <option value="SEF">SEF</option>
                </select></label>
              <label class="field"><span>Academic year</span>
                <input id="tev-drawer-year" type="text" placeholder="e.g. 2024-2025" ${canDecide ? "" : "readonly"}></label>
              <label class="field"><span>Semester</span>
                <input id="tev-drawer-sem" type="text" placeholder="e.g. 1st Semester" ${canDecide ? "" : "readonly"}></label>
              <label class="field"><span>Overall rating</span>
                <input id="tev-drawer-rating" type="text" inputmode="decimal" ${canDecide ? "" : "readonly"}></label>
              <label class="field"><span>Rating scale</span>
                <input id="tev-drawer-scale" type="text" inputmode="decimal" ${canDecide ? "" : "readonly"}></label>
              <label class="field field-span"><span>Reviewer remarks</span>
                <textarea id="tev-drawer-remarks" rows="4" placeholder="Explain your decision or corrections (required for revision, rejection, or field changes)" ${canDecide ? "" : "readonly"}></textarea></label>
              <div class="field field-span"><span>Review decision</span>
                <p id="tev-drawer-status-display" class="tev-drawer-status"></p></div>
              <div id="tev-drawer-tech-slot" class="field-span"></div>
              ${actions}
            </form>
            <aside class="tev-drawer-preview" aria-label="Original document preview">
              <p class="eyebrow">Original document</p>
              <p class="note">Compare the extracted fields with the PDF for this semester.</p>
              <div class="tev-drawer-preview-frame" id="tev-drawer-preview-frame"></div>
            </aside>
          </div>
        </div>
      </div>
    </div>`;
  },

  teachingEvaluationsPanelHtml: function (doc, canDecide) {
    const list = doc.teachingEvaluations;
    if (!list || !list.length) return "";
    const ui = FL.tevReviewUi;
    const summary = doc.teachingEvaluationSummary || {};
    const counts = ui.summaryCounts(list);
    const filter = FL.documents._tevRecordFilter || "all";
    const filtered = list.filter(function (tev) { return ui.passesFilter(tev, filter); });
    const note = summary.summaryLine
      ? summary.summaryLine + " — " + (summary.note || "Review each semester separately.")
      : (summary.note || "Review each SET/SEF semester on its own. Decisions are saved per record.");
    const filterBtn = function (key, label) {
      const active = filter === key ? " is-active" : "";
      return `<button type="button" class="tev-filter-chip${active}" data-tev-filter="${FL.esc(key)}">${FL.esc(label)}</button>`;
    };
    const needsRevisionLine = counts.needsRevision
      ? `<div class="tev-stat"><span class="tev-stat-value">${counts.needsRevision}</span><span class="tev-stat-label">Needs revision</span></div>`
      : "";
    const incompleteLine = counts.incomplete
      ? `<div class="tev-stat"><span class="tev-stat-value">${counts.incomplete}</span><span class="tev-stat-label">Incomplete extraction</span></div>`
      : "";
    const rows = filtered.map(function (tev) {
      const tevId = tev.id || tev.teachingEvaluationId;
      const label = ui.statusLabel(tev);
      const pillClass = FL.documents.tevStatusPillClass(label);
      const highlight = doc._highlightTev === tevId || doc._tevDrawerOpen === tevId ? " tev-row--focus" : "";
      const rating = tev.ratingRaw != null && tev.ratingRaw !== "" ? tev.ratingRaw : "—";
      return `<tr class="tev-row${highlight}" data-tev-row-id="${FL.esc(tevId)}" id="tev-${FL.esc(tevId)}">
        <td data-label="Type"><strong>${FL.esc(tev.evaluationType || "—")}</strong></td>
        <td data-label="Period">${FL.esc(tev.academicYear || "—")}<br><span class="sub">${FL.esc(tev.semester || "—")}</span></td>
        <td data-label="Rating">${FL.esc(String(rating))}</td>
        <td data-label="Status"><span class="${pillClass}">${FL.esc(label)}</span></td>
        <td data-label="Action" class="tev-row-action">
          <button type="button" class="btn btn-primary btn-small" data-tev-review="${FL.esc(tevId)}">Review</button>
        </td>
      </tr>`;
    }).join("");
    const emptyRow = filtered.length
      ? ""
      : `<tr><td colspan="5" class="tev-empty">${FL.esc("No records match this filter.")}</td></tr>`;
    return `<section class="card review-section" id="teaching-evaluations-panel" aria-label="Teaching evaluations">
      <div class="card-head"><h2>SET/SEF semester records</h2></div>
      <p class="note">${FL.esc(note)}</p>
      <div class="tev-summary" role="group" aria-label="Review progress">
        <div class="tev-stat"><span class="tev-stat-value">${counts.total}</span><span class="tev-stat-label">Total evaluations</span></div>
        <div class="tev-stat"><span class="tev-stat-value">${counts.reviewed}</span><span class="tev-stat-label">Reviewed</span></div>
        <div class="tev-stat"><span class="tev-stat-value">${counts.pending}</span><span class="tev-stat-label">Pending review</span></div>
        ${needsRevisionLine}${incompleteLine}
      </div>
      <div class="tev-filters" role="toolbar" aria-label="Filter evaluations">
        ${filterBtn("all", "All")}
        ${filterBtn("set", "SET")}
        ${filterBtn("sef", "SEF")}
        ${filterBtn("pending", "Pending review")}
        ${filterBtn("reviewed", "Reviewed")}
      </div>
      <div class="table-wrap tev-table-wrap">
        <table class="data tev-table">
          <thead><tr>
            <th scope="col">Type</th>
            <th scope="col">Academic year &amp; semester</th>
            <th scope="col">Extracted rating</th>
            <th scope="col">Reviewer status</th>
            <th scope="col"><span class="sr-only">Actions</span></th>
          </tr></thead>
          <tbody>${rows}${emptyRow}</tbody>
        </table>
      </div>
      ${FL.documents.teachingEvaluationDrawerShellHtml(canDecide)}
    </section>`;
  },

  closeTeachingEvaluationDrawer: function (doc) {
    const drawer = document.getElementById("tev-review-drawer");
    if (!drawer) return;
    drawer.classList.remove("is-open");
    drawer.setAttribute("aria-hidden", "true");
    document.body.classList.remove("tev-drawer-open");
    const form = document.getElementById("tev-drawer-form");
    if (form) form.dataset.activeTevId = "";
    if (doc) delete doc._tevDrawerOpen;
    FL.documents._tevDrawerDoc = null;
  },

  openTeachingEvaluationDrawer: function (session, doc, canDecide, tevId) {
    const list = doc.teachingEvaluations || [];
    const tev = list.find(function (row) {
      return (row.id || row.teachingEvaluationId) === tevId;
    });
    if (!tev) return;
    const drawer = document.getElementById("tev-review-drawer");
    if (!drawer) return;
    const ui = FL.tevReviewUi;
    const label = ui.statusLabel(tev);
    const typeEl = document.getElementById("tev-drawer-type");
    const yearEl = document.getElementById("tev-drawer-year");
    const semEl = document.getElementById("tev-drawer-sem");
    const ratingEl = document.getElementById("tev-drawer-rating");
    const scaleEl = document.getElementById("tev-drawer-scale");
    const remarksEl = document.getElementById("tev-drawer-remarks");
    const statusEl = document.getElementById("tev-drawer-status-display");
    const subtitle = document.getElementById("tev-drawer-subtitle");
    const errEl = document.getElementById("tev-drawer-error");
    const techSlot = document.getElementById("tev-drawer-tech-slot");
    const previewFrame = document.getElementById("tev-drawer-preview-frame");
    if (errEl) errEl.textContent = "";
    if (typeEl) typeEl.value = tev.evaluationType === "SET" || tev.evaluationType === "SEF" ? tev.evaluationType : "";
    if (yearEl) yearEl.value = tev.academicYear || "";
    if (semEl) semEl.value = tev.semester || "";
    if (ratingEl) ratingEl.value = tev.ratingRaw || "";
    if (scaleEl) scaleEl.value = tev.ratingScale != null ? String(tev.ratingScale) : "";
    if (remarksEl) remarksEl.value = tev.reviewerRemarks || "";
    if (statusEl) {
      statusEl.textContent = label;
      statusEl.className = "tev-drawer-status " + FL.documents.tevStatusPillClass(label);
    }
    if (subtitle) {
      subtitle.textContent = (tev.evaluationType || "Evaluation") + " · "
        + (tev.academicYear || "Year unknown") + " · " + (tev.semester || "Semester unknown");
    }
    if (techSlot) techSlot.innerHTML = FL.documents.tevTechnicalDetailsHtml(tev);
    const form = document.getElementById("tev-drawer-form");
    if (form) form.dataset.activeTevId = tevId;
    doc._tevDrawerOpen = tevId;
    FL.documents._tevDrawerDoc = doc;
    if (previewFrame) {
      FL.documents.loadDocumentPdfPreview(doc, previewFrame);
    }
    drawer.classList.add("is-open");
    drawer.setAttribute("aria-hidden", "false");
    document.body.classList.add("tev-drawer-open");
    const closeBtn = drawer.querySelector(".tev-drawer-close");
    if (closeBtn) closeBtn.focus();
  },

  repaintTeachingEvaluationsPanel: function (session, doc, canDecide) {
    const existing = document.getElementById("teaching-evaluations-panel");
    if (!existing) return;
    const openId = doc._tevDrawerOpen || "";
    existing.outerHTML = FL.documents.teachingEvaluationsPanelHtml(doc, canDecide);
    FL.documents.bindTeachingEvaluationPanel(session, doc, canDecide);
    FL.documents.bindTeachingEvaluationActions(session, doc, canDecide);
    if (openId) FL.documents.openTeachingEvaluationDrawer(session, doc, canDecide, openId);
  },

  bindTeachingEvaluationPanel: function (session, doc, canDecide) {
    if (!doc.teachingEvaluations || !doc.teachingEvaluations.length) return;
    document.querySelectorAll("[data-tev-filter]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        FL.documents._tevRecordFilter = btn.getAttribute("data-tev-filter") || "all";
        FL.documents.repaintTeachingEvaluationsPanel(session, doc, canDecide);
      });
    });
    document.querySelectorAll("[data-tev-review]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const tevId = btn.getAttribute("data-tev-review");
        FL.documents.openTeachingEvaluationDrawer(session, doc, canDecide, tevId);
      });
    });
    const drawer = document.getElementById("tev-review-drawer");
    if (!drawer) return;
    const close = function () {
      FL.documents.closeTeachingEvaluationDrawer(doc);
    };
    drawer.querySelectorAll(".tev-drawer-close, .tev-drawer-backdrop").forEach(function (el) {
      el.addEventListener("click", close);
    });
    if (!FL.documents._tevEscapeBound) {
      FL.documents._tevEscapeBound = true;
      document.addEventListener("keydown", function (ev) {
        if (ev.key !== "Escape") return;
        const openDrawer = document.getElementById("tev-review-drawer");
        if (openDrawer && openDrawer.classList.contains("is-open")) {
          FL.documents.closeTeachingEvaluationDrawer(FL.documents._tevDrawerDoc);
        }
      });
    }
  },

  buildTeachingEvaluationReviewPayload: function (baseline, decision) {
    const remarks = (document.getElementById("tev-drawer-remarks").value || "").trim();
    const payload = { remarks: remarks, reason: remarks };
    const typeEl = document.getElementById("tev-drawer-type");
    const typeVal = typeEl && typeEl.value ? typeEl.value.trim() : "";
    const yearVal = (document.getElementById("tev-drawer-year").value || "").trim();
    const semVal = (document.getElementById("tev-drawer-sem").value || "").trim();
    const ratingVal = (document.getElementById("tev-drawer-rating").value || "").trim();
    const scaleVal = (document.getElementById("tev-drawer-scale").value || "").trim();
    if (typeVal && typeVal !== (baseline.evaluationType || "")) payload.evaluationType = typeVal;
    if (yearVal && yearVal !== (baseline.academicYear || "")) payload.academicYear = yearVal;
    if (semVal && semVal !== (baseline.semester || "")) payload.semester = semVal;
    if (ratingVal && ratingVal !== (baseline.ratingRaw || "")) payload.ratingRaw = ratingVal;
    if (scaleVal && String(baseline.ratingScale != null ? baseline.ratingScale : "") !== scaleVal) {
      payload.ratingScale = scaleVal;
    }
    if (decision !== "save") payload.decision = decision;
    return payload;
  },

  bindTeachingEvaluationActions: function (session, doc, canDecide) {
    if (!canDecide || !doc.teachingEvaluations || !doc.teachingEvaluations.length) return;
    const list = doc.teachingEvaluations;
    const form = document.getElementById("tev-drawer-form");
    document.querySelectorAll("#tev-review-drawer [data-tev-decision]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const decision = btn.getAttribute("data-tev-decision");
        const tevId = form && form.dataset.activeTevId;
        if (!tevId) return;
        const idx = list.findIndex(function (row) {
          return (row.id || row.teachingEvaluationId) === tevId;
        });
        if (idx < 0) return;
        const errEl = document.getElementById("tev-drawer-error");
        if (errEl) errEl.textContent = "";
        const baseline = list[idx];
        const payload = FL.documents.buildTeachingEvaluationReviewPayload(baseline, decision);
        const remarks = payload.remarks || "";
        if ((decision === "reject" || decision === "revision") && remarks.length < 8) {
          if (errEl) errEl.textContent = "Add reviewer remarks (at least 8 characters) for revision or rejection.";
          return;
        }
        const hasFieldChange = payload.evaluationType || payload.academicYear || payload.semester
          || payload.ratingRaw || payload.ratingScale;
        if ((decision === "save" || hasFieldChange) && remarks.length < 8) {
          if (errEl) errEl.textContent = "Add remarks explaining your corrections (at least 8 characters).";
          return;
        }
        if (decision === "save" && !hasFieldChange) {
          if (errEl) errEl.textContent = "Change at least one field, or choose Validate, Request revision, or Reject.";
          return;
        }
        const toastOk = {
          approve: "Evaluation validated.",
          reject: "Evaluation rejected.",
          revision: "Revision requested for this evaluation.",
          save: "Corrections saved."
        };
        FL.store.submitTeachingEvaluationReview(session, doc.id, tevId, payload).then(function (data) {
          if (data.document) Object.assign(doc, data.document);
          if (data.teachingEvaluation && idx >= 0) list[idx] = data.teachingEvaluation;
          delete doc._tevDrawerOpen;
          FL.ui.toast(toastOk[decision] || "Review saved.", "ok");
          FL.documents.paintReview(session, doc, canDecide);
        }).catch(function (error) {
          if (errEl) errEl.textContent = error.message || "Could not save this review. Try again.";
          FL.ui.toast(error.message || "Could not save review.", "danger");
        });
      });
    });
  },

  decisionHtml: function (doc, canDecide) {
    if (!canDecide) {
      return `
        <div class="card-head"><h2>Reviewer feedback</h2></div>
        ${doc.feedback ? `<p>${FL.esc(doc.feedback)}</p>` : `<p>No reviewer feedback has been recorded.</p>`}
        <p class="meta">${doc.decidedAt ? "Recorded " + FL.esc(FL.formatWhen(doc.decidedAt)) : ""}</p>`;
    }
    const scored = FL.scoring.scoreDocument(doc);
    const officialMax = scored.historical ? scored.officialMax : (scored.indicator ? scored.indicator.maxPoints : null);
    const assignedRaw = scored.historical ? scored.basePoints : FL.documents.defaultAssignedScore(doc);
    const assigned = assignedRaw === "" ? "" : assignedRaw;
    const preview = FL.documents.scorePreview(doc, assigned === "" ? NaN : Number(assigned));
    const isSetSef = FL.documents.isSetSefSemesterDocument(doc);
    const period = FL.documents.periodSimulationDisplay(doc);
    const scoreLabel = isSetSef
      ? "Document credited points (use 0 for SET/SEF semester confirmation)"
      : (scored.indicator && scored.indicator.formula && scored.indicator.formula.type === "rating"
        ? "Reviewer-assigned score (verified points)"
        : "Reviewer-assigned score");
    const scoreHint = isSetSef
      ? "Confirm this semester record with 0 document points. "
        + (period && period.score != null
          ? "Current period aggregation: " + period.score + " pts (" + (period.filled || "coverage") + "). "
          : (period && period.filled ? "Coverage " + period.filled + ". " : ""))
        + "Official SET/SEF indicator points apply once per evaluation period (per published rules), not per uploaded PDF."
      : (scored.indicator && FL.documents.usesContributorPercent(scored.indicator)
        ? "Base points before the declared contribution percentage. Credited points appear in the preview below."
        : (scored.indicator && scored.indicator.formula && scored.indicator.formula.type === "rating"
          ? "Enter verified points from the evaluation rating and applicable formula. Provisional score is a starting suggestion."
          : "Enter verified points for this evidence. They cannot exceed the official maximum."));
    const scoreField = officialMax == null ? `
      <p class="note">Match an indicator before assigning a score.</p>` : `
      <div class="score-panel">
        <label class="field" for="decision-score"><span>${FL.esc(scoreLabel)}</span>
          <input id="decision-score" class="score-input score-input-lg" type="number" min="0" max="${FL.esc(String(officialMax))}" step="0.01" inputmode="decimal" value="${assigned === "" ? "" : FL.esc(String(assigned))}" placeholder="0">
        </label>
        <p class="note">Official maximum ${FL.esc(String(officialMax))}. ${FL.esc(scoreHint)}</p>
        ${FL.documents.decisionScorePreviewHtml(doc, preview, officialMax)}
      </div>`;
    return `
      <div class="card-head"><h2>Reviewer decision</h2></div>
      ${scoreField}
      <label class="field" for="feedback"><span>Remarks</span>
        <textarea id="feedback" rows="5" placeholder="Justification for the assigned score, missing evidence, or the reason for rejection">${FL.esc(doc.feedback || doc.remarks || "")}</textarea>
      </label>
      <p class="field-error" id="feedback-error"></p>
      <div class="decision-row">
        <button class="btn btn-primary" type="button" id="approve">Accept</button>
        <button class="btn btn-primary${doc.status === "approved" ? "" : " is-hidden"}" type="button" id="correct-score">Correct score</button>
        <button class="btn btn-danger" type="button" id="reject">Reject</button>
        <button class="btn btn-warning" type="button" id="revise">Request revision</button>
        <button class="btn" type="button" id="reopen">Reopen</button>
      </div>`;
  },

  bindDecision: function (session, doc) {
    const feedback = document.getElementById("feedback");
    const error = document.getElementById("feedback-error");
    const user = FL.store.userById(session.userId);
    const requireText = function () {
      if (feedback.value.trim()) {
        error.textContent = "";
        return true;
      }
      return false;
    };
    document.getElementById("approve").addEventListener("click", function () {
      error.textContent = "";
      if (!doc.indicatorId) {
        error.textContent = "Match an Annex I indicator before approval.";
        return;
      }
      const assignedInput = document.getElementById("decision-score");
      const assigned = assignedInput ? Number(assignedInput.value) : NaN;
      if (!assignedInput) {
        error.textContent = "Match an Annex I indicator and enter a reviewer-assigned score before approval.";
        return;
      }
      const award = FL.documents.award(doc, assigned);
      if (award.error) {
        error.textContent = award.error;
        if (assignedInput) assignedInput.focus();
        return;
      }
      const gate = FL.validation.approvalGate(doc);
      if (!gate.ok) {
        error.textContent = FL.validation.formatBlockers(gate.blockers);
        return;
      }
      const body = award.setSefSemesterConfirmation
        ? "<p>Confirm this SET/SEF semester record? This file supports one evaluation period; the configured semester aggregation determines official SET/SEF indicator points.</p>"
        : (award.duplicateIndicator
          ? "<p>Approve this document and record its score? Another approved document already uses this indicator for this faculty member. The document can still be approved. Only the highest score for that indicator is counted in the faculty KRA total, so points are not double-credited.</p>"
          : "<p>Approve this document and include its final score in the faculty KRA estimate? This remains an evaluation-support record.</p>");
      FL.ui.modal({
        title: "Approve document",
        body: body,
        confirmLabel: "Approve",
        onClose: function (ok) {
          if (!ok) return;
          doc.status = "approved";
          doc.feedback = feedback.value.trim();
          doc.remarks = doc.feedback;
          doc.review = award.review;
          doc.decidedAt = new Date().toISOString();
          const persist = FL.store.usesLiveDocuments() && session.role === "reviewer"
            ? FL.store.submitDocumentReview(doc, "approve", doc.feedback, session)
            : FL.store.saveDocument(doc, session);
          persist.then(function () {
            return FL.audit.record(user, "Approved document", doc.id, "Approved " + doc.name + ".");
          }).then(function () {
            return FL.store.addNotification({
              id: "NTF-" + Date.now(),
              audience: "administrator",
              title: "Document approved",
              body: doc.id + " was approved by " + user.name + ".",
              at: doc.decidedAt,
              read: false,
              ref: doc.id
            });
          }).then(function () {
            FL.ui.toast("Document approved.", "ok");
            FL.documents.paintReview(session, doc, true);
          }).catch(function (error) {
            FL.ui.toast(error.message || "The decision was not saved.", "danger");
          });
        }
      });
    });
    document.getElementById("revise").addEventListener("click", function () {
      if (!requireText()) {
        error.textContent = "Reviewer feedback is required when requesting a revision.";
        feedback.focus();
        return;
      }
      doc.status = "revision";
      doc.feedback = feedback.value.trim();
      doc.remarks = doc.feedback;
      doc.decidedAt = new Date().toISOString();
      const persistRev = FL.store.usesLiveDocuments() && session.role === "reviewer"
        ? FL.store.submitDocumentReview(doc, "revision", doc.feedback, session)
        : FL.store.saveDocument(doc, session);
      persistRev.then(function () {
        return FL.audit.record(user, "Requested revision", doc.id, doc.feedback);
      }).then(function () {
        if (FL.store.usesLiveDocuments()) return null;
        return FL.store.addNotification({
          id: "NTF-" + Date.now(),
          audience: "administrator",
          title: "Revision requested",
          body: user.name + " requested a revision on " + doc.id + ". " + doc.feedback,
          at: doc.decidedAt,
          read: false,
          ref: doc.id
        });
      }).then(function () {
        FL.ui.toast("Revision requested.", "warn");
        FL.documents.paintReview(session, doc, true);
      }).catch(function (error) {
        FL.ui.toast(error.message || "The decision was not saved.", "danger");
      });
    });
    document.getElementById("reject").addEventListener("click", function () {
      if (!requireText()) {
        error.textContent = "A reason is required when rejecting a document.";
        feedback.focus();
        return;
      }
      FL.ui.modal({
        title: "Reject document",
        body: "<p>Reject this document? The reason in the feedback will be kept with the record, and the score will stay out of the KRA estimate.</p>",
        confirmLabel: "Reject",
        danger: true,
        onClose: function (ok) {
          if (!ok) return;
          doc.status = "rejected";
          doc.feedback = feedback.value.trim();
          doc.remarks = doc.feedback;
          doc.decidedAt = new Date().toISOString();
          const persistRej = FL.store.usesLiveDocuments() && session.role === "reviewer"
            ? FL.store.submitDocumentReview(doc, "reject", doc.feedback, session)
            : FL.store.saveDocument(doc, session);
          persistRej.then(function () {
            return FL.audit.record(user, "Rejected document", doc.id, doc.feedback);
          }).then(function () {
            if (FL.store.usesLiveDocuments()) return null;
            return FL.store.addNotification({
              id: "NTF-" + Date.now(),
              audience: "administrator",
              title: "Document rejected",
              body: user.name + " rejected " + doc.id + ". " + doc.feedback,
              at: doc.decidedAt,
              read: false,
              ref: doc.id
            });
          }).then(function () {
            FL.ui.toast("Document rejected.", "danger");
            FL.documents.paintReview(session, doc, true);
          }).catch(function (error) {
            FL.ui.toast(error.message || "The decision was not saved.", "danger");
          });
        }
      });
    });
    const correctScore = document.getElementById("correct-score");
    if (correctScore) correctScore.addEventListener("click", function () {
      error.textContent = "";
      const assignedInput = document.getElementById("decision-score");
      const assigned = assignedInput ? Number(assignedInput.value) : NaN;
      const award = FL.documents.award(doc, assigned);
      if (award.error) {
        error.textContent = award.error;
        if (assignedInput) assignedInput.focus();
        return;
      }
      doc.status = "approved";
      doc.feedback = feedback.value.trim() || "Score corrected by the reviewer.";
      doc.remarks = doc.feedback;
      doc.review = award.review;
      doc.decidedAt = new Date().toISOString();
      FL.store.saveDocument(doc, session).then(function () {
        return FL.audit.record(user, "Corrected document score", doc.id, doc.feedback);
      }).then(function () {
        FL.ui.toast("Score corrected.", "ok");
        FL.documents.paintReview(session, doc, true);
      }).catch(function (saveError) {
        FL.ui.toast(saveError.message || "The correction was not saved.", "danger");
      });
    });
    document.getElementById("reopen").addEventListener("click", function () {
      doc.status = "pending-review";
      doc.review = null;
      doc.feedback = feedback.value.trim() || "Reopened for review. The provisional score is shown until the next decision.";
      doc.remarks = doc.feedback;
      doc.decidedAt = new Date().toISOString();
      FL.store.saveDocument(doc, session).then(function () {
        return FL.audit.record(user, "Reopened document", doc.id, doc.feedback);
      }).then(function () {
        FL.ui.toast("Document reopened.", "ok");
        FL.documents.paintReview(session, doc, true);
      }).catch(function (saveError) {
        FL.ui.toast(saveError.message || "The document was not reopened.", "danger");
      });
    });
  }
};

function _docFolderQueryContext() {
  const params = new URLSearchParams(window.location.search);
  return {
    facultyId: params.get("faculty") || "",
    kraId: params.get("kra") || "",
    criterionId: params.get("criterion") || "",
    indicatorId: params.get("indicator") || ""
  };
}

FL.pages["admin-documents"] = function (session) {
  FL.evidence.mount(session);
};

FL.pages["reviewer-documents"] = function (session) {
  FL.evidence.mount(session);
};

FL.pages["reviewer-queue"] = function (session) {
  window.location.replace("documents.html?filter=pending-review");
};

FL.pages["reviewer-review"] = function (session) { FL.documents.renderReview(session, true); };
FL.pages["admin-document-view"] = function (session) { FL.documents.renderReview(session, false); };
