/**
 * KRA II Criterion A — reviewer/faculty-friendly labels and compact review layout.
 */
window.FL = window.FL || {};

FL.kra2AWorkspaceUi = {
  CRITERION_ID: "kra2-a",

  SLOT_LABELS: {
    primary_output: "Primary supporting document",
    contribution_certificate: "Certificate of Contribution (Annex D)"
  },

  facultyStatusMeta: function (bundle) {
    var rs = ((bundle && bundle.reviewStatus) || "pending").toLowerCase();
    var submitted = !!(bundle && bundle.submittedForReviewAt);
    if (rs === "approved") {
      return { key: "approved", label: "Approved", hint: "Reviewer verified this accomplishment." };
    }
    if (rs === "rejected") {
      return { key: "needs-changes", label: "Needs Changes", hint: "Faculty may revise and resubmit." };
    }
    if (submitted) {
      return { key: "under-review", label: "Under Review", hint: "Waiting for reviewer verification." };
    }
    return { key: "draft", label: "Draft", hint: "Faculty has not submitted for review yet." };
  },

  indicatorLabel: function (indicatorId) {
    var ind = (indicatorId || "").trim();
    if (ind === "kra2-a-journal-sole") return "Sole author — journal article";
    if (ind === "kra2-a-journal-co") return "Co-author — journal article";
    if (FL.rules && FL.rules.indicatorById) {
      var row = FL.rules.indicatorById(ind);
      if (row && row.name) return row.name;
    }
    return "Journal article";
  },

  requiredSlotIds: function (bundle) {
    var contribution = bundle && bundle.contribution;
    if ((contribution || "").toLowerCase() === "declared") {
      return ["primary_output", "contribution_certificate"];
    }
    return ["primary_output"];
  },

  buildEvidenceSlotItems: function (bundle, primaryDoc, slotIds) {
    var checklist = (bundle && bundle.checklist) || {};
    var esc = FL.esc;
    return (slotIds || []).map(function (slotId) {
      var entry = checklist[slotId] || {};
      var docId = entry.documentId || "";
      var label = FL.kra2AWorkspaceUi.SLOT_LABELS[slotId] || slotId.replace(/_/g, " ");
      var status = entry.status || "missing";
      var fileName = docId ? "Document " + docId : "Not uploaded";
      if (primaryDoc && slotId === "primary_output") {
        fileName = primaryDoc.fileName || primaryDoc.title || fileName;
      }
      return {
        slotId: slotId,
        label: label,
        status: status,
        documentId: docId,
        fileName: fileName,
        previewUrl: docId && primaryDoc && docId === primaryDoc.id ? primaryDoc.fileUrl : null
      };
    });
  },

  humanizeBlocker: function (text) {
    var map = {
      "Title of the research output is required.": "Article title is missing.",
      "Journal or publication venue is required.": "Journal name is missing.",
      "Author line is required.": "Author names are missing.",
      "Publication date is required.": "Publication date is missing.",
      "Declared contribution percentage (1–100) is required for co-authored outputs.":
        "Contribution percentage is missing for co-author claim.",
      "Verify all required evidence and resolve blockers before approving.":
        "Verify every document and resolve missing items before approving."
    };
    return map[text] || text;
  },

  formatSubmittedDate: function (row) {
    var raw = (row && (row.submittedAt || row.submittedForReviewAt)) || "";
    if (!raw) return "—";
    try {
      var d = new Date(raw);
      if (isNaN(d.getTime())) return String(raw).slice(0, 10);
      return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
    } catch (_e) {
      return String(raw).slice(0, 10);
    }
  },

  kra2SummaryLineHtml: function (summary) {
    var validated = summary && summary.validatedPoints != null ? summary.validatedPoints : 0;
    var max = summary && summary.maxPoints != null ? summary.maxPoints : 100;
    return "Verified " + String(validated) + " / " + String(max) + " pts (criterion cap)";
  },

  accomplishmentListHtml: function (params) {
    var esc = FL.esc;
    var rows = params.rows || [];
    var facultyName = params.personName || "Faculty";
    var list = rows.length
      ? rows
          .map(function (row) {
            var meta = FL.kra2AWorkspaceUi.facultyStatusMeta({
              reviewStatus: row.reviewStatus,
              submittedForReviewAt: row.submittedForReviewAt || row.submittedAt
            });
            var est = row.estimatedPoints != null ? row.estimatedPoints : "—";
            var assessed =
              row.reviewerAssessedPoints != null ? row.reviewerAssessedPoints : "—";
            var title = row.outputTitle || row.title || "Accomplishment";
            var submitted = FL.kra2AWorkspaceUi.formatSubmittedDate(row);
            var href = params.reviewHref(row);
            return (
              '<article class="evidence-accomplishment-card">' +
              '<div class="evidence-accomplishment-head">' +
              "<h3>" +
              esc(title) +
              "</h3>" +
              '<span class="badge badge--' +
              esc(meta.key) +
              '">' +
              esc(meta.label) +
              "</span></div>" +
              '<dl class="kv-grid kv-grid--compact evidence-accomplishment-meta">' +
              FL.documents.kvRow("Faculty", esc(facultyName)) +
              FL.documents.kvRow("Submitted", esc(submitted)) +
              FL.documents.kvRow("Estimated points", esc(String(est))) +
              FL.documents.kvRow("Reviewer-assessed", esc(String(assessed))) +
              "</dl>" +
              '<p class="evidence-accomplishment-actions">' +
              '<a class="btn btn-primary btn-small" href="' +
              esc(href) +
              '">Open Review</a></p></article>'
            );
          })
          .join("")
      : '<p class="muted">No accomplishments submitted yet.</p>';
    return (
      '<div class="kra2-a-workspace">' +
      '<h2 class="evidence-section-title">' +
      esc(params.criterionTitle || "Criterion A — Research Outputs") +
      "</h2>" +
      '<p class="muted" data-kra2-summary-slot>' +
      esc(facultyName) +
      " · " +
      esc(FL.kra2AWorkspaceUi.kra2SummaryLineHtml(params.summary || {})) +
      "</p>" +
      '<div class="evidence-accomplishment-cards">' +
      list +
      "</div></div>"
    );
  },

  scoringRuleLine: function (scoring, doc) {
    var ind = (scoring && scoring.indicatorId) || (doc && doc.indicatorId) || "";
    var label = FL.kra2AWorkspaceUi.indicatorLabel(ind);
    var eligible = scoring && scoring.eligiblePoints;
    if (eligible != null) {
      return label + " · official indicator maximum " + eligible + " pts";
    }
    return label;
  },

  ocrExtractionHtml: function (payload) {
    var esc = FL.esc;
    var extraction = (payload && payload.ocrExtraction) || {};
    var fields = extraction.fields || {};
    var keys = Object.keys(fields);
    if (!keys.length) {
      return '<p class="muted">No structured OCR metadata is available for this file yet.</p>';
    }
    var rows = keys
      .map(function (key) {
        var block = fields[key] || {};
        var val = (block.value || "").trim();
        if (!val) return "";
        var label = key.replace(/([A-Z])/g, " $1").replace(/^./, function (c) {
          return c.toUpperCase();
        });
        return FL.documents.kvRow(label, esc(val));
      })
      .filter(Boolean)
      .join("");
    return rows
      ? '<dl class="kv-grid kv-grid--compact kra2-ocr-grid">' + rows + "</dl>"
      : '<p class="muted">OCR did not extract readable metadata.</p>';
  },

  compactReviewPageHtml: function (state) {
    var esc = FL.esc;
    var bundle = state.bundle || {};
    var doc = state.doc || {};
    var scoring = state.scoring || {};
    var indLabel = FL.kra2AWorkspaceUi.indicatorLabel(doc.indicatorId);
    var confirmed = bundle.metadataConfirmed || {};
    var userBlockers = (state.validation && state.validation.userBlockers) || [];
    var confirmNote = "Confirmed metadata is shown below. OCR suggestions in Supporting documents are advisory only.";
    if (userBlockers.length) {
      confirmNote =
        "Some required metadata is missing or unconfirmed: " + userBlockers.slice(0, 3).join(" ");
    } else if (bundle.submittedForReviewAt && confirmed) {
      confirmNote = "Faculty confirmed metadata at submission.";
    }
    var details =
      '<section class="card cc-compact-section kra2-section-details">' +
      "<h2>Accomplishment details</h2>" +
      '<p class="muted kra2-section-lede">' +
      esc(confirmNote) +
      "</p>" +
      '<dl class="kv-grid kv-grid--compact">' +
      FL.documents.kvRow("Title", esc(bundle.outputTitle || doc.title || "—")) +
      FL.documents.kvRow("Faculty", esc(state.facultyName || "—")) +
      FL.documents.kvRow("Accomplishment type", esc(indLabel)) +
      FL.documents.kvRow("Venue / registry", esc(bundle.outputVenue || bundle.journalTitle || "—")) +
      FL.documents.kvRow("Authors / inventors", esc(bundle.authorsLine || "—")) +
      FL.documents.kvRow("Date", esc(bundle.publicationDate || bundle.registrationDate || "—")) +
      (bundle.registrationNumber
        ? FL.documents.kvRow("Registration no.", esc(bundle.registrationNumber))
        : "") +
      (bundle.citationContext ? FL.documents.kvRow("Citation context", esc(bundle.citationContext)) : "") +
      FL.documents.kvRow("Reference (DOI/ISBN/etc.)", esc(bundle.publicationReference || "—")) +
      (bundle.contribution === "declared"
        ? FL.documents.kvRow("Declared contribution", esc(String(bundle.declaredContributionPercent || "—")) + "%")
        : "") +
      FL.documents.kvRow("Official scoring rule", esc(FL.kra2AWorkspaceUi.scoringRuleLine(scoring, doc))) +
      "</dl></section>";

    var docsHtml = FL.kra2AWorkspaceUi.evidenceCardsHtml(state);
    var previewHtml =
      '<section class="card cc-compact-section kra2-section-documents">' +
      "<h2>Supporting documents</h2>" +
      '<h3 class="kra2-subheading">Document preview</h3>' +
      '<div class="original-file-frame" data-doc-preview-id="' +
      esc(doc.id || "") +
      '"></div>' +
      '<h3 class="kra2-subheading">OCR-extracted details (advisory)</h3>' +
      FL.kra2AWorkspaceUi.ocrExtractionHtml(state.payload || {}) +
      docsHtml +
      "</section>";
    var decisionHtml = FL.kra2AWorkspaceUi.decisionSectionHtml(state);

    return (
      '<div class="portal-page cb-simple-review cc-compact-review kra2-a-review">' +
      (state.chromeHtml || "") +
      '<header class="card cb-simple-head cc-compact-head">' +
      '<a class="btn btn-ghost btn-small" href="' +
      esc(state.backHref) +
      '">' +
      esc(state.backLabel) +
      "</a>" +
      "<h1>KRA II accomplishment review</h1>" +
      '<p class="sub">' +
      esc(state.facultyName || "Faculty") +
      " · " +
      esc(indLabel) +
      "</p></header>" +
      details +
      FL.kra2AWorkspaceUi.reviewerMetadataPanelHtml(state) +
      previewHtml +
      decisionHtml +
      "</div>"
    );
  },

  ocrFieldValue: function (payload, fieldId) {
    var extraction = (payload && payload.ocrExtraction) || {};
    var fields = extraction.fields || {};
    var block = fields[fieldId];
    if (block && block.value) return String(block.value).trim();
    if (fieldId === "outputVenue" && fields.journalTitle && fields.journalTitle.value) {
      return String(fields.journalTitle.value).trim();
    }
    return "";
  },

  workflowFamily: function (indicatorId) {
    var iid = (indicatorId || "").trim();
    var parts = iid.split("-");
    var familyToken = parts.length >= 3 ? parts[2] : "";
    var crit = parts.length >= 2 ? parts[0] + "-" + parts[1] : "";
    if (familyToken === "cite") return "citation_impact";
    if (crit === "kra2-b") {
      if (familyToken.indexOf("comm") === 0) return "commercialization";
      return "invention_ip";
    }
    if (crit === "kra2-c") {
      if (familyToken.indexOf("perf") >= 0 || iid.indexOf("-perf") >= 0) return "performance_work";
      return "creative_work";
    }
    return "publication_output";
  },

  metadataFormFields: function (indicatorId) {
    var family = FL.kra2AWorkspaceUi.workflowFamily(indicatorId);
    var fields = [
      { id: "outputTitle", inputId: "kra2-meta-outputTitle", label: "Title", required: true },
      { id: "authorsLine", inputId: "kra2-meta-authorsLine", label: "Authors / inventors", required: true }
    ];
    if (family === "citation_impact") {
      fields.push({
        id: "citationContext",
        inputId: "kra2-meta-citationContext",
        label: "Citation context",
        required: true
      });
      fields.push({
        id: "publicationDate",
        inputId: "kra2-meta-publicationDate",
        label: "Publication or registration date",
        required: true
      });
      return fields;
    }
    if (family === "invention_ip") {
      fields.push({
        id: "registrationNumber",
        inputId: "kra2-meta-registrationNumber",
        label: "Patent / registration number",
        required: true
      });
      fields.push({
        id: "registrationDate",
        inputId: "kra2-meta-registrationDate",
        label: "Publication or registration date",
        required: true
      });
      return fields;
    }
    if (family === "commercialization") {
      fields.push({
        id: "outputVenue",
        inputId: "kra2-meta-outputVenue",
        label: "Venue / registry",
        required: true
      });
      fields.push({
        id: "publicationDate",
        inputId: "kra2-meta-publicationDate",
        label: "Publication or registration date",
        required: true
      });
      return fields;
    }
    fields.push({
      id: "outputVenue",
      inputId: "kra2-meta-outputVenue",
      label: "Venue / registry",
      required: true
    });
    fields.push({
      id: "publicationDate",
      inputId: "kra2-meta-publicationDate",
      label: "Publication or registration date",
      required: true
    });
    fields.push({
      id: "publicationReference",
      inputId: "kra2-meta-publicationReference",
      label: "DOI / reference",
      required: false
    });
    return fields;
  },

  applyOcrSuggestions: function (state, options) {
    options = options || {};
    var onlyEmpty = options.onlyEmpty !== false;
    var payload = state.payload || {};
    var indicatorId =
      (state.bundle && state.bundle.indicatorId) || (state.doc && state.doc.indicatorId) || "";
    var fields = FL.kra2AWorkspaceUi.metadataFormFields(indicatorId);
    var filled = [];
    fields.forEach(function (f) {
      var el = document.getElementById(f.inputId);
      if (!el) return;
      var ocrVal = FL.kra2AWorkspaceUi.ocrFieldValue(payload, f.id);
      if (!ocrVal) return;
      if (onlyEmpty && (el.value || "").trim()) return;
      el.value = ocrVal;
      filled.push(f.label || f.id);
    });
    if (filled.length) {
      return { filled: filled, message: "" };
    }
    var anyOcr = fields.some(function (f) {
      return !!FL.kra2AWorkspaceUi.ocrFieldValue(payload, f.id);
    });
    return {
      filled: [],
      message: anyOcr
        ? "All applicable fields already have values. Clear a field to apply OCR again."
        : "We couldn't find enough information in this document."
    };
  },

  collectReviewerMetadataBody: function (state) {
    var indicatorId =
      (state.bundle && state.bundle.indicatorId) || (state.doc && state.doc.indicatorId) || "";
    var fields = FL.kra2AWorkspaceUi.metadataFormFields(indicatorId);
    var body = {};
    fields.forEach(function (f) {
      var el = document.getElementById(f.inputId);
      if (!el) return;
      body[f.id] = (el.value || "").trim();
    });
    if (body.outputVenue) {
      body.journalTitle = body.outputVenue;
    }
    return body;
  },

  validateReviewerMetadata: function (state) {
    var indicatorId =
      (state.bundle && state.bundle.indicatorId) || (state.doc && state.doc.indicatorId) || "";
    var fields = FL.kra2AWorkspaceUi.metadataFormFields(indicatorId);
    var missing = [];
    fields.forEach(function (f) {
      if (!f.required) return;
      var el = document.getElementById(f.inputId);
      var val = el ? (el.value || "").trim() : "";
      if (!val) missing.push(f.label || f.id);
    });
    var body = FL.kra2AWorkspaceUi.collectReviewerMetadataBody(state);
    if (missing.length) {
      return {
        ok: false,
        message: "Please complete: " + missing.join(", ") + ".",
        body: body
      };
    }
    return { ok: true, message: "", body: body };
  },

  metadataPanelNeeded: function (state) {
    var v = state.validation || {};
    var flags = v.flags || [];
    if (flags.indexOf("metadata_not_confirmed") >= 0) return true;
    return FL.kra2AWorkspaceUi.mergeValidationMessages(v).some(function (b) {
      var t = (b || "").toLowerCase();
      return (
        t.indexOf("title") >= 0 ||
        t.indexOf("author") >= 0 ||
        t.indexOf("journal") >= 0 ||
        t.indexOf("venue") >= 0 ||
        t.indexOf("date") >= 0 ||
        t.indexOf("metadata") >= 0 ||
        t.indexOf("confirm") >= 0 ||
        t.indexOf("registration") >= 0
      );
    });
  },

  mergeValidationMessages: function (validation) {
    var v = validation || {};
    var out = [];
    var seen = {};
    function push(msg) {
      var m = (msg || "").trim();
      if (!m || seen[m]) return;
      seen[m] = true;
      out.push(m);
    }
    if (Array.isArray(v.approvalBlockers) && v.approvalBlockers.length) {
      v.approvalBlockers.forEach(push);
      return out;
    }
    (v.blockers || []).forEach(push);
    (v.userBlockers || []).forEach(push);
    return out;
  },

  computeApprovalBlockers: function (state, remarksText) {
    var v = state.validation || {};
    var items = [];
    var seen = {};
    function add(msg) {
      var m = (msg || "").trim();
      if (!m || seen[m]) return;
      seen[m] = true;
      items.push(m);
    }
    FL.kra2AWorkspaceUi.mergeValidationMessages(v).forEach(add);
    var summary = v.checklistSummary || {};
    Object.keys(summary).forEach(function (slot) {
      if (summary[slot] !== "verified") {
        add("Verify supporting evidence: " + slot.replace(/_/g, " ") + ".");
      }
    });
    var remarksLen = ((remarksText != null ? remarksText : state.remarks) || "").trim().length;
    if (remarksLen < 10) {
      add("Enter reviewer remarks (at least 10 characters).");
    }
    if (state.verificationSave && state.verificationSave.pending) {
      add("Wait for evidence verification to finish saving.");
    }
    if (!state.canDecide) {
      add("You do not have permission to approve this accomplishment.");
    }
    return items;
  },

  buildApprovalDiagnostics: function (state, remarksText) {
    var v = state.validation || {};
    var remarksLen = ((remarksText != null ? remarksText : state.remarks) || "").trim().length;
    return {
      canDecide: !!state.canDecide,
      verificationSavePending: !!(state.verificationSave && state.verificationSave.pending),
      validationStatus: v.validationStatus,
      reviewStatus: v.reviewStatus,
      flags: v.flags || [],
      blockers: v.blockers || [],
      userBlockers: v.userBlockers || [],
      approvalBlockers: v.approvalBlockers || [],
      checklistSummary: v.checklistSummary || {},
      metadataConfirmed: (state.bundle && state.bundle.metadataConfirmed) || {},
      readyForApproval: v.readyForApproval,
      remarksLength: remarksLen,
      computedBlockers: FL.kra2AWorkspaceUi.computeApprovalBlockers(state, remarksText)
    };
  },

  logApprovalDiagnostics: function (state, remarksText) {
    var debug =
      (typeof window !== "undefined" &&
        window.location &&
        window.location.search &&
        window.location.search.indexOf("kra2debug=1") >= 0) ||
      (typeof window !== "undefined" && window.FL && window.FL.kra2DebugApproval);
    if (!debug) return;
    console.log("[KRA II approve]", FL.kra2AWorkspaceUi.buildApprovalDiagnostics(state, remarksText));
  },

  approvalChecklistHtml: function (state, remarksText) {
    var esc = FL.esc;
    var items = FL.kra2AWorkspaceUi.computeApprovalBlockers(state, remarksText);
    var ready = items.length === 0;
    var rows = items.length
      ? items.map(function (b) {
          return '<li class="kra2-checklist-blocker">' + esc(b) + "</li>";
        }).join("")
      : '<li class="kra2-checklist-ok">All approval requirements are satisfied.</li>';
    return (
      '<div class="kra2-approval-checklist' +
      (ready ? " is-ready" : "") +
      '" id="kra2-approval-checklist">' +
      "<h3 class=\"kra2-subheading\">Why can't I approve this?</h3>" +
      '<p class="muted kra2-test-notice">Fictional test PDF — confirm metadata explicitly; OCR is advisory only.</p>' +
      '<ul class="cc-blocker-list">' +
      rows +
      "</ul></div>"
    );
  },

  reviewerMetadataPanelHtml: function (state) {
    var esc = FL.esc;
    if (!state.canDecide || !FL.kra2AWorkspaceUi.metadataPanelNeeded(state)) return "";
    var bundle = state.bundle || {};
    var payload = state.payload || {};
    var indicatorId = bundle.indicatorId || (state.doc && state.doc.indicatorId) || "";
    function fieldVal(key, bundleKey) {
      var fromBundle = (bundle[bundleKey || key] || "").toString().trim();
      if (fromBundle) return fromBundle;
      if (key === "outputVenue") {
        fromBundle = (bundle.journalTitle || "").toString().trim();
        if (fromBundle) return fromBundle;
      }
      return "";
    }
    var formFields = FL.kra2AWorkspaceUi.metadataFormFields(indicatorId);
    var inputsHtml = formFields
      .map(function (f) {
        var optional = f.required ? "" : " (optional)";
        return (
          "<label>" +
          esc(f.label + optional) +
          '<input type="text" id="' +
          esc(f.inputId) +
          '" value="' +
          esc(fieldVal(f.id)) +
          '"></label>'
        );
      })
      .join("");
    return (
      '<section class="card cc-compact-section kra2-metadata-edit">' +
      "<h2>Confirm accomplishment metadata</h2>" +
      '<p class="muted">Copy OCR suggestions if helpful, then save to confirm. Confirmed values are stored separately from advisory OCR.</p>' +
      '<div class="kra2-metadata-fields">' +
      inputsHtml +
      "</div>" +
      '<div class="kra2-metadata-actions">' +
      '<button type="button" class="btn btn-ghost btn-small" id="kra2-fill-ocr" data-kra2-action="fill-ocr">Use OCR suggestions</button>' +
      '<button type="button" class="btn btn-primary btn-small" id="kra2-save-metadata" data-kra2-action="save-metadata">Save confirmed metadata</button>' +
      '<span class="cc-save-indicator" id="kra2-fill-ocr-indicator" aria-live="polite"></span>' +
      '<span class="cc-save-indicator" id="kra2-save-metadata-indicator" aria-live="polite"></span></div></section>'
    );
  },

  evidenceCardsHtml: function (state) {
    var esc = FL.esc;
    var canDecide = !!state.canDecide;
    var items = state.evidenceItems || [];
    var cards = items
      .map(function (item, idx) {
        var statusLabel =
          item.status === "verified"
            ? "Verified"
            : item.status === "missing"
              ? "Missing"
              : "Pending verification";
        var previewBtn = item.documentId
          ? '<button type="button" class="btn btn-small btn-ghost" data-kra2-scroll-preview="' +
            esc(item.documentId) +
            '">Preview</button>'
          : "";
        var verifyCtrl = "";
        if (canDecide && item.documentId) {
          verifyCtrl =
            '<label class="cc-slot-verify-label">Verification ' +
            '<select class="kra2-slot-status" data-slot="' +
            esc(item.slotId) +
            '" id="kra2-slot-' +
            esc(item.slotId) +
            '">' +
            '<option value="present_unverified"' +
            (item.status === "present_unverified" ? " selected" : "") +
            ">Pending</option>" +
            '<option value="verified"' +
            (item.status === "verified" ? " selected" : "") +
            ">Verified</option>" +
            '<option value="reviewer_required"' +
            (item.status === "reviewer_required" ? " selected" : "") +
            ">Needs clarification</option>" +
            "</select></label>" +
            '<span class="cc-save-indicator" id="kra2-save-' +
            esc(item.slotId) +
            '"></span>';
        }
        return (
          '<article class="card cc-evidence-card">' +
          "<h3>" +
          esc(item.label) +
          "</h3>" +
          '<p class="muted">' +
          esc(item.fileName) +
          " · " +
          esc(statusLabel) +
          "</p>" +
          '<div class="cc-evidence-card-actions">' +
          previewBtn +
          verifyCtrl +
          "</div></article>"
        );
      })
      .join("");
    return '<div class="kra2-evidence-checklist"><h3 class="kra2-subheading">Evidence verification</h3>' + cards + "</div>";
  },

  decisionSectionHtml: function (state) {
    var esc = FL.esc;
    var validation = state.validation || {};
    var scoring = state.scoring || {};
    var systemPts =
      scoring.systemCalculatedPoints != null
        ? scoring.systemCalculatedPoints
        : scoring.estimatedPoints;
    var assessed = scoring.reviewerAssessedPoints;
    var method = scoring.scoringMethod || (scoring.allowsContributionEdit ? "contribution_based" : "fixed");
    var methodLabel = scoring.scoringMethodLabel || (method === "contribution_based" ? "Contribution-Based" : "Fixed");
    var allowsAdjust = !!scoring.allowsPointAdjustment;
    var allowsContribution = !!scoring.allowsContributionEdit || method === "contribution_based";
    var bundle = state.bundle || {};
    var finalPts = assessed != null ? assessed : systemPts;
    var canDecide = !!state.canDecide;
    var checklistHtml = FL.kra2AWorkspaceUi.approvalChecklistHtml(state, "");

    var assessedField = "";
    var methodHelp = "";
    var indicatorMax = scoring.indicatorMaxPoints != null ? scoring.indicatorMaxPoints : scoring.eligiblePoints;
    var assessableMax = scoring.maxAssessedPoints != null ? scoring.maxAssessedPoints : systemPts;

    if (method === "contribution_based") {
      methodHelp =
        "Use verified contribution % to recalculate eligible points. You may also reduce assessed points when indexing/eligibility rules require it.";
    } else if (allowsAdjust || method === "variable") {
      methodHelp =
        "System-calculated points assume full eligibility. You may assess a lower score (for example 30 of 50) when official indexing or eligibility rules require it. Scores cannot exceed the system-calculated eligible amount or the published indicator maximum.";
    } else {
      methodHelp =
        "Official fixed points for this indicator. Confirm eligibility or reject; arbitrary partial scores are not permitted.";
    }

    if (canDecide) {
      if (allowsContribution) {
        assessedField =
          '<label class="kra2-scoring-label" for="kra2-contribution-percent">Verified contribution (%)' +
          '<input type="number" id="kra2-contribution-percent" class="kra2-scoring-input" min="1" max="100" step="0.01" value="' +
          esc(String(bundle.declaredContributionPercent != null ? bundle.declaredContributionPercent : "")) +
          '"></label>' +
          '<button type="button" class="btn btn-ghost btn-small" id="kra2-recalc-contribution">Recalculate points</button>' +
          '<span class="cc-save-indicator" id="kra2-save-contribution-indicator"></span>';
      }
      if (allowsAdjust) {
        assessedField +=
          '<label class="kra2-scoring-label" for="kra2-assessed-points">Reviewer-assessed points' +
          (indicatorMax != null
            ? ' <span class="muted">(max ' + esc(String(assessableMax)) + " of " + esc(String(indicatorMax)) + " official)</span>"
            : "") +
          '<input type="number" id="kra2-assessed-points" class="kra2-scoring-input" min="0" max="' +
          esc(assessableMax != null ? String(assessableMax) : "") +
          '" step="0.01" value="' +
          esc(finalPts != null ? String(finalPts) : "") +
          '"></label>' +
          '<label class="kra2-scoring-label kra2-adjustment-reason" for="kra2-score-adjustment-reason">' +
          "Reason for score adjustment (required when assessed differs from system-calculated)" +
          '<textarea id="kra2-score-adjustment-reason" rows="2" class="kra2-scoring-textarea">' +
          esc((scoring.scoreAdjustmentReason || "").toString()) +
          "</textarea></label>";
      } else {
        assessedField +=
          '<div class="kra2-scoring-readonly">' +
          "<span>Reviewer-assessed points (on approval)</span>" +
          "<strong>" +
          esc(systemPts != null ? String(systemPts) : "—") +
          "</strong></div>" +
          '<input type="hidden" id="kra2-assessed-points" value="' +
          esc(systemPts != null ? String(systemPts) : "") +
          '">';
      }
    }

    return (
      '<section class="card cc-compact-section cc-decision-section kra2-complete-review">' +
      "<h2>Complete review</h2>" +
      checklistHtml +
      '<div class="kra2-scoring-panel">' +
      "<h3 class=\"kra2-subheading\">Scoring</h3>" +
      '<p class="muted kra2-scoring-method">Scoring method: <strong>' +
      esc(methodLabel) +
      "</strong></p>" +
      '<p class="muted kra2-scoring-method-help">' +
      esc(methodHelp) +
      "</p>" +
      '<div class="kra2-scoring-row">' +
      "<span>Official scoring rule</span>" +
      "<span class=\"kra2-scoring-rule\">" +
      esc(FL.kra2AWorkspaceUi.scoringRuleLine(scoring, state.doc || {})) +
      "</span></div>" +
      '<div class="kra2-scoring-row kra2-scoring-row--highlight">' +
      "<span>System-calculated eligible points</span>" +
      "<strong class=\"kra2-system-points\" id=\"kra2-system-points-display\">" +
      esc(systemPts != null ? String(systemPts) : "—") +
      "</strong></div>" +
      '<div class="kra2-scoring-row">' +
      "<span>Final reviewer-assessed points (on approval)</span>" +
      "<strong class=\"kra2-final-points\" id=\"kra2-final-points-display\">" +
      esc(finalPts != null ? String(finalPts) : "—") +
      "</strong></div>" +
      assessedField +
      "</div>" +
      (canDecide
        ? '<label class="kra2-remarks-label" for="kra2-remarks">Reviewer remarks (workflow notes; not a score)' +
          '<textarea id="kra2-remarks" rows="4" class="kra2-remarks-input">' +
          esc(state.remarks || "") +
          "</textarea></label>" +
          '<div class="cc-decision-actions kra2-decision-actions">' +
          '<button type="button" class="btn btn-primary" id="kra2-approve"' +
          (!canDecide ? " disabled" : "") +
          ">Approve</button>" +
          '<p class="muted kra2-approve-hint" id="kra2-approve-hint"></p>' +
          '<button type="button" class="btn btn-ghost" id="kra2-reject">Reject</button>' +
          "</div>"
        : "") +
      "</section>"
    );
  },

  slotSaveIndicatorMessage: function (phase) {
    if (phase === "saving") return "Saving…";
    if (phase === "error") return "Could not save — try again.";
    if (phase === "saved") return "Saved";
    return "";
  }
};
