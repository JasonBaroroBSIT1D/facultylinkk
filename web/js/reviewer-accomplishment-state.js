/**
 * Shared reviewer accomplishment lifecycle — submission, verification, and decisions.
 * Used by KRA I–IV in-workspace accomplishment review (not document OCR alone).
 */
window.FL = window.FL || {};

FL.reviewerAccomplishmentState = {
  bundle: function (state) {
    return (state && state.bundle) || {};
  },

  doc: function (state) {
    return (state && state.doc) || {};
  },

  validation: function (state) {
    return (state && state.validation) || {};
  },

  normalizeReviewStatus: function (state) {
    var bundle = FL.reviewerAccomplishmentState.bundle(state);
    var validation = FL.reviewerAccomplishmentState.validation(state);
    var ra = bundle.reviewerAssessment || {};
    var candidates = [
      bundle.reviewStatus,
      ra.reviewStatus,
      validation.reviewStatus,
      state && state.doc && state.doc.reviewStatus
    ];
    var i;
    for (i = 0; i < candidates.length; i++) {
      var raw = (candidates[i] || "").toString().trim().toLowerCase();
      if (raw === "approved" || raw === "rejected" || raw === "pending") return raw;
    }
    if (FL.reviewerAccomplishmentState.isSubmittedForReview(state)) return "pending";
    return "draft";
  },

  isSubmittedForReview: function (state) {
    var bundle = FL.reviewerAccomplishmentState.bundle(state);
    if ((bundle.submittedForReviewAt || "").trim()) return true;
    var flags = FL.reviewerAccomplishmentState.validation(state).flags || [];
    if (flags.indexOf("not_submitted") >= 0) return false;
    var doc = FL.reviewerAccomplishmentState.doc(state);
    var st = (doc.status || "").toLowerCase();
    if (st === "draft") return false;
    if (
      st === "pending_review"
      || st === "reviewer_required"
      || st === "approved"
      || st === "rejected"
      || st === "revision"
      || st === "needs_revision"
    ) {
      return true;
    }
    var v = FL.reviewerAccomplishmentState.validation(state);
    if (v.submittedForReview === true) return true;
    return false;
  },

  isDraftAwaitingFaculty: function (state) {
    if (FL.reviewerAccomplishmentState.normalizeReviewStatus(state) === "approved") return false;
    if (FL.reviewerAccomplishmentState.normalizeReviewStatus(state) === "rejected") return false;
    return !FL.reviewerAccomplishmentState.isSubmittedForReview(state);
  },

  isAccomplishmentApproved: function (state) {
    return FL.reviewerAccomplishmentState.normalizeReviewStatus(state) === "approved";
  },

  isAccomplishmentRejected: function (state) {
    return FL.reviewerAccomplishmentState.normalizeReviewStatus(state) === "rejected";
  },

  isPendingSubmittedReview: function (state) {
    if (!FL.reviewerAccomplishmentState.isSubmittedForReview(state)) return false;
    if (FL.reviewerAccomplishmentState.isAccomplishmentApproved(state)) return false;
    if (FL.reviewerAccomplishmentState.isAccomplishmentRejected(state)) return false;
    return true;
  },

  /** Interactive evidence verification (PATCH slot status) — requires faculty submission. */
  canVerifyEvidence: function (state) {
    if (!state || !state.canDecide) return false;
    if (!FL.reviewerAccomplishmentState.isSubmittedForReview(state)) return false;
    if (FL.reviewerAccomplishmentState.isAccomplishmentApproved(state)) return false;
    return true;
  },

  canSavePreparationNotes: function (state) {
    return !!(state && state.canDecide && FL.reviewerAccomplishmentState.isDraftAwaitingFaculty(state));
  },

  canSaveFullAssessment: function (state) {
    if (!state || !state.canDecide) return false;
    if (FL.reviewerAccomplishmentState.isDraftAwaitingFaculty(state)) return false;
    return true;
  },

  canFinalizeReviewDecision: function (state) {
    return FL.reviewerAccomplishmentState.isPendingSubmittedReview(state) && !!state.canDecide;
  },

  slotVerificationDisplayLabel: function (state, slotStatus) {
    if (FL.reviewerAccomplishmentState.isDraftAwaitingFaculty(state)) {
      return "Not ready for verification";
    }
    var st = (slotStatus || "").toLowerCase();
    if (st === "verified") return "Verified";
    if (st === "reviewer_required") return "Needs clarification";
    if (st === "missing") return "Missing";
    if (st === "not_applicable") return "Not applicable";
    return "Pending verification";
  },

  draftBannerHtml: function () {
    return (
      '<div class="rev-accomplishment-draft-banner" role="status">' +
      '<p class="rev-accomplishment-draft-banner__title">Waiting for faculty submission</p>' +
      '<p class="muted rev-accomplishment-draft-banner__lede">' +
      "The faculty is still preparing this accomplishment. You can view documents and leave preparation notes. " +
      "Verification will be available after submission." +
      "</p></div>"
    );
  },

  preparationNotesSectionHtml: function (state) {
    var esc = FL.esc;
    var bundle = FL.reviewerAccomplishmentState.bundle(state);
    var ra = bundle.reviewerAssessment || {};
    var scoring = (state && state.scoring) || {};
    var text =
      scoring.draftReviewerRemarks != null && String(scoring.draftReviewerRemarks).trim()
        ? scoring.draftReviewerRemarks
        : (state && state.remarks) || bundle.reviewerRemarks || ra.draftRemarks || ra.remarks || "";
    return (
      '<section class="card cc-compact-section rev-prep-notes-section">' +
      "<h2>Preparation notes for faculty</h2>" +
      '<p class="muted">These notes are saved for your reference and do not verify evidence or approve the accomplishment.</p>' +
      '<label class="kra2-remarks-label" for="kra2-prep-notes">Preparation notes' +
      '<textarea id="kra2-prep-notes" rows="4" class="kra2-remarks-input" placeholder="Optional guidance while the faculty completes submission.">' +
      esc(text) +
      "</textarea></label>" +
      '<div class="cc-decision-actions">' +
      '<button type="button" class="btn btn-primary" id="kra2-save-prep-notes">Save Notes</button>' +
      '<span class="cc-save-indicator" id="kra2-save-prep-notes-indicator"></span>' +
      "</div></section>"
    );
  }
};
