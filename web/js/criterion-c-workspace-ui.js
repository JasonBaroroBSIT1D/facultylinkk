/**
 * KRA I Criterion C — reviewer workspace (Phase C3). Pure helpers.
 */
window.FL = window.FL || {};

FL.criterionCWorkspaceUi = {
  CRITERION_ID: "kra1-c",
  ANNEX_MAX_POINTS: 10,

  SLOT_LABELS: {
    approval_sheet: "Signed approval sheet",
    rrpa_copc: "RRPA or COPC for the academic program",
    mentor_designation: "Official mentor/coach designation",
    award_certificate: "Award, certificate, or photo of major prize",
    competition_mechanics: "Competition mechanics (major awards/winners)",
    awarding_organization: "Award-giving organization profile"
  },

  RESEARCH_TYPE_LABELS: {
    sp_cp: "Special Project / Capstone Project",
    ut: "Undergraduate Thesis",
    mt: "Master's Thesis",
    dd: "Doctoral Dissertation"
  },

  isPrimaryClaimDocument: function (doc, allDocs) {
    if (!doc || doc.criterionId !== FL.criterionCWorkspaceUi.CRITERION_ID) return false;
    if (doc.criterionCEvidence && doc.criterionCEvidence.isSupportingDocument) return false;
    var link = doc.criterionCEvidence && doc.criterionCEvidence.link;
    if (link && link.role === "supporting") return false;
    var legacy = doc.extractedInfo && doc.extractedInfo.criterionCEvidenceLink;
    if (legacy && legacy.role === "supporting") return false;
    if (allDocs && FL.criterionCWorkspaceUi.isReferencedAsSupporting(doc.id, allDocs)) return false;
    return true;
  },

  /** Checklist slots that hold the primary claim file — not supporting evidence. */
  PRIMARY_CLAIM_SLOTS: {
    approval_sheet: true,
    mentor_designation: true
  },

  isReferencedAsSupporting: function (docId, docs) {
    var primarySlots = FL.criterionCWorkspaceUi.PRIMARY_CLAIM_SLOTS;
    return (docs || []).some(function (primary) {
      var bundle = primary.criterionCEvidence && primary.criterionCEvidence.bundle;
      var checklist = bundle && bundle.checklist;
      if (!checklist) return false;
      return Object.keys(checklist).some(function (slot) {
        if (primarySlots[slot]) return false;
        var entry = checklist[slot];
        return entry && entry.documentId === docId;
      });
    });
  },

  normalizeWorkflowStatus: function (status) {
    var s = (status || "").trim().toLowerCase().replace(/_/g, "-");
    if (s === "pending-review" || s === "pending") return "pending-review";
    if (s === "needs-revision" || s === "revision") return "revision";
    return s || "unknown";
  },

  isFacultyDraftItem: function (item) {
    var st = FL.criterionCWorkspaceUi.normalizeWorkflowStatus(
      item && item.primary && item.primary.status
    );
    return st === "draft";
  },

  bundleFromAccomplishmentRow: function (row) {
    if (!row) return {};
    return {
      projectTitle: row.projectTitle,
      studentNames: row.studentNames,
      studentGroupLabel: row.studentGroupLabel,
      serviceCategory: row.serviceCategory,
      researchType: row.researchType,
      role: row.role,
      academicYear: row.academicYear,
      completionDate: row.completionDate,
      reviewStatus: row.reviewStatus,
      metadataConfirmed: row.metadataConfirmed,
      metadataFacultyConfirmedAt: row.metadataFacultyConfirmedAt,
      accomplishmentId: row.accomplishmentId
    };
  },

  mergeAccomplishmentListItems: function (apiRows, docs) {
    var ui = FL.criterionCWorkspaceUi;
    var cDocs = (docs || []).filter(function (d) {
      return d.criterionId === ui.CRITERION_ID;
    });
    var rows = apiRows && apiRows.length ? apiRows : null;
    if (!rows) {
      return ui.buildWorkspaceModel(cDocs);
    }
    return rows.map(function (row) {
      var docId = row.documentId;
      var primary = cDocs.find(function (d) {
        return d.id === docId;
      });
      if (!primary) {
        primary = {
          id: docId,
          criterionId: ui.CRITERION_ID,
          indicatorId: row.indicatorId,
          status: row.status,
          submittedAt: row.submittedAt,
          title: row.title
        };
      }
      var fromStore = primary.criterionCEvidence || {};
      var bundle = fromStore.bundle
        ? Object.assign({}, fromStore.bundle, ui.bundleFromAccomplishmentRow(row))
        : ui.bundleFromAccomplishmentRow(row);
      return {
        primary: primary,
        bundle: bundle,
        validation: fromStore.validation || {},
        scoring: {
          estimatedPoints: row.estimatedPoints,
          reviewerAssessedPoints: row.reviewerAssessedPoints,
          indicatorId: row.indicatorId
        },
        apiRow: row
      };
    });
  },

  evidenceCompletenessLabel: function (item) {
    var ui = FL.criterionCWorkspaceUi;
    var bundle = item.bundle || {};
    var validation = item.validation || {};
    var slots = ui.requiredSlotIds(bundle);
    var checklist = bundle.checklist || {};
    var missing = 0;
    var unverified = 0;
    slots.forEach(function (slotId) {
      var entry = checklist[slotId];
      var st = (entry && entry.status) || "missing";
      if (st === "missing" || !entry || !entry.documentId) missing += 1;
      else if (st !== "verified") unverified += 1;
    });
    if (missing) return missing + " required file(s) missing";
    if (unverified) return "Evidence uploaded — pending verification";
    if ((validation.validationStatus || "").toLowerCase() === "valid") return "Evidence complete";
    return validation.validationStatus
      ? ui.validationStatusMeta(validation.validationStatus).label
      : "Checklist in progress";
  },

  workflowStatusMeta: function (status) {
    var key = FL.criterionCWorkspaceUi.normalizeWorkflowStatus(status);
    var map = {
      draft: { badge: "info", label: "Faculty draft" },
      "pending-review": { badge: "pending", label: "Under review" },
      revision: { badge: "reviewer-required", label: "Needs revision" },
      "reviewer-required": { badge: "reviewer-required", label: "Reviewer action" },
      approved: { badge: "approved", label: "Approved" },
      rejected: { badge: "invalid", label: "Rejected" }
    };
    return map[key] || { badge: "info", label: status || "Unknown" };
  },

  maxCriterionCPoints: function (kraSettings) {
    var sc = FL.scoringConfiguration;
    if (sc && kraSettings) {
      var fromKs = sc.criterionCMax(kraSettings);
      if (fromKs != null) return fromKs;
    }
    if (sc && sc.hasApplicable && sc.hasApplicable()) {
      var live = sc.criterionCMax();
      if (live != null) return live;
    }
    if (sc && sc._canUseLiveApi && sc._canUseLiveApi() && sc._state && sc._state.loadedAt) {
      return null;
    }
    return FL.criterionCWorkspaceUi.ANNEX_MAX_POINTS;
  },

  officialPointsForIndicator: function (indicatorId, options) {
    var opts = options || {};
    var sc = FL.scoringConfiguration;
    if (sc && opts.kraSettings) {
      return sc.indicatorPoints(indicatorId, opts.kraSettings);
    }
    if (sc && sc.hasApplicable && sc.hasApplicable()) {
      return sc.indicatorPoints(indicatorId);
    }
    if (sc && sc._canUseLiveApi && sc._canUseLiveApi() && sc._state && sc._state.loadedAt) {
      return null;
    }
    var hit = FL.rules && FL.rules.findIndicator ? FL.rules.findIndicator(indicatorId) : null;
    if (hit && hit.indicator && hit.indicator.points != null) return Number(hit.indicator.points);
    return null;
  },

  serviceLabel: function (bundle, indicatorId) {
    var ui = FL.criterionCWorkspaceUi;
    var cat = bundle && bundle.serviceCategory;
    if (cat === "mentorship" || indicatorId === "kra1-c-mentor") return "Mentorship";
    return "Research advising / panel";
  },

  roleLabel: function (bundle) {
    var role = bundle && bundle.role;
    if (role === "adviser") return "Adviser";
    if (role === "panel") return "Panel member";
    return "—";
  },

  researchTypeLabel: function (bundle) {
    var ui = FL.criterionCWorkspaceUi;
    var rt = bundle && bundle.researchType;
    if (!rt) return "—";
    return ui.RESEARCH_TYPE_LABELS[rt] || rt;
  },

  isUnreliableResearchTitle: function (value) {
    var t = (value == null ? "" : String(value)).trim();
    if (!t || t.length < 4) return true;
    var lower = t.toLowerCase();
    if (lower.indexOf("signed approval sheet") >= 0 || lower.indexOf("approval sheet") >= 0) return true;
    if (lower.indexOf("sample") >= 0) return true;
    if (/^\d{1,3}[\s._-]+(?:signed|approval|sheet)/i.test(t)) return true;
    if (/\.(pdf|docx?|png|jpe?g)\b/i.test(t)) return true;
    if ((t.match(/_/g) || []).length >= 2 && (t.match(/\s/g) || []).length <= 1) return true;
    return false;
  },

  metadataConfirmationLabel: function (bundle) {
    var c = bundle && bundle.metadataConfirmed;
    if (!c || typeof c !== "object") return "Not confirmed by faculty";
    var required = ["projectTitle", "studentNames", "completionDate"];
    var ok = required.every(function (k) {
      return c[k] === true;
    });
    if (ok && bundle.metadataFacultyConfirmedAt) {
      return "Confirmed by faculty (" + bundle.metadataFacultyConfirmedAt + ")";
    }
    return ok ? "Confirmed by faculty" : "Awaiting faculty confirmation";
  },

  displayProjectTitle: function (bundle) {
    var t = bundle && bundle.projectTitle;
    if (t && String(t).trim() && !FL.criterionCWorkspaceUi.isUnreliableResearchTitle(t)) {
      return String(t).trim();
    }
    return "—";
  },

  accomplishmentTitle: function (bundle, doc) {
    var shown = FL.criterionCWorkspaceUi.displayProjectTitle(bundle);
    if (shown !== "—") return shown;
    return "Criterion C accomplishment";
  },

  validationStatusMeta: function (status) {
    var key = (status || "incomplete").toLowerCase();
    var map = {
      incomplete: { badge: "pending", label: "Incomplete" },
      reviewer_required: { badge: "reviewer-required", label: "Pending verification" },
      valid: { badge: "approved", label: "Ready for scoring" },
      invalid: { badge: "invalid", label: "Rejected / ineligible" }
    };
    return map[key] || { badge: "info", label: status || "Unknown" };
  },

  slotStatusMeta: function (status) {
    var key = (status || "missing").toLowerCase();
    var map = {
      missing: { badge: "invalid", label: "Missing" },
      present_unverified: { badge: "pending", label: "Pending Verification" },
      reviewer_required: { badge: "reviewer-required", label: "Needs Clarification" },
      verified: { badge: "approved", label: "Verified" }
    };
    return map[key] || { badge: "info", label: status };
  },

  reviewStatusMeta: function (reviewStatus) {
    var key = (reviewStatus || "pending").toLowerCase();
    var map = {
      pending: { badge: "pending", label: "Pending review" },
      approved: { badge: "approved", label: "Approved" },
      rejected: { badge: "invalid", label: "Rejected" }
    };
    return map[key] || { badge: "info", label: reviewStatus };
  },

  accomplishmentListBadgeMeta: function (item) {
    var ui = FL.criterionCWorkspaceUi;
    var bundle = (item && item.bundle) || {};
    var rs = (bundle.reviewStatus || "").toLowerCase();
    if (rs === "approved" || rs === "rejected") {
      return ui.reviewStatusMeta(rs);
    }
    if (ui.isFacultyDraftItem(item)) {
      return ui.workflowStatusMeta("draft");
    }
    return ui.workflowStatusMeta(item.primary && item.primary.status);
  },

  accomplishmentScoringLineHtml: function (item) {
    var ui = FL.criterionCWorkspaceUi;
    var esc = FL.esc;
    var bundle = (item && item.bundle) || {};
    var scoring = (item && item.scoring) || {};
    var primary = item.primary || {};
    var rs = (bundle.reviewStatus || "").toLowerCase();
    var assessed = scoring.reviewerAssessedPoints;
    if (rs === "approved" && assessed != null) {
      return (
        '<p class="cc-accomplishment-scoring"><strong>Reviewer-verified:</strong> ' +
        esc(String(assessed)) +
        " pts</p>"
      );
    }
    var est =
      scoring.estimatedPoints != null ? scoring.estimatedPoints : ui.officialPointsForIndicator(primary.indicatorId);
    return (
      '<p class="cc-accomplishment-scoring"><strong>Estimated (unverified):</strong> ' +
      (est != null ? esc(String(est)) + " pts" : "—") +
      "</p>"
    );
  },

  humanizeFlag: function (flag) {
    var map = {
      duplicate_service_suspected: "Possible duplicate service — verify before approving.",
      adviser_panel_same_thesis_review: "Adviser and panel on the same thesis — Needs Policy Review.",
      project_title_missing: "Project title missing.",
      student_names_missing: "Student name(s) missing.",
      student_names_ocr_missing: "OCR did not detect student names — enter them from the approval sheet.",
      student_names_ocr_needs_review: "OCR student names are uncertain — verify before approving.",
      completion_date_missing: "Completion date missing.",
      competition_name_missing: "Competition name missing.",
      review_rejected: "Previously rejected.",
      checklist_not_fully_verified: "Not all evidence verified.",
      reviewer_accomplishment_not_approved: "Awaiting reviewer decision."
    };
    if (map[flag]) return map[flag];
    if (flag && flag.indexOf("missing_") === 0) {
      var slot = flag.slice(8);
      var label = FL.criterionCWorkspaceUi.SLOT_LABELS[slot] || slot.replace(/_/g, " ");
      return "Missing: " + label;
    }
    return (flag || "").replace(/_/g, " ");
  },

  requiredSlotIds: function (bundle) {
    var cat = bundle && bundle.serviceCategory;
    if (cat === "mentorship") {
      return ["mentor_designation", "award_certificate", "competition_mechanics", "awarding_organization"];
    }
    return ["approval_sheet", "rrpa_copc"];
  },

  buildWorkspaceModel: function (docs) {
    var ui = FL.criterionCWorkspaceUi;
    var cDocs = (docs || []).filter(function (d) {
      return d.criterionId === ui.CRITERION_ID;
    });
    var primaries = cDocs.filter(function (d) {
      return ui.isPrimaryClaimDocument(d, cDocs);
    });
    return primaries.map(function (primary) {
      return {
        primary: primary,
        bundle: primary.criterionCEvidence && primary.criterionCEvidence.bundle,
        validation: primary.criterionCEvidence && primary.criterionCEvidence.validation,
        scoring: primary.criterionCEvidence && primary.criterionCEvidence.scoring
      };
    });
  },

  filterAccomplishments: function (items, query, statusFilter) {
    var ui = FL.criterionCWorkspaceUi;
    var q = (query || "").trim().toLowerCase();
    var sf = (statusFilter || "all").toLowerCase();
    return (items || []).filter(function (item) {
      if (sf !== "all") {
        var rs = ((item.bundle && item.bundle.reviewStatus) || "pending").toLowerCase();
        var wf = ui.normalizeWorkflowStatus(item.primary && item.primary.status);
        if (sf === "draft" && !ui.isFacultyDraftItem(item)) return false;
        if (sf === "under-review" && (ui.isFacultyDraftItem(item) || rs === "approved" || rs === "rejected")) {
          return false;
        }
        if (sf === "approved" && rs !== "approved") return false;
        if (sf === "rejected" && rs !== "rejected") return false;
        if (sf === "pending-review" && wf !== "pending-review" && wf !== "revision") return false;
      }
      if (!q) return true;
      var bundle = item.bundle || {};
      var title = ui.accomplishmentTitle(bundle, item.primary).toLowerCase();
      var hay = [
        title,
        (bundle.studentNames || "").toLowerCase(),
        (item.primary.indicatorId || "").toLowerCase(),
        ui.serviceLabel(bundle).toLowerCase(),
        ui.researchTypeLabel(bundle).toLowerCase(),
        ui.roleLabel(bundle).toLowerCase()
      ].join(" ");
      return hay.indexOf(q) >= 0;
    });
  },

  splitReviewAndDraftItems: function (items) {
    var ui = FL.criterionCWorkspaceUi;
    var review = [];
    var drafts = [];
    (items || []).forEach(function (item) {
      if (ui.isFacultyDraftItem(item)) drafts.push(item);
      else review.push(item);
    });
    return { review: review, drafts: drafts };
  },

  summaryHeaderHtml: function (params) {
    var esc = FL.esc;
    var ui = FL.criterionCWorkspaceUi;
    var summary = params.summary || {};
    var counts = summary.reviewCounts || {};
    var assessed = summary.estimatedPoints;
    var max = summary.maxPoints != null ? summary.maxPoints : ui.maxCriterionCPoints(params.kraSettings);
    var draftEst = summary.draftEstimatedSum;
    var visible = params.visibleCount != null ? params.visibleCount : summary.accomplishmentCount || 0;
    var banner = params.configBanner;
    if (banner == null && FL.scoringConfiguration) {
      banner = FL.scoringConfiguration.bannerHtml({ compact: true });
    }
    var configNote = params.scoringConfigLabel
      ? `<p class="note cc-config-ref">${esc(params.scoringConfigLabel)}</p>`
      : "";
    return (banner || "") + `<section class="card cc-workspace-head">
      <h2 class="evidence-section-title">${esc(params.criterionTitle || "Criterion C — Research Advising and Mentorship Services")}</h2>
      <p class="note cc-workspace-faculty">Faculty: <strong>${esc(params.personName || "")}</strong></p>
      ${configNote}
      <p class="note">Criterion maximum: <strong>${max != null ? esc(String(max)) : "—"}</strong> points</p>
      <div class="cc-summary-grid cc-summary-grid--compact">
        <article class="cc-stat-card"><span class="cc-stat-label">Accomplishments</span><strong>${esc(String(visible))}</strong></article>
        <article class="cc-stat-card"><span class="cc-stat-label">Under review</span><strong>${esc(String(counts.pending || 0))}</strong></article>
        <article class="cc-stat-card"><span class="cc-stat-label">Approved</span><strong>${esc(String(counts.approved || 0))}</strong></article>
        <article class="cc-stat-card"><span class="cc-stat-label">Rejected</span><strong>${esc(String(counts.rejected || 0))}</strong></article>
        <article class="cc-stat-card"><span class="cc-stat-label">Reviewer-assessed total</span><strong>${assessed != null ? esc(String(assessed)) + " / " + esc(String(max)) : "—"}</strong></article>
        <article class="cc-stat-card cc-stat-card--muted"><span class="cc-stat-label">Estimated (unverified)</span><strong>${draftEst != null ? esc(String(draftEst)) + " pts" : "—"}</strong></article>
      </div>
      <p class="note cc-workspace-hint">Verify each evidence file in the checklist, then approve the accomplishment. Approved accomplishments mark their linked source PDFs as approved in the faculty PDF document review column.</p>
    </section>`;
  },

  accomplishmentScoringContextHtml: function (params) {
    var ui = FL.criterionCWorkspaceUi;
    var esc = FL.esc;
    var doc = params.doc || {};
    var bundle = params.bundle || {};
    var ind = doc.indicatorId;
    var refOpts = params.refKraSettings ? { kraSettings: params.refKraSettings } : {};
    var applicable = ui.officialPointsForIndicator(ind, refOpts);
    if (applicable == null) applicable = ui.officialPointsForIndicator(ind);
    var max = ui.maxCriterionCPoints(params.refKraSettings);
    var roleLabel = ui.roleLabel(bundle);
    var typeLabel = ui.researchTypeLabel(bundle);
    var service = ui.serviceLabel(bundle, ind);
    if (service === "Mentorship") {
      typeLabel = "Mentorship";
      roleLabel = "—";
    }
    return (
      '<dl class="kv-grid kv-grid--compact cc-scoring-context">' +
      FL.documents.kvRow("Faculty", esc(params.facultyName || "—")) +
      FL.documents.kvRow("Service", esc(service)) +
      (typeLabel !== "—" ? FL.documents.kvRow("Research type", esc(typeLabel)) : "") +
      (roleLabel !== "—" ? FL.documents.kvRow("Role", esc(roleLabel)) : "") +
      FL.documents.kvRow(
        "Applicable points",
        applicable != null ? esc(String(applicable)) + " pts" : "—"
      ) +
      FL.documents.kvRow(
        "Criterion C maximum",
        max != null ? esc(String(max)) + " pts" : "—"
      ) +
      "</dl>"
    );
  },

  accomplishmentCardHtml: function (item, options) {
    var ui = FL.criterionCWorkspaceUi;
    var esc = FL.esc;
    var opt = options || {};
    var primary = item.primary;
    var bundle = item.bundle || {};
    var wfMeta = ui.accomplishmentListBadgeMeta(item);
    var href = opt.reviewHref ? opt.reviewHref(primary) : "#";
    var readOnly = opt.readOnly || ui.isFacultyDraftItem(item);
    var rolePart =
      bundle.role === "adviser" || bundle.role === "panel"
        ? " · " + esc(ui.roleLabel(bundle))
        : "";
    var action = readOnly
      ? `<a class="btn btn-ghost" href="${esc(href)}">View draft</a>`
      : `<a class="btn btn-primary" href="${esc(href)}">${esc(opt.isAdmin ? "Open" : "Open Review")}</a>`;
    return `<article class="card cc-accomplishment-card${readOnly ? " cc-accomplishment-card--draft" : ""}" data-doc-id="${esc(primary.id)}">
      <header class="cc-accomplishment-head">
        <div>
          <p class="cb-eyebrow">${esc(ui.researchTypeLabel(bundle))}${rolePart}</p>
          <h3>${esc(ui.accomplishmentTitle(bundle, primary))}</h3>
        </div>
        ${FL.ui.statusBadge(wfMeta.badge)}
      </header>
      <p class="sub">Academic year ${esc(bundle.academicYear || "—")} · ${esc(wfMeta.label)}</p>
      ${ui.accomplishmentScoringLineHtml(item)}
      <div class="cc-accomplishment-actions">${action}</div>
    </article>`;
  },

  listSectionHtml: function (items, params, listId) {
    var ui = FL.criterionCWorkspaceUi;
    if (!items.length) return "";
    var cards = items.map(function (item) {
      return ui.accomplishmentCardHtml(item, {
        reviewHref: params.reviewHref,
        isAdmin: params.isAdmin,
        readOnly: params.readOnly
      });
    }).join("");
    return `<div class="cc-accomplishment-list" id="${listId}">${cards}</div>`;
  },

  criterionCReviewWorkspaceHtml: function (params) {
    var ui = FL.criterionCWorkspaceUi;
    var esc = FL.esc;
    var split = ui.splitReviewAndDraftItems(params.items || []);
    var reviewItems = split.review;
    var draftItems = split.drafts;
    var totalVisible = reviewItems.length + draftItems.length;
    var summaryParams = Object.assign({}, params, {
      visibleCount: totalVisible
    });
    var emptyReview = !reviewItems.length;
    var emptyAll = !totalVisible;
    var apiCount = params.summary && params.summary.accomplishmentCount;
    var mismatch = !emptyAll && emptyReview && draftItems.length && apiCount > draftItems.length;
    var reviewBlock = emptyReview
      ? (mismatch
        ? FL.ui.empty("No accomplishments ready for review", "Submitted items could not be loaded. Refresh the page or open from the review queue.")
        : draftItems.length
          ? `<p class="note">No submitted accomplishments yet. Faculty drafts are listed below for visibility only.</p>`
          : FL.ui.empty("No accomplishments yet", "This faculty member has not created a Criterion C research or mentorship accomplishment."))
      : ui.listSectionHtml(reviewItems, params, "cc-accomplishment-list");
    var draftBlock = draftItems.length
      ? `<section class="cc-draft-section">
          <h3 class="evidence-section-title">Faculty drafts</h3>
          ${ui.listSectionHtml(draftItems, Object.assign({}, params, { readOnly: true }), "cc-draft-list")}
        </section>`
      : "";
    return (
      ui.summaryHeaderHtml(summaryParams) +
      reviewBlock +
      draftBlock +
      (emptyAll && apiCount > 0
        ? FL.ui.empty(
            "List sync issue",
            "The summary reports " +
              esc(String(apiCount)) +
              " accomplishment(s) but the workspace could not render them. Try refreshing documents."
          )
        : "")
    );
  },

  /** @deprecated use criterionCReviewWorkspaceHtml */
  workspaceListHtml: function (params) {
    return FL.criterionCWorkspaceUi.criterionCReviewWorkspaceHtml(params);
  },

  REVIEW_STEPS: [
    { id: "details", label: "1. Accomplishment details" },
    { id: "evidence", label: "2. Supporting evidence" },
    { id: "decision", label: "3. Final assessment" }
  ],

  reviewStepsBanner: function (activeStep) {
    var esc = FL.esc;
    var steps = FL.criterionCWorkspaceUi.REVIEW_STEPS;
    return (
      '<nav class="cb-review-steps" aria-label="Review steps">' +
      steps
        .map(function (s) {
          var on = s.id === activeStep;
          return (
            '<span class="cb-review-step' +
            (on ? " is-active" : "") +
            '">' +
            esc(s.label) +
            "</span>"
          );
        })
        .join("") +
      "</nav>"
    );
  },

  buildEvidenceSlotItems: function (bundle, primaryDoc, slotIds) {
    var ui = FL.criterionCWorkspaceUi;
    var checklist = (bundle && bundle.checklist) || {};
    return (slotIds || []).map(function (slotId) {
      var entry = checklist[slotId] || {};
      var fileId = entry.documentId;
      var fileDoc = null;
      if (fileId && primaryDoc) {
        fileDoc = fileId === primaryDoc.id ? primaryDoc : FL.store.documentById(fileId);
      }
      var status = entry.status || (fileId ? "present_unverified" : "missing");
      return {
        slotId: slotId,
        label: ui.SLOT_LABELS[slotId] || slotId.replace(/_/g, " "),
        entry: entry,
        fileDoc: fileDoc,
        status: status
      };
    });
  },

  slotMissingMessage: function (slotId) {
    var label = FL.criterionCWorkspaceUi.SLOT_LABELS[slotId] || slotId;
    return "The faculty member has not uploaded " + label + " yet. You cannot verify this slot until a file is linked.";
  },

  evidenceVerificationSummaryRows: function (bundle, slotIds) {
    var ui = FL.criterionCWorkspaceUi;
    var items = ui.buildEvidenceSlotItems(bundle, null, slotIds);
    return items.map(function (item) {
      var stMeta = ui.slotStatusMeta(item.status);
      return {
        slotId: item.slotId,
        label: item.label,
        status: item.status,
        statusMeta: stMeta,
        ok: item.status === "verified"
      };
    });
  },

  reviewApprovalGate: function (validation, canDecide) {
    var flags = (validation && validation.flags) || [];
    var blockers = (validation && validation.blockers) || [];
    var policyBlock = flags.some(function (f) {
      return f === "adviser_panel_same_thesis_review" || f === "duplicate_service_suspected";
    });
    var canApprove =
      !!canDecide &&
      !!(validation && validation.readyForReviewer) &&
      !blockers.length &&
      !policyBlock;
    var blockerHint = "";
    if (policyBlock) {
      blockerHint = "Resolve policy flags (duplicate service or adviser/panel review) before approving.";
    } else if (blockers.length) {
      blockerHint = blockers[0];
    } else if (!validation || !validation.readyForReviewer) {
      blockerHint = "Complete all requirements before approving.";
    }
    return { canApprove: canApprove, policyBlock: policyBlock, blockerHint: blockerHint };
  },

  ocrFieldValue: function (ocrExtraction, key) {
    var fields =
      ocrExtraction && ocrExtraction.fields && typeof ocrExtraction.fields === "object"
        ? ocrExtraction.fields
        : {};
    var entry = fields[key];
    if (!entry || entry.value == null) return "";
    return String(entry.value).trim();
  },

  ocrStructuredStudents: function (ocrExtraction) {
    var structured = ocrExtraction && ocrExtraction.structured;
    if (!structured || !Array.isArray(structured.students)) return [];
    return structured.students.filter(function (n) {
      return n && String(n).trim();
    });
  },

  ocrStudentNeedsReview: function (payload) {
    var flags = (payload && payload.ocrReviewFlags) || [];
    if (flags.indexOf("student_names_ocr_needs_review") >= 0) return true;
    if (flags.indexOf("student_names_ocr_missing") >= 0) return true;
    var fields =
      payload && payload.ocrExtraction && payload.ocrExtraction.fields
        ? payload.ocrExtraction.fields
        : {};
    var entry = fields.studentNames;
    if (!entry) return false;
    var st = (entry.status || "").toLowerCase();
    return st === "needs_review" || st === "missing";
  },

  isResearchAccomplishment: function (bundle) {
    return (bundle && bundle.serviceCategory || "").toLowerCase() !== "mentorship";
  },

  studentNamesInlineWarning: function (payload, bundle) {
    var ui = FL.criterionCWorkspaceUi;
    var saved = (bundle && bundle.studentNames || "").trim();
    if (saved) {
      if (ui.ocrStudentNeedsReview(payload)) {
        return "Saved names present — confirm they match the approval sheet.";
      }
      return "";
    }
    if (ui.ocrStudentNeedsReview(payload)) {
      return "Missing or uncertain — confirm from the approval sheet and save.";
    }
    return "Required — enter student name(s) from the approval sheet.";
  },

  researchDetailsCardHtml: function (params) {
    var ui = FL.criterionCWorkspaceUi;
    var esc = FL.esc;
    var bundle = params.bundle || {};
    if (!ui.isResearchAccomplishment(bundle)) return "";
    var ocr = params.ocrExtraction || null;
    var payload = params.payload || null;
    var canEdit = !!params.canDecide;
    var studentBundle = (bundle.studentNames || "").trim();
    var studentOcr = ui.ocrFieldValue(ocr, "studentNames");
    var studentInput = studentBundle || studentOcr;
    var ayBundle = (bundle.academicYear || "").trim();
    var ayOcr = ui.ocrFieldValue(ocr, "academicYear");
    var ayInput = ayBundle || ayOcr;
    var groupBundle = (bundle.studentGroupLabel || "").trim();
    var groupOcr = ui.ocrFieldValue(ocr, "studentGroupLabel");
    var groupInput = groupBundle || groupOcr;
    var showGroup = !!(groupInput || params.showGroupEditor);
    var completionBundle = (bundle.completionDate || "").trim();
    var completionOcr = ui.ocrFieldValue(ocr, "completionDate");
    var completionInput = completionBundle || completionOcr;
    var warn = ui.studentNamesInlineWarning(payload || { ocrExtraction: ocr, ocrReviewFlags: params.ocrReviewFlags }, bundle);
    var warnHtml = warn
      ? ' <span class="cc-inline-warn" role="status">' + esc(warn) + "</span>"
      : "";
    var fields = canEdit
      ? '<div class="cc-research-fields">' +
        '<label class="field field-wide cc-field-students">' +
        "<span>Student name(s)" +
        warnHtml +
        "</span>" +
        '<input type="text" id="cc-reviewer-student-names" autocomplete="off" value="' +
        esc(studentInput) +
        '" placeholder="As shown on the signed approval sheet" />' +
        "</label>" +
        '<label class="field"><span>Academic year</span>' +
        '<input type="text" id="cc-reviewer-academic-year" autocomplete="off" value="' +
        esc(ayInput) +
        '" placeholder="e.g. 2025-2026" /></label>' +
        '<label class="field"><span>Approval date</span>' +
        '<input type="date" id="cc-reviewer-completion-date" value="' +
        esc(completionInput) +
        '" /></label>' +
        (showGroup
          ? '<label class="field field-wide"><span>Group (optional)</span>' +
            '<input type="text" id="cc-reviewer-group-label" autocomplete="off" value="' +
            esc(groupInput) +
            '" placeholder="Group name or number" /></label>'
          : canEdit
            ? '<p class="cc-group-toggle"><button type="button" class="btn btn-ghost btn-small" id="cc-show-group-field">Add group label</button></p>'
            : "") +
        '<div class="cc-metadata-actions">' +
        '<button type="button" class="btn btn-primary" id="cc-save-research-metadata">Save details</button>' +
        '<span id="cc-metadata-save-indicator" class="cc-save-indicator" aria-live="polite"></span>' +
        "</div></div>"
      : '<dl class="kv-grid kv-grid--compact">' +
        FL.documents.kvRow("Student name(s)", esc(studentInput || "—")) +
        FL.documents.kvRow("Academic year", esc(ayInput || "—")) +
        FL.documents.kvRow("Approval date", esc(completionInput || "—")) +
        (groupInput ? FL.documents.kvRow("Group", esc(groupInput)) : "") +
        "</dl>";
    return (
      '<section class="card cc-research-details">' +
      '<h2 class="cb-subhead">Research details</h2>' +
      '<p class="note">Prefilled from OCR when available. Save confirmed values for backend approval validation.</p>' +
      fields +
      ui.ocrDetailsCollapsibleHtml(params) +
      "</section>"
    );
  },

  /** @deprecated use researchDetailsCardHtml */
  reviewerResearchMetadataEditorHtml: function (params) {
    return FL.criterionCWorkspaceUi.researchDetailsCardHtml(params);
  },

  ocrDetailsCollapsibleHtml: function (params) {
    var ui = FL.criterionCWorkspaceUi;
    var esc = FL.esc;
    var ocr = params.ocrExtraction;
    var bundle = params.bundle || {};
    var ocrStatus = (params.ocrStatus || "pending").toLowerCase();
    var rows = ui.ocrResearchFieldRows(ocr, bundle);
    var structured = ocr && ocr.structured ? ocr.structured : {};
    var extra =
      structured.students && structured.students.length
        ? "<p class=\"note\"><strong>OCR student list:</strong> " +
          esc(structured.students.join(", ")) +
          "</p>"
        : "";
    if (structured.advisers && structured.advisers.length) {
      extra +=
        '<p class="note">Adviser(s) detected (excluded from students): ' +
        esc(structured.advisers.join(", ")) +
        "</p>";
    }
    if (structured.panelMembers && structured.panelMembers.length) {
      extra +=
        '<p class="note">Panel member(s) detected (excluded from students): ' +
        esc(structured.panelMembers.join(", ")) +
        "</p>";
    }
    var body = rows.map(function (r) {
      return r.html;
    }).join("");
    var statusLine = "";
    if (ocrStatus === "processing" || ocrStatus === "pending") {
      statusLine = '<p class="note">OCR in progress — fields may update automatically.</p>';
    } else if (ocrStatus === "failed") {
      statusLine =
        '<p class="note warn">' +
        esc(params.ocrError ? String(params.ocrError) : "OCR failed.") +
        (params.canRetry
          ? ' <button type="button" class="btn btn-ghost btn-small" id="cc-ocr-retry">Retry OCR</button>'
          : "") +
        "</p>";
    }
    if (!body && !statusLine && !extra) {
      return "";
    }
    return (
      '<details class="cc-ocr-details">' +
      '<summary>View OCR details</summary>' +
      '<div class="cc-ocr-details-body">' +
      statusLine +
      extra +
      (body ? '<dl class="kv-grid kv-grid--compact">' + body + "</dl>" : "") +
      "</div></details>"
    );
  },

  OCR_RESEARCH_FIELD_LABELS: {
    projectTitle: "Research / project title",
    studentNames: "Student name(s)",
    studentGroupLabel: "Group label",
    academicYear: "Academic year",
    completionDate: "Completion / approval date"
  },

  ocrResearchFieldRows: function (ocrExtraction, bundle) {
    var ui = FL.criterionCWorkspaceUi;
    var esc = FL.esc;
    var fields =
      ocrExtraction && ocrExtraction.fields && typeof ocrExtraction.fields === "object"
        ? ocrExtraction.fields
        : {};
    return Object.keys(ui.OCR_RESEARCH_FIELD_LABELS).map(function (key) {
      var label = ui.OCR_RESEARCH_FIELD_LABELS[key];
      var entry = fields[key];
      var ocrVal = entry && entry.value ? String(entry.value).trim() : "";
      var bundleVal = bundle && bundle[key] ? String(bundle[key]).trim() : "";
      var shown = bundleVal || ocrVal || "—";
      var status = entry && entry.status ? String(entry.status) : "";
      var conf = entry && entry.confidence ? String(entry.confidence) : "";
      var note = "";
      if (key === "studentNames" && status === "needs_review") {
        note = "Uncertain OCR — verify student names (not adviser/panel) before approving.";
      } else if (!bundleVal && !ocrVal && key !== "studentGroupLabel") {
        note = "Missing — verify on the signed approval sheet.";
      } else if (conf === "medium" || conf === "low") {
        note = "Uncertain OCR — verify or correct during review.";
      } else if (status === "missing" && key !== "studentGroupLabel") {
        note = "Not found in OCR text — verify manually.";
      }
      return {
        key: key,
        label: label,
        value: shown,
        note: note,
        html:
          FL.documents.kvRow(esc(label), esc(shown)) +
          (note ? '<p class="note cc-ocr-field-note warn">' + esc(note) + "</p>" : "")
      };
    });
  },

  ocrResearchPanelHtml: function (params) {
    return FL.criterionCWorkspaceUi.ocrDetailsCollapsibleHtml(params);
  },

  evidenceChecklistCompactHtml: function (params) {
    var ui = FL.criterionCWorkspaceUi;
    var esc = FL.esc;
    var items = params.evidenceItems || [];
    if (!items.length) {
      return '<section class="card cc-evidence-checklist"><p class="note">No evidence checklist configured.</p></section>';
    }
    var canDecide = !!params.canDecide;
    var reviewState = params.state || null;
    var canVerify =
      params.canVerifyEvidence != null
        ? params.canVerifyEvidence
        : reviewState && FL.reviewerAccomplishmentState
          ? FL.reviewerAccomplishmentState.canVerifyEvidence(reviewState)
          : canDecide;
    var draftAwaiting =
      reviewState && FL.reviewerAccomplishmentState
        ? FL.reviewerAccomplishmentState.isDraftAwaitingFaculty(reviewState)
        : false;
    var rows = items
      .map(function (item) {
        var stMeta = ui.slotStatusMeta(item.status);
        var missing = !item.fileDoc || item.status === "missing" || !item.entry.documentId;
        var displayLabel =
          draftAwaiting && !missing
            ? FL.reviewerAccomplishmentState.slotVerificationDisplayLabel(reviewState, item.status)
            : stMeta.label;
        var open =
          !missing && item.fileDoc && item.fileDoc.fileUrl
            ? '<a class="btn btn-ghost btn-small" target="_blank" rel="noopener" href="' +
              esc(item.fileDoc.fileUrl) +
              '">Open</a>'
            : "";
        var verify = "";
        if (canVerify && !missing) {
          verify =
            '<select class="cc-evidence-slot-select" data-cc-slot="' +
            esc(item.slotId) +
            '" aria-label="Verification for ' +
            esc(item.label) +
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
            "</select>" +
            '<span class="cc-slot-save-indicator" data-cc-slot-indicator="' +
            esc(item.slotId) +
            '" aria-live="polite"></span>';
        } else if (missing) {
          verify = '<span class="note warn">Not uploaded</span>';
        } else {
          verify = esc(displayLabel);
        }
        return (
          "<tr>" +
          "<td>" +
          esc(item.label) +
          "</td>" +
          "<td>" +
          FL.ui.statusBadge(stMeta.badge) +
          "</td>" +
          "<td class=\"cc-evidence-checklist-actions\">" +
          verify +
          " " +
          open +
          "</td></tr>"
        );
      })
      .join("");
    return (
      '<section class="card cc-evidence-checklist">' +
      '<h2 class="cb-subhead">Evidence checklist</h2>' +
      (draftAwaiting
        ? '<p class="note">Evidence is view-only until the faculty submits this accomplishment for review.</p>'
        : '<p class="note">Checklist verification is separate from accomplishment approval — confirm each file here before you approve below.</p>') +
      '<table class="cc-evidence-checklist-table"><thead><tr><th>Document</th><th>Status</th><th>Review</th></tr></thead>' +
      "<tbody>" +
      rows +
      "</tbody></table></section>"
    );
  },

  compactDecisionSectionHtml: function (params) {
    var ui = FL.criterionCWorkspaceUi;
    var esc = FL.esc;
    var validation = params.validation || {};
    var scoring = params.scoring || {};
    var bundle = params.bundle || {};
    var gate = ui.reviewApprovalGate(validation, params.canDecide);
    var ind = params.doc && params.doc.indicatorId;
    var refOpts = params.refKraSettings ? { kraSettings: params.refKraSettings } : {};
    var applicable = ui.officialPointsForIndicator(ind, refOpts);
    if (applicable == null) applicable = ui.officialPointsForIndicator(ind);
    var defaultPts =
      params.assessedPoints ||
      (applicable != null ? String(applicable) : "");
    var blocker =
      gate.canApprove || !params.canDecide
        ? ""
        : '<p class="cc-approve-blocker note warn" role="status">' + esc(gate.blockerHint || "") + "</p>";
    var controls = params.canDecide
      ? '<div class="cc-decision-compact">' +
        '<p class="cc-decision-meta"><strong>Estimated (unverified):</strong> ' +
        (scoring.estimatedPoints != null ? esc(String(scoring.estimatedPoints)) + " pts" : "—") +
        " · <strong>Published service points:</strong> " +
        (applicable != null ? esc(String(applicable)) + " pts" : "—") +
        "</p>" +
        '<label class="field field-wide"><span>Assessed points</span>' +
        '<input type="number" step="0.01" id="cc-assessed-points" value="' +
        esc(defaultPts) +
        '" /></label>' +
        '<label class="field field-wide"><span>Remarks (min. 10 characters to approve or reject)</span>' +
        '<textarea id="cc-remarks" rows="3">' +
        esc(params.remarks || "") +
        "</textarea></label>" +
        '<div class="cc-decision-row">' +
        '<button type="button" class="btn btn-primary" id="cc-approve"' +
        (gate.canApprove ? "" : " disabled") +
        ' title="' +
        esc(gate.blockerHint || "") +
        '">Approve</button>' +
        '<button type="button" class="btn btn-danger" id="cc-reject">Reject</button>' +
        blocker +
        "</div></div>"
      : '<p class="note">Read-only — approval actions are disabled.</p>';
    var history = (bundle.reviewerAssessment && bundle.reviewerAssessment.history) || [];
    var historyHtml = history.length
      ? '<ul class="cc-review-history">' +
        history
          .map(function (h) {
            return (
              "<li>" +
              esc(h.reviewStatus || "") +
              " · " +
              esc(String(h.assessedPoints != null ? h.assessedPoints : "")) +
              "</li>"
            );
          })
          .join("") +
        "</ul>"
      : "";
    return (
      '<section class="card cc-decision-compact">' +
      '<h2 class="cb-subhead">Review decision</h2>' +
      controls +
      historyHtml +
      "</section>"
    );
  },

  compactReviewPageHtml: function (state) {
    var ui = FL.criterionCWorkspaceUi;
    var esc = FL.esc;
    var bundle = state.bundle || {};
    var ind = state.doc && state.doc.indicatorId;
    var ocrStatus =
      (state.payload && state.payload.ocrStatus) ||
      (state.doc && state.doc.ocr && state.doc.ocr.status) ||
      "pending";
    var researchParams = {
      bundle: bundle,
      payload: state.payload,
      ocrExtraction: state.payload && state.payload.ocrExtraction,
      ocrReviewFlags: (state.payload && state.payload.ocrReviewFlags) || [],
      ocrStatus: ocrStatus,
      ocrError: state.doc && state.doc.ocr && state.doc.ocr.error,
      canDecide: state.canDecide,
      showGroupEditor: !!state.showGroupEditor
    };
    var mentorshipBlock = "";
    if (!ui.isResearchAccomplishment(bundle) && bundle.mentorship) {
      mentorshipBlock =
        '<section class="card"><h2 class="cb-subhead">Mentorship details</h2>' +
        '<dl class="kv-grid kv-grid--compact">' +
        FL.documents.kvRow("Competition", esc(bundle.mentorship.competitionName || "—")) +
        "</dl></section>";
    }
    return (
      '<div class="portal-page cb-simple-review cc-compact-review">' +
      (state.chromeHtml || "") +
      '<header class="card cb-simple-head cc-compact-head">' +
      '<a class="btn btn-ghost btn-small" href="' +
      esc(state.backHref) +
      '">' +
      esc(state.backLabel) +
      "</a>" +
      "<h1>" +
      esc(ui.accomplishmentTitle(bundle, state.doc)) +
      "</h1>" +
      '<p class="sub">' +
      esc(state.facultyName || "Faculty") +
      " · " +
      esc(ui.serviceLabel(bundle, ind)) +
      " · " +
      esc(ui.researchTypeLabel(bundle)) +
      " · " +
      esc(ui.roleLabel(bundle)) +
      "</p></header>" +
      ui.researchDetailsCardHtml(researchParams) +
      mentorshipBlock +
      (FL.reviewerAccomplishmentState && FL.reviewerAccomplishmentState.isDraftAwaitingFaculty(state)
        ? FL.reviewerAccomplishmentState.draftBannerHtml()
        : "") +
      ui.evidenceChecklistCompactHtml({
        evidenceItems: state.evidenceItems,
        canDecide: state.canDecide,
        state: state
      }) +
      (FL.reviewerAccomplishmentState && FL.reviewerAccomplishmentState.canSavePreparationNotes(state)
        ? FL.reviewerAccomplishmentState.preparationNotesSectionHtml(state)
        : "") +
      (FL.reviewerAccomplishmentState && FL.reviewerAccomplishmentState.isDraftAwaitingFaculty(state)
        ? ""
        : ui.compactDecisionSectionHtml({
            validation: state.validation,
            scoring: state.scoring,
            bundle: bundle,
            doc: state.doc,
            canDecide: state.canDecide,
            remarks: state.remarks,
            assessedPoints: state.assessedPoints,
            refKraSettings: state.refKraSettings
          })) +
      "</div>"
    );
  },

  slotStatusShouldPersist: function (newStatus, confirmedStatus) {
    return (newStatus || "") !== (confirmedStatus || "");
  },

  slotSaveIndicatorMessage: function (phase, savedStatus) {
    if (phase === "saving") return "Saving…";
    if (phase === "error") return "Could not save — change status again to retry.";
    if (phase === "saved") {
      if (savedStatus === "verified") return "Saved — Verified";
      if (savedStatus === "reviewer_required") return "Saved — Needs clarification";
      if (savedStatus === "present_unverified") return "Saved — Pending verification";
      return "Saved";
    }
    return "";
  },

  syncConfirmedSlotStatuses: function (state) {
    var checklist = (state.bundle && state.bundle.checklist) || {};
    var map = {};
    (state.slotIds || []).forEach(function (slotId) {
      var entry = checklist[slotId];
      map[slotId] = (entry && entry.status) || "missing";
    });
    state.verificationSave = state.verificationSave || { pending: false, requestId: 0 };
    state.verificationSave.confirmedBySlot = map;
    return map;
  },

  validationMessagesHtml: function (validation) {
    var ui = FL.criterionCWorkspaceUi;
    var esc = FL.esc;
    var flags = (validation && validation.flags) || [];
    var blockers = (validation && validation.blockers) || [];
    var flagHtml = flags
      .map(function (f) {
        var policy = f === "adviser_panel_same_thesis_review" || f === "duplicate_service_suspected";
        return (
          '<li class="' +
          (policy ? "warn" : "") +
          '">' +
          esc(ui.humanizeFlag(f)) +
          (policy ? " <strong>Needs policy review</strong>" : "") +
          "</li>"
        );
      })
      .join("");
    var blockerHtml = blockers.map(function (b) {
      return "<li>" + esc(b) + "</li>";
    }).join("");
    return { flagHtml: flagHtml, blockerHtml: blockerHtml, hasBlockers: blockers.length > 0 };
  }
};
