/**
 * KRA II Criterion A — reviewer/faculty-friendly labels and compact review layout.
 */
window.FL = window.FL || {};

FL.kra2AWorkspaceUi = {
  CRITERION_ID: "kra2-a",

  SLOT_LABELS: {
    primary_output: "Primary supporting document",
    contribution_certificate: "Certificate of Contribution (Annex D)",
    peer_review_evidence: "Peer review and academic press evidence",
    indexing_certification: "Indexing certification (Research Director)",
    citing_publication_evidence: "Citing article (PDF)",
    translation_impact_evidence: "Proof of project, policy, or product use"
  },

  CRITERION_A_REQUIRED_SLOTS: {
    "kra2-a-book-sole": ["primary_output", "peer_review_evidence"],
    "kra2-a-book-co": ["primary_output", "contribution_certificate"],
    "kra2-a-chapter-sole": ["primary_output", "peer_review_evidence"],
    "kra2-a-chapter-co": ["primary_output", "contribution_certificate"],
    "kra2-a-journal-sole": ["primary_output", "indexing_certification"],
    "kra2-a-journal-co": ["primary_output", "indexing_certification", "contribution_certificate"],
    "kra2-a-monograph-sole": ["primary_output", "peer_review_evidence"],
    "kra2-a-monograph-co": ["primary_output", "contribution_certificate"],
    "kra2-a-translation-sole": ["primary_output", "translation_impact_evidence"],
    "kra2-a-translation-co": ["primary_output", "translation_impact_evidence", "contribution_certificate"],
    "kra2-a-cite": ["primary_output", "citing_publication_evidence", "indexing_certification"]
  },

  CRITERION_B_REQUIRED_SLOTS: {
    "kra2-b-patent-a-sole": ["primary_output", "invention_photo", "president_special_order"],
    "kra2-b-patent-p-sole": ["primary_output", "invention_photo", "president_special_order"],
    "kra2-b-patent-g-sole": ["primary_output", "invention_photo", "president_special_order"],
    "kra2-b-patent-a-co": ["primary_output", "contribution_certificate"],
    "kra2-b-patent-p-co": ["primary_output", "contribution_certificate"],
    "kra2-b-patent-g-co": ["primary_output", "contribution_certificate"],
    "kra2-b-comm-local": [
      "product_photo",
      "patent_certificate",
      "licensing_or_cpr_evidence",
      "commercialization_proof",
      "rd_itso_certification"
    ],
    "kra2-b-comm-intl": [
      "product_photo",
      "patent_certificate",
      "licensing_or_cpr_evidence",
      "commercialization_proof",
      "rd_itso_certification"
    ],
    "kra2-b-um-sole": ["primary_output", "invention_photo", "president_special_order"],
    "kra2-b-id-sole": ["primary_output", "invention_photo", "president_special_order"],
    "kra2-b-um-co": ["primary_output", "contribution_certificate"],
    "kra2-b-id-co": ["primary_output", "contribution_certificate"],
    "kra2-b-sw-new-sole": [
      "president_special_order",
      "project_summary",
      "software_documentation",
      "primary_output",
      "utilization_certification"
    ],
    "kra2-b-sw-new-co": [
      "president_special_order",
      "project_summary",
      "software_documentation",
      "primary_output",
      "utilization_certification",
      "contribution_certificate"
    ],
    "kra2-b-sw-upd-sole": [
      "president_special_order",
      "project_summary",
      "primary_output",
      "utilization_certification",
      "software_update_description"
    ],
    "kra2-b-sw-upd-co": [
      "president_special_order",
      "project_summary",
      "primary_output",
      "utilization_certification",
      "software_update_description",
      "contribution_certificate"
    ],
    "kra2-b-variety-sole": ["president_special_order", "registration_deposit_evidence"],
    "kra2-b-variety-co": ["registration_deposit_evidence", "contribution_certificate"]
  },

  CRITERION_C_REQUIRED_SLOTS: {
    "kra2-c-acting": [
      "primary_output",
      "program_documentation",
      "media_documentation",
      "role_certification"
    ],
    "kra2-c-arch-design": [
      "primary_output",
      "invitation_acceptance",
      "exhibition_documentation",
      "authorship_documentation",
      "organizing_body_info"
    ],
    "kra2-c-choreo-co": ["primary_output", "contribution_certificate"],
    "kra2-c-choreo-sole": [
      "primary_output",
      "invitation_acceptance",
      "performance_proof",
      "role_certification"
    ],
    "kra2-c-conducting": ["primary_output", "invitation_acceptance", "role_certification"],
    "kra2-c-dance-perf": ["primary_output", "role_certification"],
    "kra2-c-directing": [
      "primary_output",
      "program_documentation",
      "media_documentation",
      "role_certification"
    ],
    "kra2-c-essay": ["primary_output", "editorial_review", "publisher_credibility"],
    "kra2-c-film": [
      "primary_output",
      "invitation_acceptance",
      "festival_program",
      "role_certification"
    ],
    "kra2-c-music-arr-co": ["primary_output", "contribution_certificate"],
    "kra2-c-music-arr-sole": [
      "primary_output",
      "invitation_acceptance",
      "performance_proof",
      "role_certification"
    ],
    "kra2-c-music-comp-co": ["primary_output", "contribution_certificate"],
    "kra2-c-music-comp-sole": ["primary_output", "invitation_acceptance", "performance_proof"],
    "kra2-c-music-perf": ["primary_output", "invitation_acceptance", "role_certification"],
    "kra2-c-music-prod-co": ["primary_output", "contribution_certificate"],
    "kra2-c-music-prod-sole": [
      "primary_output",
      "copyright_registration",
      "published_release",
      "role_certification"
    ],
    "kra2-c-novel-co": ["primary_output", "contribution_certificate"],
    "kra2-c-novel-sole": ["primary_output", "editorial_review", "publisher_credibility"],
    "kra2-c-playwright-co": ["primary_output", "contribution_certificate"],
    "kra2-c-playwright-sole": [
      "primary_output",
      "copyright_registration",
      "invitation_acceptance",
      "production_proof",
      "role_certification"
    ],
    "kra2-c-poetry": ["primary_output", "editorial_review", "publisher_credibility"],
    "kra2-c-prod-design": [
      "primary_output",
      "design_portfolio",
      "media_documentation",
      "program_documentation",
      "role_certification"
    ],
    "kra2-c-story-co": ["primary_output", "contribution_certificate"],
    "kra2-c-story-sole": ["primary_output", "editorial_review", "publisher_credibility"],
    "kra2-c-visual": [
      "primary_output",
      "invitation_acceptance",
      "exhibition_catalog",
      "gallery_documentation",
      "role_certification"
    ]
  },

  CRITERION_B_SLOT_LABELS: {
    invention_photo: "Photo of the invention or design",
    president_special_order: "Special Order signed by the President",
    product_photo: "Photo of the patented product",
    patent_certificate: "Invention Patent Certificate",
    licensing_or_cpr_evidence: "CPR or licensing agreement",
    commercialization_proof: "Proof of commercialization",
    rd_itso_certification: "Research Director / ITSO certification",
    project_summary: "Project summary",
    software_documentation: "User manual or design documentation",
    utilization_certification: "End-user utilization certification",
    software_update_description: "Description of substantial new functionalities",
    registration_deposit_evidence: "Registration or deposit evidence"
  },

  CRITERION_C_SLOT_LABELS: {
    authorship_documentation: "Authorship documentation",
    contribution_certificate: "Certificate of Contribution — Creative Works (Annex I)",
    copyright_registration: "Copyright registration",
    design_portfolio: "Design portfolio or proposal",
    editorial_review: "Publisher guidelines and editorial review evidence",
    exhibition_catalog: "Exhibition catalog, brochure, or program",
    exhibition_documentation: "Exhibition or competition documentation",
    festival_program: "Festival program or screening announcement",
    gallery_documentation: "Gallery or venue information",
    invitation_acceptance: "Proof of invitation or acceptance",
    media_documentation: "Photo or video documentation",
    organizing_body_info: "Organizing body or gallery profile",
    performance_proof: "Proof of performance or first performance",
    production_proof: "Proof of production or staging",
    program_documentation: "Program, playbill, or event flyer",
    published_release: "Published release or distribution details",
    publisher_credibility: "Proof of publisher credibility",
    role_certification: "Certification of role (director, organizer, dean, etc.)"
  },

  facultyStatusMeta: function (bundle) {
    var rs = FL.kra2AWorkspaceUi.normalizeReviewStatus({ bundle: bundle });
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

  /** Authoritative review status from API bundle (not stale validation labels). */
  normalizeReviewStatus: function (state) {
    var bundle = (state && state.bundle) || {};
    var validation = (state && state.validation) || {};
    var ra = bundle.reviewerAssessment || {};
    var candidates = [
      bundle.reviewStatus,
      ra.reviewStatus,
      validation.reviewStatus,
      state && state.doc && state.doc.reviewStatus
    ];
    for (var i = 0; i < candidates.length; i++) {
      var raw = (candidates[i] || "").toString().trim().toLowerCase();
      if (raw === "approved" || raw === "rejected" || raw === "pending") return raw;
    }
    if (bundle.submittedForReviewAt) return "pending";
    return "pending";
  },

  isAccomplishmentApproved: function (state) {
    return FL.kra2AWorkspaceUi.normalizeReviewStatus(state) === "approved";
  },

  isAccomplishmentRejected: function (state) {
    return FL.kra2AWorkspaceUi.normalizeReviewStatus(state) === "rejected";
  },

  isReviewDecisionLocked: function (state) {
    return FL.kra2AWorkspaceUi.isAccomplishmentApproved(state);
  },

  reassessmentCapabilitiesFor: function (state) {
    return (
      state.reassessmentCapabilities ||
      (state.payload && state.payload.reassessmentCapabilities) ||
      {}
    );
  },

  reassessmentSessionFor: function (state) {
    var bundle = state.bundle || {};
    return bundle.reassessmentSession || (state.payload && state.payload.reassessmentSession) || null;
  },

  isReassessmentSessionActive: function (state) {
    var session = FL.kra2AWorkspaceUi.reassessmentSessionFor(state);
    return !!(session && session.active);
  },

  isPendingSubmittedReview: function (state) {
    var bundle = (state && state.bundle) || {};
    if (!bundle.submittedForReviewAt) return false;
    if (FL.kra2AWorkspaceUi.isAccomplishmentApproved(state)) return false;
    if (FL.kra2AWorkspaceUi.isAccomplishmentRejected(state)) return false;
    return true;
  },

  canEditReviewerAssessment: function (state) {
    var bundle = (state && state.bundle) || {};
    if (!bundle.submittedForReviewAt || !state.canDecide) return false;
    if (FL.kra2AWorkspaceUi.isReassessmentSessionActive(state)) return false;
    return true;
  },

  pendingApprovalBlockersHtml: function (state) {
    var esc = FL.esc;
    var v = state.validation || {};
    var blockers = FL.kra2AWorkspaceUi.mergeValidationMessages(v);
    if (!blockers.length) return "";
    var indicatorId = FL.kra2AWorkspaceUi.resolveIndicatorId(state.bundle, state.payload, state.doc);
    var rows = blockers.map(function (b) {
      var slotMatch = (b || "").match(/Verify supporting evidence:\s*(.+)\./i);
      if (slotMatch && slotMatch[1]) {
        var label = slotMatch[1].trim();
        var slotId = null;
        var labels = (state.payload && state.payload.slotLabels) || {};
        Object.keys(labels).forEach(function (sid) {
          if (labels[sid] === label) slotId = sid;
        });
        if (slotId) {
          return (
            '<li class="kra2-checklist-blocker">' +
            esc(b) +
            ' <button type="button" class="btn btn-ghost btn-small kra2-goto-slot" data-slot="' +
            esc(slotId) +
            '">Go to evidence</button></li>'
          );
        }
      }
      return '<li class="kra2-checklist-blocker">' + esc(b) + "</li>";
    });
    return (
      '<div class="kra2-pending-blockers">' +
      "<h3 class=\"kra2-subheading\">Before you can approve</h3>" +
      '<p class="muted">You can still save your assessed points and feedback while these items are outstanding.</p>' +
      '<ul class="cc-blocker-list">' +
      rows.join("") +
      "</ul></div>"
    );
  },

  authoritativeEligiblePoints: function (scoring) {
    scoring = scoring || {};
    if (scoring.reviewerEligiblePoints != null) return scoring.reviewerEligiblePoints;
    if (scoring.maxAssessedPoints != null) return scoring.maxAssessedPoints;
    if (scoring.eligiblePoints != null) return scoring.eligiblePoints;
    if (scoring.systemCalculatedPoints != null) return scoring.systemCalculatedPoints;
    return scoring.estimatedPoints;
  },

  unifiedReviewerAssessmentHtml: function (state) {
    var esc = FL.esc;
    var scoring = state.scoring || {};
    var bundle = state.bundle || {};
    var ra = bundle.reviewerAssessment || {};
    var status = FL.kra2AWorkspaceUi.normalizeReviewStatus(state);
    var statusLabel =
      status === "approved" ? "Approved" : status === "rejected" ? "Rejected" : "Pending review";
    var showApproveActions = FL.kra2AWorkspaceUi.isPendingSubmittedReview(state);
    var systemPts = FL.kra2AWorkspaceUi.authoritativeEligiblePoints(scoring);
    var formulaPts =
      scoring.formulaCalculatedPoints != null
        ? scoring.formulaCalculatedPoints
        : scoring.systemCalculatedPoints != null &&
            systemPts != null &&
            Math.abs(parseFloat(scoring.systemCalculatedPoints, 10) - parseFloat(systemPts, 10)) > 0.001
          ? scoring.systemCalculatedPoints
          : null;
    var approvedPts = scoring.approvedPoints != null ? scoring.approvedPoints : ra.approvedPoints;
    var assessed = scoring.reviewerAssessedPoints;
    if (assessed == null && ra.draftAssessedPoints != null) assessed = ra.draftAssessedPoints;
    if (assessed == null && status === "approved" && approvedPts != null) assessed = approvedPts;
    if (assessed == null && ra.assessedPoints != null) assessed = ra.assessedPoints;
    var finalPts = assessed != null ? assessed : systemPts;
    var numericBlocked = !!scoring.numericScoringBlocked;
    var pointsEditable = !numericBlocked && systemPts != null;
    var assessableMax =
      scoring.maxAssessedPoints != null
        ? scoring.maxAssessedPoints
        : scoring.indicatorMaxPoints != null
          ? scoring.indicatorMaxPoints
          : systemPts;
    var adjustmentReason = (
      scoring.scoreAdjustmentReason ||
      ra.draftScoreAdjustmentReason ||
      ra.scoreAdjustmentReason ||
      ""
    ).toString();
    var feedbackText =
      scoring.draftReviewerRemarks != null && String(scoring.draftReviewerRemarks).trim()
        ? scoring.draftReviewerRemarks
        : state.remarks ||
          scoring.finalizedReviewerRemarks ||
          bundle.reviewerRemarks ||
          ra.draftRemarks ||
          ra.remarks ||
          "";

    var assessedInput =
      '<label class="kra2-scoring-label kra2-scoring-label--primary" for="kra2-assessed-points">' +
      "Reviewer-assessed points" +
      (assessableMax != null && pointsEditable
        ? ' <span class="muted">(max ' + esc(String(assessableMax)) + ")</span>"
        : "") +
      '<input type="number" id="kra2-assessed-points" class="kra2-scoring-input"' +
      (pointsEditable ? "" : ' readonly="readonly"') +
      ' min="0"' +
      (assessableMax != null ? ' max="' + esc(String(assessableMax)) + '"' : "") +
      ' step="0.01" value="' +
      esc(finalPts != null && finalPts !== "" ? String(finalPts) : "") +
      '"></label>';
    if (numericBlocked) {
      assessedInput +=
        '<p class="muted kra2-scoring-fixed-note">' +
        esc(
          scoring.numericScoringBlockerMessage ||
            "Numeric score approval is blocked until published designation scoring is verified."
        ) +
        "</p>";
    }

    var finalizedNote = "";
    if (status === "approved") {
      finalizedNote =
        '<p class="muted kra2-assessment-finalized-note" id="kra2-assessment-finalized-note">' +
        "Saved assessment changes do not change approved points until a correction is finalized through reassessment." +
        "</p>";
    } else if (status === "rejected") {
      finalizedNote =
        '<p class="muted kra2-assessment-finalized-note">' +
        "Saving updates your assessment draft only. Rejection status and faculty resubmission rules are unchanged." +
        "</p>";
    }

    var decisionActions =
      '<div class="cc-decision-actions kra2-decision-actions">' +
      '<button type="button" class="btn btn-ghost" id="kra2-save-assessment">Save Assessment</button>' +
      '<span class="cc-save-indicator" id="kra2-save-assessment-indicator"></span>';
    if (showApproveActions) {
      decisionActions +=
        '<button type="button" class="btn btn-primary" id="kra2-approve">Approve</button>' +
        '<p class="muted kra2-approve-hint" id="kra2-approve-hint"></p>' +
        '<button type="button" class="btn btn-ghost" id="kra2-reject">Reject</button>';
    }
    decisionActions += "</div>";

    return (
      '<div class="kra2-unified-assessment">' +
      '<div class="kra2-scoring-row"><span>Status</span><strong>' + esc(statusLabel) + "</strong></div>" +
      (approvedPts != null
        ? '<div class="kra2-scoring-row kra2-scoring-row--approved"><span>Current approved points</span><strong>' +
          esc(String(approvedPts)) +
          "</strong></div>"
        : "") +
      (numericBlocked && scoring.numericScoringBlockerMessage
        ? '<div class="kra2-scoring-blocker-banner" role="status">' +
          esc(scoring.numericScoringBlockerMessage) +
          "</div>"
        : "") +
      '<div class="kra2-scoring-row kra2-scoring-row--highlight">' +
      "<span>System-calculated eligible points</span>" +
      "<strong class=\"kra2-system-points\" id=\"kra2-system-points-display\">" +
      esc(systemPts != null ? String(systemPts) : "—") +
      "</strong></div>" +
      (formulaPts != null
        ? '<p class="muted">Formula output before official cap: ' + esc(String(formulaPts)) + " pts</p>"
        : "") +
      '<strong class="kra2-final-points sr-only" id="kra2-final-points-display">' +
      esc(finalPts != null ? String(finalPts) : "—") +
      "</strong>" +
      assessedInput +
      '<label class="kra2-scoring-label" for="kra2-score-adjustment-reason">Reason for score adjustment' +
      '<span class="muted"> (required when assessed points differ from eligible amount)</span>' +
      '<textarea id="kra2-score-adjustment-reason" rows="2" class="kra2-scoring-textarea">' +
      esc(adjustmentReason) +
      "</textarea></label>" +
      '<label class="kra2-remarks-label" for="kra2-remarks">Reviewer feedback' +
      '<textarea id="kra2-remarks" rows="4" class="kra2-remarks-input" placeholder="Explain acceptance, required corrections, or general assessment remarks.">' +
      esc(feedbackText) +
      "</textarea></label>" +
      finalizedNote +
      decisionActions +
      "</div>"
    );
  },

  unifiedPendingReviewerAssessmentHtml: function (state) {
    return FL.kra2AWorkspaceUi.unifiedReviewerAssessmentHtml(state);
  },

  reassessmentRequestSupplementHtml: function (state) {
    if (!FL.kra2AWorkspaceUi.isAccomplishmentApproved(state)) return "";
    if (FL.kra2AWorkspaceUi.isReassessmentSessionActive(state)) return "";
    var esc = FL.esc;
    var reopen = FL.kra2AWorkspaceUi.canOpenReassessment(state);
    if (reopen.allowed) {
      var actionLabel = reopen.actionLabel || "Request Reassessment";
      return (
        '<div class="kra2-reassessment-open kra2-scoring-panel">' +
        "<h3 class=\"kra2-subheading\">Finalize a score correction</h3>" +
        '<p class="muted">Use reassessment when a saved assessment revision should replace approved points on record.</p>' +
        '<label class="kra2-remarks-label" for="kra2-reassessment-reason">Reason for reassessment (required, at least 20 characters)' +
        '<textarea id="kra2-reassessment-reason" rows="3" class="kra2-remarks-input" placeholder="Explain why the approved score or feedback must be corrected."></textarea></label>' +
        '<button type="button" class="btn btn-primary" id="kra2-start-reassessment">' +
        esc(actionLabel) +
        "</button>" +
        (reopen.canFinalize
          ? ""
          : '<p class="muted">An administrator must finalize reassessment unless your role can finalize directly.</p>') +
        "</div>"
      );
    }
    if (reopen.message) {
      return '<p class="muted kra2-reassessment-hint">' + esc(reopen.message) + "</p>";
    }
    return "";
  },

  canOpenReassessment: function (state) {
    if (!FL.kra2AWorkspaceUi.isAccomplishmentApproved(state)) {
      return { allowed: false, message: "Reassessment applies only after approval." };
    }
    if (FL.kra2AWorkspaceUi.isReassessmentSessionActive(state)) {
      return { allowed: false, message: "A reassessment session is already open." };
    }
    var caps = FL.kra2AWorkspaceUi.reassessmentCapabilitiesFor(state);
    if (!caps.canRequestReassessment) {
      return {
        allowed: false,
        message: "You are not assigned to review this accomplishment."
      };
    }
    return {
      allowed: true,
      message: "",
      actionLabel: caps.actionLabel || "Request Reassessment",
      canFinalize: !!caps.canFinalizeReassessment
    };
  },

  syncReviewStatusFields: function (state) {
    if (!state) return;
    var rs = FL.kra2AWorkspaceUi.normalizeReviewStatus(state);
    if (state.bundle && typeof state.bundle === "object") state.bundle.reviewStatus = rs;
    if (state.validation && typeof state.validation === "object") state.validation.reviewStatus = rs;
  },

  kraReviewPageTitle: function (state) {
    var crit =
      (state && state.doc && state.doc.criterionId) ||
      (state && state.bundle && state.bundle.criterionId) ||
      "";
    if (String(crit).indexOf("kra3-") === 0) return "KRA III accomplishment review";
    return "KRA II accomplishment review";
  },

  resolveIndicatorId: function (bundle, payload, doc) {
    return (
      (bundle && bundle.indicatorId) ||
      (payload && payload.effectiveIndicatorId) ||
      (payload && payload.scoring && payload.scoring.indicatorId) ||
      (doc && doc.indicatorId) ||
      ""
    )
      .trim();
  },

  criterionARequiredSlots: function (indicatorId) {
    var ind = (indicatorId || "").trim();
    if (!ind || ind.indexOf("kra2-a-") !== 0) return null;
    var slots = FL.kra2AWorkspaceUi.CRITERION_A_REQUIRED_SLOTS[ind];
    return slots ? slots.slice() : null;
  },

  criterionBRequiredSlots: function (indicatorId) {
    var ind = (indicatorId || "").trim();
    if (!ind || ind.indexOf("kra2-b-") !== 0) return null;
    var slots = FL.kra2AWorkspaceUi.CRITERION_B_REQUIRED_SLOTS[ind];
    return slots ? slots.slice() : null;
  },

  criterionCRequiredSlots: function (indicatorId) {
    var ind = (indicatorId || "").trim();
    if (!ind || ind.indexOf("kra2-c-") !== 0) return null;
    var slots = FL.kra2AWorkspaceUi.CRITERION_C_REQUIRED_SLOTS[ind];
    return slots ? slots.slice() : null;
  },

  slotLabelForIndicator: function (slotId, indicatorId, payload) {
    if (payload && payload.slotLabels && payload.slotLabels[slotId]) {
      return payload.slotLabels[slotId];
    }
    var ind = (indicatorId || "").trim();
    if (ind.indexOf("kra2-a-") === 0) {
      if (slotId === "primary_output") {
        if (ind.indexOf("book") >= 0 || ind.indexOf("monograph") >= 0) return "Published book (PDF)";
        if (ind.indexOf("chapter") >= 0) return "Published chapter (PDF)";
        if (ind.indexOf("journal") >= 0) return "Published article (PDF)";
        if (ind.indexOf("translation") >= 0) return "Research output (PDF)";
        if (ind.indexOf("cite") >= 0) return "Your cited article (PDF)";
      }
      if (slotId === "peer_review_evidence") return "Peer review and academic press evidence";
      if (slotId === "contribution_certificate") {
        return ind.indexOf("translation") >= 0
          ? "Certificate of Contribution (Annex E)"
          : "Certificate of Contribution (Annex D)";
      }
    }
    if (ind.indexOf("kra2-b-") === 0) {
      if (slotId === "primary_output") {
        if (ind.indexOf("patent") >= 0) return "IPOPHL patent stage document";
        if (ind.indexOf("comm-") >= 0) return "Commercialization evidence (PDF)";
        if (ind.indexOf("sw-") >= 0) return "Copyright certificate (IPOPHL)";
        if (ind.indexOf("um-") >= 0 || ind.indexOf("id-") >= 0) return "Registration certificate";
        if (ind.indexOf("variety") >= 0) return "Registration or deposit evidence";
      }
      if (slotId === "contribution_certificate") {
        if (ind.indexOf("sw-") >= 0) return "Certificate of Contribution (Annex G)";
        if (ind.indexOf("variety") >= 0) return "Certificate of Contribution (Annex H)";
        return "Certificate of Contribution (Annex F)";
      }
      if (FL.kra2AWorkspaceUi.CRITERION_B_SLOT_LABELS[slotId]) {
        return FL.kra2AWorkspaceUi.CRITERION_B_SLOT_LABELS[slotId];
      }
    }
    return FL.kra2AWorkspaceUi.SLOT_LABELS[slotId] || slotId.replace(/_/g, " ");
  },

  publicationOutputKind: function (indicatorId) {
    var ind = (indicatorId || "").trim();
    if (ind.indexOf("book") >= 0 || ind.indexOf("monograph") >= 0) return "book";
    if (ind.indexOf("chapter") >= 0) return "chapter";
    if (ind.indexOf("journal") >= 0) return "journal";
    if (ind.indexOf("translation") >= 0) return "translation";
    if (ind.indexOf("cite") >= 0) return "citation";
    return "publication";
  },

  venueFieldLabel: function (indicatorId) {
    var kind = FL.kra2AWorkspaceUi.publicationOutputKind(indicatorId);
    if (kind === "book" || kind === "chapter") return "Publisher";
    if (kind === "journal") return "Journal";
    return "Venue / registry";
  },

  indicatorLabel: function (indicatorId, bundle) {
    var ind = (indicatorId || "").trim();
    if (bundle && bundle.indicatorTitle) return String(bundle.indicatorTitle).trim();
    if (FL.rules && FL.rules.findIndicator) {
      var hit = FL.rules.findIndicator(ind);
      if (hit && hit.indicator && hit.indicator.name) return hit.indicator.name;
    }
    if (ind.indexOf("book") >= 0) return "Academic book";
    if (ind.indexOf("monograph") >= 0) return "Monograph";
    if (ind.indexOf("chapter") >= 0) return "Book chapter";
    if (ind.indexOf("journal") >= 0) return "Journal article";
    if (ind.indexOf("translation") >= 0) return "Translation";
    if (ind.indexOf("cite") >= 0) return "Citation impact";
    if (ind.indexOf("kra2-b-patent") >= 0) return "Invention patent";
    if (ind.indexOf("kra2-b-comm") >= 0) return "Commercialized patented product";
    if (ind.indexOf("kra2-b-um") >= 0) return "Utility model";
    if (ind.indexOf("kra2-b-id") >= 0) return "Industrial design";
    if (ind.indexOf("kra2-b-sw") >= 0) return "Copyrighted software";
    if (ind.indexOf("kra2-b-variety") >= 0) return "Plant variety / breed / microbial strain";
    return ind ? ind.replace(/^kra2-[abc]-/, "").replace(/-/g, " ") : "Accomplishment";
  },

  requiredSlotIds: function (bundle, payload) {
    payload = payload || {};
    if (Array.isArray(payload.requiredEvidenceSlots) && payload.requiredEvidenceSlots.length) {
      return payload.requiredEvidenceSlots.slice();
    }
    var indicatorId = FL.kra2AWorkspaceUi.resolveIndicatorId(bundle, payload);
    var critA = FL.kra2AWorkspaceUi.criterionARequiredSlots(indicatorId);
    if (critA) return critA;
    var critB = FL.kra2AWorkspaceUi.criterionBRequiredSlots(indicatorId);
    if (critB) return critB;
    var critC = FL.kra2AWorkspaceUi.criterionCRequiredSlots(indicatorId);
    if (critC) return critC;
    var contribution = bundle && bundle.contribution;
    if ((contribution || "").toLowerCase() === "declared") {
      return ["primary_output", "contribution_certificate"];
    }
    return ["primary_output"];
  },

  buildEvidenceSlotItems: function (bundle, primaryDoc, slotIds, options) {
    options = options || {};
    var checklist = (bundle && bundle.checklist) || {};
    var docById = options.docById || {};
    var indicatorId = FL.kra2AWorkspaceUi.resolveIndicatorId(bundle, options.payload, primaryDoc);
    return (slotIds || []).map(function (slotId) {
      var entry = checklist[slotId] || {};
      var docId = entry.documentId || "";
      var label = FL.kra2AWorkspaceUi.slotLabelForIndicator(slotId, indicatorId, options.payload);
      var status = entry.status || "missing";
      var fileName = "Not uploaded";
      if (docId) {
        var linked = docById[docId];
        if (linked) {
          fileName = linked.fileName || linked.title || fileName;
        } else if (primaryDoc && docId === primaryDoc.id) {
          fileName = primaryDoc.fileName || primaryDoc.title || docId;
        } else {
          fileName = docId;
        }
      }
      var isPrimary = !!(primaryDoc && docId && docId === primaryDoc.id);
      return {
        slotId: slotId,
        label: label,
        status: status,
        documentId: docId,
        fileName: fileName,
        isPrimary: isPrimary,
        previewUrl: isPrimary && primaryDoc ? primaryDoc.fileUrl : null
      };
    });
  },

  humanizeBlocker: function (text) {
    var map = {
      "Title of the research output is required.": "Article title is missing.",
      "Journal or publication venue is required.": "Publisher or journal name is missing.",
      "Publisher or publication venue is required.": "Publisher name is missing.",
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
    summary = summary || {};
    var validated = summary.validatedPoints != null ? summary.validatedPoints : 0;
    var estimated = summary.estimatedPoints != null ? summary.estimatedPoints : "—";
    var max = summary.maxPoints != null ? summary.maxPoints : 100;
    return (
      "Estimated " +
      String(estimated) +
      " · Verified " +
      String(validated) +
      " / " +
      String(max) +
      " pts (criterion cap)"
    );
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
            var title = row.activityTitle || row.outputTitle || row.title || "Accomplishment";
            var submitted = FL.kra2AWorkspaceUi.formatSubmittedDate(row);
            var href = params.reviewHref(row);
            var verified =
              row.validatedPoints != null
                ? row.validatedPoints
                : row.reviewStatus === "approved" && row.reviewerAssessedPoints != null
                  ? row.reviewerAssessedPoints
                  : "—";
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
              FL.documents.kvRow("Verified points", esc(String(verified))) +
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

  scoringRuleLine: function (scoring, doc, bundle) {
    var ind =
      (scoring && scoring.indicatorId) ||
      FL.kra2AWorkspaceUi.resolveIndicatorId(bundle, null, doc) ||
      (doc && doc.indicatorId) ||
      "";
    var label = FL.kra2AWorkspaceUi.indicatorLabel(ind, bundle);
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
    FL.kra2AWorkspaceUi.syncReviewStatusFields(state);
    var esc = FL.esc;
    var bundle = state.bundle || {};
    var doc = state.doc || {};
    var scoring = state.scoring || {};
    var statusMeta = FL.kra2AWorkspaceUi.facultyStatusMeta(bundle);
    var indicatorId = FL.kra2AWorkspaceUi.resolveIndicatorId(bundle, state.payload, doc);
    var indLabel = FL.kra2AWorkspaceUi.indicatorLabel(indicatorId, bundle);
    var venueLabel = FL.kra2AWorkspaceUi.venueFieldLabel(indicatorId);
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
      FL.documents.kvRow(venueLabel, esc(bundle.outputVenue || bundle.journalTitle || "—")) +
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
      FL.documents.kvRow(
        "Official scoring rule",
        esc(FL.kra2AWorkspaceUi.scoringRuleLine(scoring, doc, bundle))
      ) +
      "</dl></section>";

    var primaryDocLabel = doc.fileName || doc.title || bundle.outputTitle || "Primary document";
    var docsHtml = FL.kra2AWorkspaceUi.evidenceCardsHtml(state);
    var previewHtml =
      '<section class="card cc-compact-section kra2-section-documents">' +
      "<h2>Supporting documents</h2>" +
      '<h3 class="kra2-subheading">Document preview</h3>' +
      '<p class="muted kra2-preview-active-label" id="kra2-preview-doc-label">Showing: ' +
      esc(primaryDocLabel) +
      "</p>" +
      '<div class="original-file-frame kra2-doc-preview-frame" data-doc-preview-id="' +
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
      "<h1>" +
      esc(FL.kra2AWorkspaceUi.kraReviewPageTitle(state)) +
      "</h1>" +
      '<p class="sub">' +
      esc(state.facultyName || "Faculty") +
      " · " +
      esc(indLabel) +
      '</p><p class="kra2-review-status kra2-review-status--' +
      esc(statusMeta.key) +
      '"><strong>Status:</strong> ' +
      esc(statusMeta.label) +
      " — " +
      esc(statusMeta.hint) +
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
      var perfTokens = {
        "music-perf": 1,
        "dance-perf": 1,
        conducting: 1,
        acting: 1,
        directing: 1
      };
      if (perfTokens[familyToken] || iid.indexOf("-perf") >= 0) return "performance_work";
      return "creative_work";
    }
    return "publication_output";
  },

  criterionCSubfamily: function (indicatorId) {
    var iid = (indicatorId || "").trim();
    if (iid.indexOf("kra2-c-") !== 0) return "literary";
    if (iid.indexOf("kra2-c-music-comp-") === 0 || iid.indexOf("kra2-c-music-arr-") === 0) return "music_composition";
    if (iid.indexOf("kra2-c-music-prod-") === 0) return "music_production";
    if (iid.indexOf("kra2-c-music-perf") === 0 || iid.indexOf("kra2-c-conducting") === 0) return "music_performance";
    if (iid.indexOf("kra2-c-choreo-") === 0) return "dance_choreography";
    if (iid.indexOf("kra2-c-dance-perf") === 0) return "dance_performance";
    if (iid.indexOf("kra2-c-directing") === 0 || iid.indexOf("kra2-c-acting") === 0) return "theater_performance";
    if (iid.indexOf("kra2-c-playwright-") === 0 || iid.indexOf("kra2-c-prod-design") === 0) return "theater";
    if (iid.indexOf("kra2-c-visual") === 0) return "visual_arts";
    if (iid.indexOf("kra2-c-arch-design") === 0) return "design_exhibition";
    if (iid.indexOf("kra2-c-film") === 0) return "film";
    if (
      iid.indexOf("kra2-c-novel-") === 0 ||
      iid.indexOf("kra2-c-story-") === 0 ||
      iid.indexOf("kra2-c-poetry") === 0 ||
      iid.indexOf("kra2-c-essay") === 0
    ) {
      return "literary";
    }
    return "literary";
  },

  criterionCMetadataLabels: function (indicatorId) {
    var sub = FL.kra2AWorkspaceUi.criterionCSubfamily(indicatorId);
    var profiles = {
      music_composition: {
        outputTitle: "Title of composition or arrangement",
        authorsLine: "Composer or arranger",
        outputVenue: "Venue, organizer, or publisher",
        publicationDate: "Date of first performance or publication"
      },
      music_production: {
        outputTitle: "Title of produced work",
        authorsLine: "Producer or creator",
        outputVenue: "Label, platform, or release venue",
        publicationDate: "Release or publication date"
      },
      music_performance: {
        outputTitle: "Title of performance",
        authorsLine: "Performer or conductor",
        outputVenue: "Performance venue or organizer",
        publicationDate: "Date of performance"
      },
      dance_choreography: {
        outputTitle: "Title of choreography",
        authorsLine: "Choreographer",
        outputVenue: "Venue or organizer",
        publicationDate: "Date of first performance"
      },
      dance_performance: {
        outputTitle: "Title of dance performance",
        authorsLine: "Dancer or performer",
        outputVenue: "Performance venue or organizer",
        publicationDate: "Date of performance"
      },
      theater: {
        outputTitle: "Title of production or role",
        authorsLine: "Playwright or creator",
        outputVenue: "Theater, organizer, or festival",
        publicationDate: "Date of production or publication"
      },
      theater_performance: {
        outputTitle: "Title of performance",
        authorsLine: "Performer or director",
        outputVenue: "Performance venue or organizer",
        publicationDate: "Date of performance"
      },
      visual_arts: {
        outputTitle: "Title of artwork",
        authorsLine: "Artist or creator",
        outputVenue: "Gallery or exhibition venue",
        publicationDate: "Exhibition date"
      },
      design_exhibition: {
        outputTitle: "Title of design or project",
        authorsLine: "Designer or creator",
        outputVenue: "Exhibition, competition, or organizer",
        publicationDate: "Exhibition or competition date"
      },
      film: {
        outputTitle: "Film title",
        authorsLine: "Director or creator",
        outputVenue: "Festival, venue, or organizer",
        publicationDate: "Screening or release date"
      },
      literary: {
        outputTitle: "Title of literary work",
        authorsLine: "Author or contributor",
        outputVenue: "Publisher or publication",
        publicationDate: "Publication date"
      }
    };
    return profiles[sub] || profiles.literary;
  },

  metadataFormFields: function (indicatorId) {
    var iid = (indicatorId || "").trim();
    if (iid.indexOf("kra2-c-") === 0) {
      var cLabels = FL.kra2AWorkspaceUi.criterionCMetadataLabels(indicatorId);
      var cFields = [
        { id: "outputTitle", inputId: "kra2-meta-outputTitle", label: cLabels.outputTitle, required: true },
        { id: "authorsLine", inputId: "kra2-meta-authorsLine", label: cLabels.authorsLine, required: true },
        {
          id: "outputVenue",
          inputId: "kra2-meta-outputVenue",
          label: cLabels.outputVenue,
          required: true
        },
        {
          id: "publicationDate",
          inputId: "kra2-meta-publicationDate",
          label: cLabels.publicationDate,
          required: true
        }
      ];
      return cFields;
    }
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
      label: FL.kra2AWorkspaceUi.venueFieldLabel(indicatorId),
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
      label:
        FL.kra2AWorkspaceUi.publicationOutputKind(indicatorId) === "book" ? "ISBN / reference" : "DOI / reference",
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
    if (FL.kra2AWorkspaceUi.isReviewDecisionLocked(state)) {
      return [];
    }
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
    if (!(Array.isArray(v.approvalBlockers) && v.approvalBlockers.length)) {
      var summary = v.checklistSummary || {};
      var indicatorId = FL.kra2AWorkspaceUi.resolveIndicatorId(state.bundle, state.payload, state.doc);
      Object.keys(summary).forEach(function (slot) {
        if (summary[slot] === "verified") return;
        var label = FL.kra2AWorkspaceUi.slotLabelForIndicator(slot, indicatorId, state.payload);
        if (summary[slot] === "missing" || !summary[slot]) {
          add("Please upload: " + label + ".");
        } else {
          add("Verify supporting evidence: " + label + ".");
        }
      });
    }
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
    var bundle = state.bundle || {};
    if (!bundle.submittedForReviewAt) {
      add("Faculty has not submitted this accomplishment for review.");
    }
    var scoring = state.scoring || {};
    if (scoring.numericScoringBlocked) {
      add(
        scoring.numericScoringBlockerMessage ||
          "Numeric score approval is blocked until published designation scoring is verified."
      );
    }
    if (typeof document !== "undefined") {
      var assessedEl = document.getElementById("kra2-assessed-points");
      var reasonEl = document.getElementById("kra2-score-adjustment-reason");
      var systemPts = FL.kra2AWorkspaceUi.authoritativeEligiblePoints(scoring);
      if (assessedEl && systemPts != null && assessedEl.value !== "") {
        var assessedVal = parseFloat(assessedEl.value, 10);
        if (
          !isNaN(assessedVal) &&
          Math.abs(assessedVal - parseFloat(systemPts, 10)) > 0.001 &&
          (!reasonEl || reasonEl.value.trim().length < 10)
        ) {
          add("Explain why your assessed points differ from the system-calculated eligible amount (at least 10 characters).");
        }
      }
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
      "<h3 class=\"kra2-subheading\">Approval requirements</h3>" +
      '<p class="muted kra2-test-notice">Fictional test PDF — confirm metadata explicitly; OCR is advisory only.</p>' +
      '<ul class="cc-blocker-list">' +
      rows +
      "</ul></div>"
    );
  },

  reviewerMetadataPanelHtml: function (state) {
    var esc = FL.esc;
    if (
      !state.canDecide ||
      FL.kra2AWorkspaceUi.isReviewDecisionLocked(state) ||
      !FL.kra2AWorkspaceUi.metadataPanelNeeded(state)
    ) {
      return "";
    }
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
    var canDecide = !!state.canDecide && !FL.kra2AWorkspaceUi.isReviewDecisionLocked(state);
    var items = state.evidenceItems || [];
    var cards = items
      .map(function (item, idx) {
        var statusLabel =
          item.status === "verified"
            ? "Verified"
            : item.status === "missing"
              ? "Missing"
              : "Pending verification";
        var previewBtn = "";
        if (item.documentId) {
          previewBtn =
            '<button type="button" class="btn btn-small btn-ghost" data-kra2-preview-doc="' +
            esc(item.documentId) +
            '" data-kra2-preview-label="' +
            esc(item.label + " — " + item.fileName) +
            '">Preview</button>';
        }
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

  approvedDecisionSectionHtml: function (state) {
    var esc = FL.esc;
    var bundle = state.bundle || {};
    var scoring = state.scoring || {};
    var payload = state.payload || {};
    var ra = bundle.reviewerAssessment || {};
    var approvedPts =
      ra.approvedPoints != null
        ? ra.approvedPoints
        : ra.assessedPoints != null
          ? ra.assessedPoints
          : scoring.reviewerAssessedPoints;
    var version =
      payload.scoringVersion != null
        ? payload.scoringVersion
        : scoring.scoringConfigurationVersion != null
          ? scoring.scoringConfigurationVersion
          : bundle.scoringVersion;
    var remarks = (bundle.reviewerRemarks || ra.remarks || state.remarks || "").trim();
    var assessedAt = ra.assessedAt || "";
    var reviewerName = ra.reviewerDisplayName || "";
    var systemPts =
      scoring.systemCalculatedPoints != null
        ? scoring.systemCalculatedPoints
        : scoring.estimatedPoints;

    var mismatchNote = "";
    if (
      approvedPts != null &&
      systemPts != null &&
      Math.abs(parseFloat(approvedPts, 10) - parseFloat(systemPts, 10)) > 0.001
    ) {
      mismatchNote =
        '<p class="muted kra2-score-mismatch-note">Approved points differ from the current system-calculated eligible amount. ' +
        "This may reflect an intentional reviewer adjustment or a legacy scoring calculation. " +
        "Use authorized reassessment to correct the approved record without losing audit history.</p>";
    }
    var reopen = FL.kra2AWorkspaceUi.canOpenReassessment(state);
    var reassessControls = "";
    if (FL.kra2AWorkspaceUi.isReassessmentSessionActive(state)) {
      reassessControls = FL.kra2AWorkspaceUi.reassessmentActivePanelHtml(state);
    } else if (reopen.allowed) {
      var actionLabel = reopen.actionLabel || "Request Reassessment";
      reassessControls =
        '<div class="kra2-reassessment-open">' +
        '<p class="muted">The approved score stays on record until a reassessment is finalized.</p>' +
        '<label class="kra2-remarks-label" for="kra2-reassessment-reason">Reason for reassessment (required, at least 20 characters)' +
        '<textarea id="kra2-reassessment-reason" rows="3" class="kra2-remarks-input" placeholder="Explain why the approved score or feedback must be corrected."></textarea></label>' +
        '<button type="button" class="btn btn-primary" id="kra2-start-reassessment">' +
        esc(actionLabel) +
        "</button>" +
        (reopen.canFinalize
          ? ""
          : '<p class="muted">After you enter a corrected score, an administrator must finalize the reassessment.</p>') +
        "</div>";
    } else if (!reopen.allowed && FL.kra2AWorkspaceUi.isAccomplishmentApproved(state)) {
      reassessControls =
        '<p class="muted kra2-reassessment-hint">' + esc(reopen.message || "") + "</p>";
    }

    return (
      '<section class="card cc-compact-section cc-decision-section kra2-complete-review kra2-complete-review--approved">' +
      "<h2>Review decision</h2>" +
      '<div class="kra2-approved-banner" role="status">' +
      '<p class="kra2-approved-banner__title">Approved</p>' +
      '<p class="muted">This accomplishment is finalized. Use reassessment only when an authorized correction is required.</p>' +
      "</div>" +
      '<dl class="kv-grid kv-grid--compact kra2-approved-summary">' +
      FL.documents.kvRow("Status", "Approved") +
      FL.documents.kvRow(
        "Approved points",
        approvedPts != null ? esc(String(approvedPts)) : "—"
      ) +
      FL.documents.kvRow(
        "System-calculated eligible points",
        systemPts != null ? esc(String(systemPts)) : "—"
      ) +
      FL.documents.kvRow(
        "Published scoring version",
        version != null && version !== "" ? esc(String(version)) : "—"
      ) +
      FL.documents.kvRow("Reviewer feedback", remarks ? esc(remarks) : "—") +
      (ra.scoreAdjustmentReason
        ? FL.documents.kvRow("Score adjustment reason", esc(String(ra.scoreAdjustmentReason)))
        : "") +
      (reviewerName ? FL.documents.kvRow("Reviewed by", esc(reviewerName)) : "") +
      (assessedAt ? FL.documents.kvRow("Approved on", esc(assessedAt)) : "") +
      "</dl>" +
      mismatchNote +
      reassessControls +
      "</section>"
    );
  },

  reassessmentActivePanelHtml: function (state) {
    var esc = FL.esc;
    var scoring = state.scoring || {};
    var session = FL.kra2AWorkspaceUi.reassessmentSessionFor(state) || {};
    var prior = session.priorApproval || {};
    var systemPts =
      scoring.systemCalculatedPoints != null
        ? scoring.systemCalculatedPoints
        : prior.systemCalculatedPoints != null
          ? prior.systemCalculatedPoints
          : scoring.estimatedPoints;
    var draftPts =
      session.draftAssessedPoints != null ? session.draftAssessedPoints : prior.approvedPoints;
    var draftRemarks = session.draftRemarks != null ? session.draftRemarks : state.remarks || "";
    var draftReason = session.draftScoreAdjustmentReason || "";
    var allowsAdjust = !!scoring.allowsPointAdjustment;
    var assessableMax = scoring.maxAssessedPoints != null ? scoring.maxAssessedPoints : systemPts;
    var caps = FL.kra2AWorkspaceUi.reassessmentCapabilitiesFor(state);
    var canFinalize = !!caps.canFinalizeReassessment;
    var summaryHtml =
      '<div class="kra2-reassessment-summary" id="kra2-reassessment-summary">' +
      "<h4 class=\"kra2-subheading\">Confirmation summary</h4>" +
      "<ul class=\"cc-blocker-list\">" +
      "<li>Original approved points: <strong>" +
      esc(prior.approvedPoints != null ? String(prior.approvedPoints) : "—") +
      "</strong></li>" +
      "<li>Corrected points: <strong id=\"kra2-reassess-summary-points\">" +
      esc(draftPts != null ? String(draftPts) : "—") +
      "</strong></li>" +
      "<li>System-calculated eligible: <strong>" +
      esc(systemPts != null ? String(systemPts) : "—") +
      "</strong></li>" +
      "</ul></div>";

    return (
      '<div class="kra2-reassessment-panel">' +
      '<h3 class="kra2-subheading">Authorized reassessment</h3>' +
      '<p class="muted">Original approval is preserved in history until you finalize this correction.</p>' +
      '<dl class="kv-grid kv-grid--compact">' +
      FL.documents.kvRow("Reason for reopening", esc(session.openReason || "—")) +
      FL.documents.kvRow(
        "Original approved points",
        prior.approvedPoints != null ? esc(String(prior.approvedPoints)) : "—"
      ) +
      FL.documents.kvRow(
        "Original approved on",
        prior.assessedAt ? esc(String(prior.assessedAt)) : "—"
      ) +
      "</dl>" +
      '<div class="kra2-scoring-row kra2-scoring-row--highlight"><span>System-calculated eligible points</span><strong>' +
      esc(systemPts != null ? String(systemPts) : "—") +
      "</strong></div>" +
      (allowsAdjust
        ? '<label class="kra2-scoring-label" for="kra2-reassess-points">Corrected assessed points' +
          '<input type="number" id="kra2-reassess-points" class="kra2-scoring-input" min="0" max="' +
          esc(assessableMax != null ? String(assessableMax) : "") +
          '" step="0.01" value="' +
          esc(draftPts != null ? String(draftPts) : "") +
          '"></label>' +
          '<label class="kra2-scoring-label" for="kra2-reassess-adjustment-reason">Reason for score adjustment' +
          '<textarea id="kra2-reassess-adjustment-reason" rows="2" class="kra2-scoring-textarea">' +
          esc(draftReason) +
          "</textarea></label>"
        : '<input type="hidden" id="kra2-reassess-points" value="' +
          esc(systemPts != null ? String(systemPts) : "") +
          '">') +
      '<label class="kra2-remarks-label" for="kra2-reassess-remarks">Updated reviewer feedback' +
      '<textarea id="kra2-reassess-remarks" rows="4" class="kra2-remarks-input">' +
      esc(draftRemarks) +
      "</textarea></label>" +
      summaryHtml +
      (canFinalize
        ? '<label class="kra2-confirm-label"><input type="checkbox" id="kra2-reassess-confirm"> I confirm this reassessment should replace the approved score.</label>'
        : '<p class="muted">Save your corrected score and feedback. An administrator must finalize this reassessment.</p>') +
      '<div class="cc-decision-actions kra2-decision-actions">' +
      '<button type="button" class="btn btn-ghost" id="kra2-reassess-save">Save reassessment draft</button>' +
      (canFinalize
        ? '<button type="button" class="btn btn-primary" id="kra2-reassess-finalize">Finalize reassessment</button>'
        : "") +
      '<button type="button" class="btn btn-ghost" id="kra2-reassess-cancel">Cancel reassessment</button>' +
      "</div></div>"
    );
  },

  rejectedDecisionSectionHtml: function (state) {
    var esc = FL.esc;
    var bundle = state.bundle || {};
    var ra = bundle.reviewerAssessment || {};
    var scoring = state.scoring || {};
    var remarks = (bundle.reviewerRemarks || ra.remarks || state.remarks || "").trim();
    var systemPts =
      scoring.systemCalculatedPoints != null
        ? scoring.systemCalculatedPoints
        : ra.systemCalculatedPoints != null
          ? ra.systemCalculatedPoints
          : scoring.estimatedPoints;

    return (
      '<section class="card cc-compact-section cc-decision-section kra2-complete-review kra2-complete-review--rejected">' +
      "<h2>Review decision</h2>" +
      '<div class="kra2-rejected-banner" role="status">' +
      '<p class="kra2-rejected-banner__title">Needs changes</p>' +
      '<p class="muted">The faculty member may revise and resubmit. Final approval actions are unavailable until then.</p>' +
      "</div>" +
      '<dl class="kv-grid kv-grid--compact kra2-rejected-summary">' +
      FL.documents.kvRow("Status", "Rejected") +
      FL.documents.kvRow(
        "System-calculated eligible points",
        systemPts != null ? esc(String(systemPts)) : "—"
      ) +
      FL.documents.kvRow("Reviewer feedback", remarks ? esc(remarks) : "—") +
      (ra.scoreAdjustmentReason
        ? FL.documents.kvRow("Score adjustment reason", esc(String(ra.scoreAdjustmentReason)))
        : "") +
      "</dl></section>"
    );
  },

  decisionSectionHtml: function (state) {
    FL.kra2AWorkspaceUi.syncReviewStatusFields(state);
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
    var canEditAssessment = FL.kra2AWorkspaceUi.canEditReviewerAssessment(state);
    var showApproveActions = FL.kra2AWorkspaceUi.isPendingSubmittedReview(state);
    var checklistHtml = FL.kra2AWorkspaceUi.approvalChecklistHtml(state, "");

    var methodHelp = "";
    var indicatorMax = scoring.indicatorMaxPoints != null ? scoring.indicatorMaxPoints : scoring.eligiblePoints;
    var officialBase = scoring.officialBasePoints;
    var verifiedPct = scoring.verifiedContributionPercent;
    var groupMax = scoring.groupMaxPoints;
    var criterionCap = scoring.criterionMaxPoints;
    var critId = (scoring.criterionId || (state.doc && state.doc.criterionId) || "").trim();
    var criterionLabel =
      critId === "kra3-a" || critId === "kra2-a"
        ? "Criterion A maximum (subtotal cap)"
        : critId === "kra3-b"
          ? "Criterion B maximum (subtotal cap)"
          : critId === "kra3-c"
            ? "Criterion C maximum (subtotal cap)"
            : critId === "kra3-d"
              ? "Criterion D maximum (subtotal cap)"
              : "Criterion maximum (subtotal cap)";

    var governingRule = (scoring.adjustmentGoverningRule || "").trim();
    if (governingRule) {
      methodHelp = governingRule;
    } else if (method === "contribution_based") {
      methodHelp =
        "Use verified contribution % to recalculate eligible points. You may also reduce assessed points when indexing or eligibility rules require it.";
    } else if (allowsAdjust || method === "variable") {
      methodHelp =
        "You may assess a lower score when official indexing or eligibility rules require it. Scores cannot exceed the system-calculated eligible amount or the published indicator maximum.";
    } else {
      methodHelp =
        "Official fixed points for this indicator. Confirm eligibility or reject; arbitrary partial scores are not permitted.";
    }

    var contributionField = "";
    if (canDecide && allowsContribution) {
      contributionField =
        '<label class="kra2-scoring-label" for="kra2-contribution-percent">Verified contribution (%)' +
        '<input type="number" id="kra2-contribution-percent" class="kra2-scoring-input" min="1" max="100" step="0.01" value="' +
        esc(String(bundle.declaredContributionPercent != null ? bundle.declaredContributionPercent : "")) +
        '"></label>' +
        '<button type="button" class="btn btn-ghost btn-small" id="kra2-recalc-contribution">Recalculate points</button>' +
        '<span class="cc-save-indicator" id="kra2-save-contribution-indicator"></span>';
    }

    var scoringContextHtml =
      '<div class="kra2-scoring-panel">' +
      "<h3 class=\"kra2-subheading\">Scoring context</h3>" +
      '<p class="muted kra2-scoring-method">Scoring method: <strong>' +
      esc(methodLabel) +
      "</strong></p>" +
      '<p class="muted kra2-scoring-method-help">' +
      esc(methodHelp) +
      "</p>" +
      '<div class="kra2-scoring-row">' +
      "<span>Official accomplishment base points</span>" +
      "<strong>" +
      esc(officialBase != null ? String(officialBase) + " pts" : "—") +
      "</strong></div>" +
      (verifiedPct != null
        ? '<div class="kra2-scoring-row"><span>Verified contribution</span><strong>' +
          esc(String(verifiedPct)) +
          "%</strong></div>"
        : "") +
      (groupMax != null
        ? '<div class="kra2-scoring-row"><span>Category group cap (Annex A)</span><strong>' +
          esc(String(groupMax)) +
          " pts max</strong></div>"
        : "") +
      (criterionCap != null && /^kra[23]-/.test(critId)
        ? '<div class="kra2-scoring-row"><span>' +
          esc(criterionLabel) +
          "</span><strong>" +
          esc(String(criterionCap)) +
          " pts</strong></div>"
        : "") +
      '<div class="kra2-scoring-row">' +
      "<span>Official indicator maximum (per output)</span>" +
      "<strong>" +
      esc(indicatorMax != null ? String(indicatorMax) + " pts" : "—") +
      "</strong></div>" +
      (canEditAssessment
        ? '<strong class="kra2-final-points sr-only" id="kra2-final-points-display">' +
          esc(finalPts != null ? String(finalPts) : "—") +
          "</strong>"
        : '<div class="kra2-scoring-row kra2-scoring-row--highlight">' +
          "<span>System-calculated eligible points</span>" +
          "<strong class=\"kra2-system-points\" id=\"kra2-system-points-display\">" +
          esc(systemPts != null ? String(systemPts) : "—") +
          "</strong></div>" +
          '<div class="kra2-scoring-row">' +
          "<span>Reviewer-assessed points</span>" +
          "<strong class=\"kra2-final-points\" id=\"kra2-final-points-display\">" +
          esc(finalPts != null ? String(finalPts) : "—") +
          "</strong></div>") +
      (scoring.scoringConfigurationVersion
        ? '<p class="muted kra2-scoring-version">Published scoring version: ' +
          esc(String(scoring.scoringConfigurationVersion)) +
          "</p>"
        : "") +
      contributionField +
      "</div>";

    var assessmentWorkflowHtml = "";
    if (FL.kra2AWorkspaceUi.isReassessmentSessionActive(state)) {
      assessmentWorkflowHtml =
        '<div class="kra2-scoring-panel kra2-scoring-panel--assessment">' +
        FL.kra2AWorkspaceUi.reassessmentActivePanelHtml(state) +
        "</div>";
    } else if (canEditAssessment) {
      assessmentWorkflowHtml =
        '<div class="kra2-scoring-panel kra2-scoring-panel--assessment">' +
        "<h3 class=\"kra2-subheading\">Reviewer assessment</h3>" +
        (showApproveActions ? FL.kra2AWorkspaceUi.pendingApprovalBlockersHtml(state) : "") +
        FL.kra2AWorkspaceUi.unifiedReviewerAssessmentHtml(state) +
        FL.kra2AWorkspaceUi.reassessmentRequestSupplementHtml(state) +
        "</div>";
    } else if (canDecide && bundle.submittedForReviewAt) {
      assessmentWorkflowHtml =
        '<p class="muted">You do not have permission to assess or decide on this accomplishment.</p>';
    }

    return (
      '<section class="card cc-compact-section cc-decision-section kra2-complete-review">' +
      "<h2>Complete review</h2>" +
      checklistHtml +
      scoringContextHtml +
      assessmentWorkflowHtml +
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
