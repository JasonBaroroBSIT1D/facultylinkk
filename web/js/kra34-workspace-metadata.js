/**
 * KRA III (Extension) & KRA IV (Professional Development) — indicator metadata UI.
 * Uses API metadataFields when present; falls back to workflow-family field lists.
 */
window.FL = window.FL || {};

FL.kra34Metadata = {
  isKra34Indicator: function (indicatorId) {
    var iid = (indicatorId || "").trim();
    return iid.indexOf("kra3-") === 0 || iid.indexOf("kra4-") === 0;
  },

  /** @returns {{id:string,label:string,required:boolean}[]} */
  formFields: function (indicatorId, payload) {
    var iid = (indicatorId || "").trim();
    if (!FL.kra34Metadata.isKra34Indicator(iid)) return [];
    var fromApi = payload && payload.metadataFields;
    if (Array.isArray(fromApi) && fromApi.length) {
      return fromApi.map(function (row) {
        return {
          id: row.id,
          inputId: "kra34-meta-" + row.id,
          label: row.label || row.id,
          required: row.required !== false
        };
      });
    }
    return FL.kra34Metadata._fallbackFields(iid);
  },

  _fallbackFields: function (indicatorId) {
    var fam = FL.kra34Metadata._workflowFamily(indicatorId);
    var ids = FL.kra34Metadata._familyFieldIds(indicatorId, fam);
    return ids.map(function (id) {
      return {
        id: id,
        inputId: "kra34-meta-" + id,
        label: FL.kra34Metadata._fieldLabel(id, indicatorId),
        required: true
      };
    });
  },

  _workflowFamily: function (indicatorId) {
    var iid = (indicatorId || "").trim();
    if (iid.indexOf("kra4-") === 0) {
      if (iid.indexOf("kra4-a-") === 0) return "organization";
      if (iid.indexOf("kra4-b-post") === 0 || iid === "kra4-b-doctorate" || iid.indexOf("kra4-b-master") === 0)
        return "education";
      if (iid.indexOf("kra4-b-part") === 0) return "capacity_building";
      if (iid.indexOf("kra4-b-paper") === 0) return "paper_presentation";
      if (iid.indexOf("kra4-c-") === 0) return "award";
      if (iid.indexOf("kra4-d-") === 0) return "prior_experience";
      return "generic";
    }
    if (iid.indexOf("kra3-a-link") === 0) return "linkage";
    if (iid.indexOf("kra3-a-inc") === 0) return "income";
    if (iid.indexOf("kra3-a-acc") === 0) return "accreditation";
    if (iid.indexOf("kra3-a-jud") === 0) return "judging";
    if (iid.indexOf("kra3-a-cons") === 0) return "consultancy";
    if (iid.indexOf("kra3-b-col") === 0) return "media_column";
    if (iid.indexOf("kra3-b-host") === 0) return "media_host";
    if (iid.indexOf("kra3-b-guest") === 0) return "media_guest";
    if (iid.indexOf("kra3-b-res") === 0) return "resource_person";
    if (iid.indexOf("kra3-c-") === 0) return "extension_project";
    if (iid.indexOf("kra3-d-csr") === 0) return "csr";
    if (iid.indexOf("kra3-d-des") === 0) return "designation";
    return "generic_service";
  },

  _familyFieldIds: function (indicatorId, fam) {
    var kra4 = {
      organization: ["activityTitle", "organizationName", "facultyRole", "serviceStartDate", "serviceEndDate"],
      education: ["degreeTitle", "institutionName", "activityDate"],
      capacity_building: [
        "eventTitle",
        "organizationName",
        "eventDurationHours",
        "eventScope",
        "activityDate",
        "approvalReference"
      ],
      paper_presentation: [
        "paperTitle",
        "eventTitle",
        "organizationName",
        "eventScope",
        "activityDate",
        "approvalReference"
      ],
      award: ["awardTitle", "awardLevel", "organizationName", "activityDate"],
      prior_experience: ["employerName", "positionTitle", "serviceStartDate", "serviceEndDate", "experienceYears"],
      generic: ["activityTitle", "organizationName", "activityDate"]
    };
    var kra3 = {
      linkage: ["activityTitle", "organizationName", "facultyRole", "activityDate", "approvalReference"],
      income: ["activityTitle", "organizationName", "facultyRole", "grossIncomeAmount", "activityDate"],
      accreditation: ["activityTitle", "organizationName", "facultyRole", "serviceStartDate", "serviceEndDate"],
      judging: ["activityTitle", "organizationName", "facultyRole", "activityDate"],
      consultancy: ["activityTitle", "organizationName", "facultyRole", "serviceStartDate", "serviceEndDate"],
      media_column: ["activityTitle", "organizationName", "activityDate"],
      media_host: ["activityTitle", "organizationName", "serviceStartDate", "serviceEndDate", "serviceDurationMonths"],
      media_guest: ["activityTitle", "organizationName", "activityDate"],
      resource_person: ["activityTitle", "organizationName", "facultyRole", "activityDate", "deliveryHours"],
      extension_project: ["activityTitle", "organizationName", "facultyRole", "serviceStartDate", "serviceEndDate"],
      csr: ["activityTitle", "csrOverallRating", "linkedExtensionProjectId"],
      designation: ["designationTitle", "approvalReference", "serviceStartDate", "serviceEndDate", "serviceDurationMonths"],
      generic_service: ["activityTitle", "organizationName", "facultyRole", "activityDate"]
    };
    if ((indicatorId || "").indexOf("kra4-") === 0) {
      return kra4[fam] || kra4.generic;
    }
    return kra3[fam] || kra3.generic_service;
  },

  _fieldLabel: function (fieldId, indicatorId) {
    var labels = FL.kra34Metadata._LABELS;
    if (labels[fieldId]) return labels[fieldId];
    return fieldId.replace(/([A-Z])/g, " $1").replace(/^./, function (c) {
      return c.toUpperCase();
    });
  },

  _LABELS: {
    activityTitle: "Activity or project title",
    organizationName: "Organization / partner",
    facultyRole: "Faculty role or participation",
    activityDate: "Date completed or awarded",
    serviceStartDate: "Start date",
    serviceEndDate: "End date",
    institutionName: "Institution",
    degreeTitle: "Degree or qualification",
    eventTitle: "Training or event title",
    eventDurationHours: "Duration (hours)",
    eventScope: "Local or international",
    paperTitle: "Paper title",
    awardTitle: "Award title",
    awardLevel: "Recognition level",
    employerName: "Employer / institution",
    positionTitle: "Position / designation",
    experienceYears: "Qualifying years",
    approvalReference: "Approval / reference",
    grossIncomeAmount: "Gross income (₱)",
    deliveryHours: "Eligible service hours",
    csrOverallRating: "Overall satisfaction rating",
    linkedExtensionProjectId: "Linked extension project",
    designationTitle: "Administrative designation",
    serviceDurationMonths: "Months of service"
  },

  bundleFieldValue: function (bundle, fieldId) {
    var b = bundle || {};
    if (fieldId === "activityTitle") {
      return (b.activityTitle || b.outputTitle || "").toString().trim();
    }
    var raw = b[fieldId];
    if (raw == null || raw === "") return "";
    return String(raw).trim();
  },

  ocrHints: function (payload) {
    var p = payload || {};
    var ext = p.ocrExtraction || p.kra4OcrExtraction || p.kra3OcrExtraction || {};
    if (ext && ext.hints && typeof ext.hints === "object") return ext.hints;
    if (ext && ext.fields && typeof ext.fields === "object") {
      var out = {};
      Object.keys(ext.fields).forEach(function (k) {
        var block = ext.fields[k];
        if (block && block.value) out[k] = String(block.value).trim();
      });
      return out;
    }
    return {};
  },

  ocrFieldValue: function (payload, fieldId) {
    var hints = FL.kra34Metadata.ocrHints(payload);
    return hints[fieldId] || "";
  },

  ocrStatusLabel: function (payload, doc) {
    var st =
      (payload && payload.ocrStatus) ||
      (doc && doc.ocr && doc.ocr.status) ||
      (doc && doc.ocrStatus) ||
      "pending";
    st = String(st || "pending").toLowerCase();
    if (st === "completed") return "Completed";
    if (st === "failed") return "Failed";
    if (st === "processing" || st === "running") return "Processing";
    return "Pending";
  },

  accomplishmentDetailsHtml: function (state) {
    var esc = FL.esc;
    var bundle = state.bundle || {};
    var doc = state.doc || {};
    var scoring = state.scoring || {};
    var indicatorId =
      bundle.indicatorId || (state.doc && state.doc.indicatorId) || "";
    var indLabel =
      FL.kra2AWorkspaceUi && FL.kra2AWorkspaceUi.indicatorLabel
        ? FL.kra2AWorkspaceUi.indicatorLabel(indicatorId, bundle)
        : indicatorId;
    var fields = FL.kra34Metadata.formFields(indicatorId, state.payload);
    var rows = fields
      .map(function (f) {
        var val = FL.kra34Metadata.bundleFieldValue(bundle, f.id);
        return FL.documents.kvRow(f.label, esc(val || "—"));
      })
      .join("");
    var scoringLine =
      FL.kra2AWorkspaceUi && FL.kra2AWorkspaceUi.scoringRuleLine
        ? FL.kra2AWorkspaceUi.scoringRuleLine(scoring, doc, bundle)
        : "—";
    return (
      '<section class="card cc-compact-section kra34-section-details">' +
      "<h2>Accomplishment details</h2>" +
      '<p class="muted kra2-section-lede">Information stored for this indicator. OCR suggestions appear below; corrections are optional until you approve.</p>' +
      '<dl class="kv-grid kv-grid--compact">' +
      FL.documents.kvRow("Document title", esc(doc.title || bundle.outputTitle || "—")) +
      FL.documents.kvRow("Faculty", esc(state.facultyName || "—")) +
      FL.documents.kvRow("Accomplishment type", esc(indLabel)) +
      rows +
      FL.documents.kvRow("Official scoring rule", esc(scoringLine)) +
      "</dl></section>"
    );
  },

  extractedDocumentInfoHtml: function (state) {
    var esc = FL.esc;
    if (!state.canDecide || !FL.kra2AWorkspaceUi || FL.kra2AWorkspaceUi.isReviewDecisionLocked(state)) {
      return FL.kra34Metadata.extractedDocumentInfoReadOnlyHtml(state);
    }
    var bundle = state.bundle || {};
    var indicatorId = bundle.indicatorId || (state.doc && state.doc.indicatorId) || "";
    var fields = FL.kra34Metadata.formFields(indicatorId, state.payload);
    var hints = FL.kra34Metadata.ocrHints(state.payload || {});
    var ocrLabel = FL.kra34Metadata.ocrStatusLabel(state.payload, state.doc);
    var sourceName = (state.doc && (state.doc.fileName || state.doc.title)) || "Main document";

    var tableRows = fields
      .map(function (f) {
        var ocrVal = hints[f.id] || "";
        var current = FL.kra34Metadata.bundleFieldValue(bundle, f.id);
        var displayOcr = ocrVal ? esc(ocrVal) : '<span class="muted">Not detected</span>';
        return (
          "<tr>" +
          "<th scope=\"row\">" +
          esc(f.label) +
          "</th>" +
          "<td class=\"kra34-ocr-val\">" +
          displayOcr +
          "</td>" +
          "<td class=\"kra34-ocr-src muted\">" +
          esc(sourceName) +
          "</td>" +
          "<td class=\"kra34-ocr-st muted\">" +
          esc(ocrLabel) +
          "</td>" +
          "<td><input type=\"text\" class=\"kra34-meta-input\" id=\"" +
          esc(f.inputId) +
          "\" data-field-id=\"" +
          esc(f.id) +
          "\" value=\"" +
          esc(current) +
          "\" placeholder=\"Correction if needed\"></td>" +
          "</tr>"
        );
      })
      .join("");

    return (
      '<section class="card cc-compact-section kra34-extracted-info">' +
      "<h2>Extracted document information</h2>" +
      '<p class="muted">Advisory OCR only — does not approve points or replace evidence verification.</p>' +
      '<div class="table-wrap"><table class="data-table kra34-extracted-table">' +
      "<thead><tr><th>Field</th><th>OCR value</th><th>Source</th><th>OCR status</th><th>Reviewer correction</th></tr></thead>" +
      "<tbody>" +
      tableRows +
      "</tbody></table></div>" +
      '<div class="kra34-metadata-actions">' +
      '<button type="button" class="btn btn-ghost btn-small" id="kra34-fill-ocr" data-kra34-action="fill-ocr">Apply OCR to corrections</button>' +
      '<button type="button" class="btn btn-primary btn-small" id="kra34-save-metadata" data-kra34-action="save-metadata">Save corrections</button>' +
      '<span class="cc-save-indicator" id="kra34-save-metadata-indicator" aria-live="polite"></span>' +
      "</div></section>"
    );
  },

  extractedDocumentInfoReadOnlyHtml: function (state) {
    var esc = FL.esc;
    var bundle = state.bundle || {};
    var indicatorId = bundle.indicatorId || (state.doc && state.doc.indicatorId) || "";
    var fields = FL.kra34Metadata.formFields(indicatorId, state.payload);
    var hints = FL.kra34Metadata.ocrHints(state.payload || {});
    var rows = fields
      .map(function (f) {
        var ocrVal = hints[f.id] || "";
        var current = FL.kra34Metadata.bundleFieldValue(bundle, f.id);
        var show = current || ocrVal;
        if (!show) return "";
        return (
          FL.documents.kvRow(f.label, esc(current || ocrVal)) +
          (ocrVal && current && ocrVal !== current
            ? FL.documents.kvRow("OCR suggested", esc(ocrVal), false)
            : "")
        );
      })
      .filter(Boolean)
      .join("");
    if (!rows) {
      return (
        '<section class="card cc-compact-section kra34-extracted-info">' +
        "<h2>Extracted document information</h2>" +
        '<p class="muted">No structured OCR metadata yet.</p></section>'
      );
    }
    return (
      '<section class="card cc-compact-section kra34-extracted-info">' +
      "<h2>Extracted document information</h2>" +
      '<dl class="kv-grid kv-grid--compact">' +
      rows +
      "</dl></section>"
    );
  },

  collectCorrectionBody: function (state) {
    var indicatorId =
      (state.bundle && state.bundle.indicatorId) || (state.doc && state.doc.indicatorId) || "";
    var fields = FL.kra34Metadata.formFields(indicatorId, state.payload);
    var body = {};
    fields.forEach(function (f) {
      var el = document.getElementById(f.inputId);
      if (!el) return;
      body[f.id] = (el.value || "").trim();
    });
    return body;
  },

  applyOcrToInputs: function (state, options) {
    options = options || {};
    var onlyEmpty = options.onlyEmpty !== false;
    var indicatorId =
      (state.bundle && state.bundle.indicatorId) || (state.doc && state.doc.indicatorId) || "";
    var fields = FL.kra34Metadata.formFields(indicatorId, state.payload);
    var filled = [];
    fields.forEach(function (f) {
      var el = document.getElementById(f.inputId);
      if (!el) return;
      var ocrVal = FL.kra34Metadata.ocrFieldValue(state.payload, f.id);
      if (!ocrVal) return;
      if (onlyEmpty && (el.value || "").trim()) return;
      el.value = ocrVal;
      filled.push(f.label);
    });
    return filled;
  }
};
