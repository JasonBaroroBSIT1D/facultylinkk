/**
 * Criterion B — simplified reviewer workflow (one file at a time).
 */
window.FL = window.FL || {};

FL.criterionBSimpleReview = {
  SLOT_ORDER: [
    "primary_material",
    "primary_contribution_document",
    "imdc_evaluation_approval",
    "approved_syllabus",
    "library_certification",
    "annex_c_contribution",
    "complete_set_attestation",
    "originality_proof",
    "pedagogical_validity_proof",
    "feasibility_study",
    "benchmarking_report",
    "approved_program_outcomes",
    "curriculum_obe_mapping",
    "revised_curriculum_stakeholder_consultation",
    "dean_contribution_certification",
    "academic_council_resolution",
    "governing_board_resolution",
    "implementation_evidence",
    "rrpa_or_copc"
  ],

  _reviewHref: function (doc) {
    const base = "document-review.html?id=" + encodeURIComponent(doc.id);
    const q = [
      doc.facultyId ? "faculty=" + encodeURIComponent(doc.facultyId) : "",
      "kra=" + encodeURIComponent(doc.kraId || "kra1"),
      "criterion=kra1-b"
    ].filter(Boolean).join("&");
    return base + "&" + q;
  },

  mountAccomplishmentListInWorkspace: function (session, state, isAdmin, host, criterion) {
    const facultyId = state.facultyId;
    const person = FL.store.facultyById(facultyId);
    const docs = FL.evidence._facultyDocs(session, facultyId).filter(function (d) {
      return d.criterionId === "kra1-b";
    });
    const critLabel = criterion
      ? FL.rules.criterionUserLabel(criterion.id, criterion.name)
      : "Criterion B";
    host.innerHTML = FL.criterionBWorkspaceUi.criterionBReviewWorkspaceHtml({
      criterionLabel: critLabel,
      personName: person ? person.name : "this faculty member",
      documents: docs,
      isAdmin: isAdmin,
      reviewHref: function (doc) {
        return FL.criterionBSimpleReview._reviewHref(doc);
      }
    });
  },

  _draftStorageKey: function (docId) {
    return "fl_cb_review_draft_" + docId;
  },

  _loadStoredDraft: function (docId) {
    try {
      const raw = sessionStorage.getItem(FL.criterionBSimpleReview._draftStorageKey(docId));
      return raw ? JSON.parse(raw) : null;
    } catch (_e) {
      return null;
    }
  },

  _saveStoredDraft: function (docId, state) {
    try {
      sessionStorage.setItem(
        FL.criterionBSimpleReview._draftStorageKey(docId),
        JSON.stringify({
          drafts: state.drafts,
          fileIndex: state.fileIndex,
          step: state.step,
          rrpa: state.rrpa,
          bundleRemarks: state.bundleRemarks,
          assessment: state.assessment,
          specializationAligned: state.specializationAligned
        })
      );
    } catch (_e) {
      /* ignore quota */
    }
  },

  _clearStoredDraft: function (docId) {
    try {
      sessionStorage.removeItem(FL.criterionBSimpleReview._draftStorageKey(docId));
    } catch (_e) {
      /* ignore */
    }
  },

  paintReviewPage: function (session, doc, canDecide, ctx) {
    const page = document.getElementById("page");
    page.innerHTML = FL.ui.loading("Loading accomplishment…");
    FL.criterionBEvidence.fetchBundle(session, doc.id).then(function (payload) {
      const state = FL.criterionBSimpleReview._createState(doc, payload, canDecide);
      const stored = FL.criterionBSimpleReview._loadStoredDraft(doc.id);
      if (stored) {
        state.drafts = stored.drafts || state.drafts;
        state.fileIndex = typeof stored.fileIndex === "number" ? stored.fileIndex : state.fileIndex;
        state.step = stored.step || state.step;
        state.rrpa = stored.rrpa || state.rrpa;
        state.bundleRemarks = stored.bundleRemarks != null ? stored.bundleRemarks : state.bundleRemarks;
        state.assessment = stored.assessment || state.assessment;
        if (stored.specializationAligned !== undefined) {
          state.specializationAligned = stored.specializationAligned;
        }
      }
      state.facultyName = ctx.faculty ? ctx.faculty.name : "Faculty";
      state.backHref = ctx.back || "documents.html";
      state.backLabel = ctx.backLabel || "Back to Evidence Workspace";
      FL.criterionBSimpleReview._renderStep(session, state);
    }).catch(function (err) {
      page.innerHTML = FL.ui.empty("Could not load", FL.esc(err.message || "Try again."));
    });
  },

  _createState: function (doc, payload, canDecide) {
    const bundle = payload.bundle || {};
    const checklist = bundle.checklist || {};
    const items = [];
    FL.criterionBSimpleReview.SLOT_ORDER.forEach(function (slotId) {
      const entry = checklist[slotId];
      if (!entry || !entry.documentId) return;
      const docId = entry.documentId;
      let fileDoc = docId === doc.id ? doc : FL.store.documentById(docId);
      items.push({
        slotId: slotId,
        label: FL.criterionBWorkspaceUi.SLOT_LABELS[slotId] || slotId.replace(/_/g, " "),
        purpose: FL.criterionBWorkspaceUi.slotPurpose(slotId),
        entry: entry,
        fileDoc: fileDoc,
        draftStatus: entry.status || "present_unverified",
        draftNote: entry.reviewerNote || ""
      });
    });
    const scoring = payload.scoring || {};
    const proposed = scoring.reviewerProposedAssessment || {};
    return {
      doc: doc,
      payload: payload,
      scoring: scoring,
      bundle: bundle,
      contributionVerification: payload.contributionVerification || null,
      validation: payload.validation || {},
      canDecide: !!canDecide,
      step: items.length ? "files" : (canDecide ? "score" : "summary"),
      fileIndex: 0,
      items: items,
      drafts: {},
      bundleRemarks: bundle.reviewerRemarks || "",
      assessment: {
        points: proposed.points != null ? String(proposed.points) : "",
        justification: proposed.justification || ""
      },
      rrpa: {
        value: (payload.validation && payload.validation.rrpaCopcApplicability) ||
          bundle.rrpaCopcApplicability || "unknown",
        note: (payload.validation && payload.validation.rrpaCopcApplicabilityNote) ||
          bundle.rrpaCopcApplicabilityNote || ""
      },
      specializationAligned: bundle.specializationAligned
    };
  },

  _mergePayloadIntoState: function (state, payload) {
    if (!payload) return;
    if (payload.bundle) state.bundle = payload.bundle;
    if (payload.validation) state.validation = payload.validation;
    if (payload.scoring) state.scoring = payload.scoring;
    if (payload.contributionVerification !== undefined) {
      state.contributionVerification = payload.contributionVerification;
    }
    const ev = payload.criterionBEvidence || (payload.document && payload.document.criterionBEvidence);
    if (ev) {
      if (ev.bundle) state.bundle = ev.bundle;
      if (ev.validation) state.validation = ev.validation;
      if (ev.scoring) state.scoring = ev.scoring;
    }
    if (state.bundle && state.bundle.specializationAligned !== undefined) {
      state.specializationAligned = state.bundle.specializationAligned;
    }
    state.items.forEach(function (item) {
      const entry = (state.bundle.checklist || {})[item.slotId];
      if (entry) {
        item.entry = entry;
        item.draftStatus = entry.status || item.draftStatus;
        item.draftNote = entry.reviewerNote || item.draftNote;
      }
    });
  },

  _toastScoringBlocked: function (state) {
    const msgs = FL.criterionBWorkspaceUi.scoringBlockMessages(state, false);
    if (!msgs.length) {
      FL.ui.toast("Cannot finish scoring yet. Verify each required document first.", "warn");
      return;
    }
    const preview = msgs.slice(0, 3).join(" ");
    FL.ui.toast("Cannot finish scoring yet. " + preview, "warn");
  },

  _renderStep: function (session, state) {
    FL.criterionBSimpleReview._saveStoredDraft(state.doc.id, state);
    const page = document.getElementById("page");
    if (state.step === "files") {
      page.innerHTML = FL.criterionBSimpleReview._filesStepHtml(state);
      FL.criterionBSimpleReview._bindFilesStep(session, state);
      return;
    }
    if (state.step === "rrpa") {
      page.innerHTML = FL.criterionBSimpleReview._rrpaStepHtml(state);
      FL.criterionBSimpleReview._bindRrpaStep(session, state);
      return;
    }
    if (state.step === "score") {
      page.innerHTML = FL.criterionBSimpleReview._scoreStepHtml(state);
      FL.criterionBSimpleReview._bindScoreStep(session, state);
      return;
    }
    page.innerHTML = FL.criterionBSimpleReview._summaryStepHtml(state);
    FL.criterionBSimpleReview._bindSummaryStep(session, state);
  },

  _filesStepHtml: function (state) {
    const ui = FL.criterionBWorkspaceUi;
    const esc = FL.esc;
    const item = state.items[state.fileIndex];
    const total = state.items.length;
    const fileDoc = item.fileDoc || state.doc;
    const draft = state.drafts[item.slotId] || {
      status: item.draftStatus,
      note: item.draftNote
    };
    const accepted = draft.status === "verified";
    const rejected = draft.status === "reviewer_required";
    const previewMount = fileDoc
      ? "<div id=\"cb-simple-preview-mount\" class=\"doc-preview-mount\" data-doc-preview-id=\""
        + esc(fileDoc.id) + "\"><p class=\"ca-preview-loading\" role=\"status\">Loading document preview…</p></div>"
      : "<p class=\"note\">Preview not available.</p>";
    const contribPanel = (item.slotId === "annex_c_contribution" && state.bundle.authorship === "co")
      ? FL.criterionBSimpleReview._contributionVerificationHtml(state)
      : "";
    return `
      <div class="portal-page cb-simple-review">
        <header class="card cb-simple-head">
          <a class="btn btn-ghost btn-small" href="${esc(state.backHref)}">${esc(state.backLabel)}</a>
          <h1>${esc(ui.claimTitle(state.bundle))}</h1>
          <p class="sub">${esc(state.facultyName)} · File ${state.fileIndex + 1} of ${total}</p>
          ${FL.criterionBSimpleReview._stepsBanner("files")}
        </header>
        <section class="card cb-simple-file">
          <h2>${esc(item.label)}</h2>
          <p class="note">${esc(item.purpose || "Check that this file matches the requirement.")}</p>
          <p><strong>${esc(fileDoc ? (fileDoc.name || fileDoc.title || "Uploaded file") : "File")}</strong></p>
          <div class="cb-simple-preview preview preview-clean">${previewMount}</div>
          ${contribPanel}
          <h3 class="cb-subhead">Does this document meet the requirement?</h3>
          <div class="cb-simple-choices">
            <button type="button" class="btn ${accepted ? "btn-primary" : "btn-ghost"}" data-choice="yes">Yes, accept this file</button>
            <button type="button" class="btn ${rejected ? "btn-primary" : "btn-ghost"}" data-choice="no">No, request correction</button>
          </div>
          <label class="field field-wide cb-correction-note ${rejected ? "" : "is-hidden"}">
            <span>Explain what needs to change</span>
            <textarea rows="3" id="cb-simple-correction">${esc(draft.note || "")}</textarea>
          </label>
          <div class="cb-simple-nav">
            <button type="button" class="btn btn-ghost" id="cb-simple-prev" ${state.fileIndex === 0 ? "disabled" : ""}>Previous file</button>
            <button type="button" class="btn btn-primary" id="cb-simple-next">${state.fileIndex >= total - 1 ? "Continue" : "Next file"}</button>
          </div>
        </section>
      </div>`;
  },

  _bindFilesStep: function (session, state) {
    const item = state.items[state.fileIndex];
    const previewMount = document.getElementById("cb-simple-preview-mount");
    if (previewMount && item.fileDoc) {
      FL.documents.mountAuthenticatedPreview(item.fileDoc, previewMount, { session: session });
    } else if (previewMount && item.entry && item.entry.documentId) {
      const fallback = FL.store.documentById(item.entry.documentId);
      if (fallback) {
        FL.documents.mountAuthenticatedPreview(fallback, previewMount, { session: session });
      }
    }
    const noteEl = document.getElementById("cb-simple-correction");
    const persistDraft = function (status) {
      state.drafts[item.slotId] = {
        status: status,
        note: noteEl ? noteEl.value : ""
      };
    };
    document.querySelectorAll("[data-choice]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const yes = btn.getAttribute("data-choice") === "yes";
        persistDraft(yes ? "verified" : "reviewer_required");
        const noteWrap = document.querySelector(".cb-correction-note");
        if (noteWrap) noteWrap.classList.toggle("is-hidden", yes);
        FL.criterionBSimpleReview._renderStep(session, state);
      });
    });
    const prev = document.getElementById("cb-simple-prev");
    if (prev) {
      prev.addEventListener("click", function () {
        persistDraft(state.drafts[item.slotId] ? state.drafts[item.slotId].status : item.draftStatus);
        if (state.fileIndex > 0) {
          state.fileIndex -= 1;
          FL.criterionBSimpleReview._renderStep(session, state);
        }
      });
    }
    if (item.slotId === "annex_c_contribution" && state.bundle.authorship === "co") {
      FL.criterionBSimpleReview._bindContributionVerification(session, state);
    }
    const next = document.getElementById("cb-simple-next");
    if (next) {
      next.addEventListener("click", function () {
        const cur = state.drafts[item.slotId];
        if (!cur || (cur.status === "reviewer_required" && !(cur.note || "").trim())) {
          FL.ui.toast("Please explain what needs correction, or accept the file.", "warn");
          return;
        }
        if (state.fileIndex < state.items.length - 1) {
          state.fileIndex += 1;
          FL.criterionBSimpleReview._renderStep(session, state);
          return;
        }
        if (state.bundle.claimType === "academic_program" && state.canDecide) {
          state.step = "rrpa";
        } else if (state.canDecide) {
          state.step = "score";
        } else {
          state.step = "summary";
        }
        FL.criterionBSimpleReview._renderStep(session, state);
      });
    }
  },

  _rrpaStepHtml: function (state) {
    const esc = FL.esc;
    return `
      <div class="portal-page cb-simple-review">
        <header class="card cb-simple-head">
          <h1>RRPA or COPC</h1>
          <p class="note">Is RRPA or COPC required for this academic program?</p>
          ${FL.criterionBSimpleReview._stepsBanner("rrpa")}
        </header>
        <section class="card">
          <label class="field"><span>Your decision</span>
            <select id="cb-simple-rrpa">
              <option value="unknown"${state.rrpa.value === "unknown" ? " selected" : ""}>Not sure yet</option>
              <option value="applicable"${state.rrpa.value === "applicable" ? " selected" : ""}>Yes, it is required</option>
              <option value="not_applicable"${state.rrpa.value === "not_applicable" ? " selected" : ""}>No, not required</option>
            </select>
          </label>
          <label class="field field-wide"><span>Reason (required if not required)</span>
            <textarea id="cb-simple-rrpa-note" rows="3">${esc(state.rrpa.note || "")}</textarea>
          </label>
          <button type="button" class="btn btn-primary" id="cb-simple-rrpa-continue">Continue to assessment score</button>
        </section>
      </div>`;
  },

  _bindRrpaStep: function (session, state) {
    document.getElementById("cb-simple-rrpa-continue").addEventListener("click", function () {
      const sel = document.getElementById("cb-simple-rrpa");
      const note = document.getElementById("cb-simple-rrpa-note");
      state.rrpa.value = sel ? sel.value : "unknown";
      state.rrpa.note = note ? note.value : "";
      if (state.rrpa.value === "not_applicable" && !(state.rrpa.note || "").trim()) {
        FL.ui.toast("Please give a short reason when RRPA/COPC is not required.", "warn");
        return;
      }
      state.step = state.canDecide ? "score" : "summary";
      FL.criterionBSimpleReview._renderStep(session, state);
    });
  },

  _stepsBanner: function (active) {
    const steps = [
      { id: "files", label: "1. Check documents" },
      { id: "score", label: "2. Give score" },
      { id: "summary", label: "3. Save review" }
    ];
    return `<nav class="cb-review-steps" aria-label="Review steps">${steps.map(function (s) {
      const on = s.id === active || (active === "rrpa" && s.id === "files");
      return `<span class="cb-review-step${on ? " is-active" : ""}">${FL.esc(s.label)}</span>`;
    }).join("")}</nav>`;
  },

  _scoreStepHtml: function (state) {
    const esc = FL.esc;
    const ui = FL.criterionBWorkspaceUi;
    const sc = state.scoring || {};
    const display = sc.displayScore || {};
    const sys = sc.systemEstimatePoints;
    const guide = sc.guidelineCompliantVerifiedPoints;
    const maxPts = sc.allowedReviewerAssessmentMaxPoints;
    const base = sc.publishedBasePoints;
    const canScore = ui.canFinalizeReviewerScore(state);
    const spec = state.specializationAligned;
    const specVal = spec === true ? "yes" : spec === false ? "no" : "";
    const readiness = ui.reviewReadinessChecklistHtml(state, { showJump: true });
    const diffHint = sys != null && state.assessment.points
      ? (parseFloat(state.assessment.points) - sys).toFixed(2)
      : "";
    const currentPts = display.points != null ? esc(String(display.points)) : "Not available yet";
    const currentStatus = esc(display.label || "Estimated");
    const maxAllowed = maxPts != null ? esc(String(maxPts)) + " points" : "See rubric";
    const scoreFields = canScore
      ? `<label class="field"><span>Your assessment score (points)</span>
            <input type="number" step="0.01" min="0" id="cb-simple-assessment-points" value="${esc(state.assessment.points || "")}" />
          </label>
          <label class="field field-wide"><span>Why this score? (required for final assessment)</span>
            <textarea id="cb-simple-assessment-just" rows="4" placeholder="Brief professional justification based on evidence quality and guidelines.">${esc(state.assessment.justification || "")}</textarea>
          </label>
          ${diffHint !== "" ? `<p class="note"><strong>Difference from automated estimate:</strong> ${esc(diffHint)} pts</p>` : ""}
          <button type="button" class="btn btn-primary" id="cb-simple-score-continue">Continue to save review</button>`
      : `<p class="note warn">Finish the checklist above, then return here to enter your assessment score.</p>
          <button type="button" class="btn btn-ghost" id="cb-simple-back-files">Back to check documents</button>
          <button type="button" class="btn btn-primary" id="cb-simple-save-partial">Save document decisions only</button>`;
    const auditDetails = `<details class="cb-score-audit">
            <summary>View scoring details</summary>
            <dl class="cb-score-refs">
              <div><dt>Automated estimate (preserved)</dt><dd>${sys != null ? esc(String(sys)) + " pts" : "Not available"}</dd></div>
              <div><dt>Published base (this indicator row)</dt><dd>${base != null ? esc(String(base)) + " pts" : "See rubric"}</dd></div>
              <div><dt>Rule-based verified points</dt><dd>${guide != null ? esc(String(guide)) + " pts" : "Not eligible yet"}</dd></div>
              <div><dt>Criterion B aggregate cap</dt><dd>${sc.criterionBMaxPoints != null ? esc(String(sc.criterionBMaxPoints)) + " pts (KRA I Criterion B total cap — not this row's base)" : "30 pts default"}</dd></div>
            </dl>
            <p class="note">${esc(sc.systemEstimateNote || "")}</p>
          </details>`;
    return `
      <div class="portal-page cb-simple-review">
        <header class="card cb-simple-head">
          <h1>Give assessment score</h1>
          <p class="note">Faculty see one current score: <strong>Estimated</strong> until you save a completed assessment with justification.</p>
          ${FL.criterionBSimpleReview._stepsBanner("score")}
        </header>
        <section class="card">${readiness}</section>
        <section class="card cb-score-panel">
          ${state.bundle.claimType !== "academic_program" ? `<label class="field"><span>Does this work align with the faculty member's field of specialization?</span>
            <select id="cb-specialization-aligned">
              <option value=""${specVal === "" ? " selected" : ""}>Not confirmed yet</option>
              <option value="yes"${specVal === "yes" ? " selected" : ""}>Yes — aligned with specialization</option>
              <option value="no"${specVal === "no" ? " selected" : ""}>No — not aligned</option>
            </select>
          </label>` : ""}
          <div class="cb-score-summary">
            <p class="cb-score-current"><strong>Current Score:</strong> ${currentPts}${display.points != null ? " points" : ""}</p>
            <p><strong>Status:</strong> ${currentStatus}</p>
            <p><strong>Maximum Allowed:</strong> ${maxAllowed}</p>
          </div>
          ${auditDetails}
          ${scoreFields}
        </section>
      </div>`;
  },

  _bindScoreStep: function (session, state) {
    const specEl = document.getElementById("cb-specialization-aligned");
    if (specEl) {
      specEl.addEventListener("change", function () {
        const v = specEl.value;
        state.specializationAligned = v === "yes" ? true : v === "no" ? false : null;
        FL.criterionBSimpleReview._renderStep(session, state);
      });
    }
    document.querySelectorAll("[data-goto-file]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        state.step = "files";
        state.fileIndex = parseInt(btn.getAttribute("data-goto-file"), 10) || 0;
        FL.criterionBSimpleReview._renderStep(session, state);
      });
    });
    const backFiles = document.getElementById("cb-simple-back-files");
    if (backFiles) {
      backFiles.addEventListener("click", function () {
        state.step = "files";
        state.fileIndex = 0;
        FL.criterionBSimpleReview._renderStep(session, state);
      });
    }
    const partial = document.getElementById("cb-simple-save-partial");
    if (partial) {
      partial.addEventListener("click", function () {
        partial.disabled = true;
        FL.criterionBSimpleReview._persistReview(session, state, { includeAssessment: false }).then(function () {
          FL.criterionBSimpleReview._clearStoredDraft(state.doc.id);
          FL.ui.toast("Document decisions saved. Faculty score remains Estimated until evidence is complete.", "ok");
          window.location.href = state.backHref;
        }).catch(function (err) {
          partial.disabled = false;
          FL.ui.toast(err.message || "Could not save.", "danger");
        });
      });
    }
    const cont = document.getElementById("cb-simple-score-continue");
    if (!cont) return;
    const ptsEl = document.getElementById("cb-simple-assessment-points");
    const justEl = document.getElementById("cb-simple-assessment-just");
    cont.addEventListener("click", function () {
      if (!FL.criterionBWorkspaceUi.canFinalizeReviewerScore(state)) {
        FL.criterionBSimpleReview._toastScoringBlocked(state);
        return;
      }
      const pts = ptsEl ? ptsEl.value : "";
      const just = justEl ? justEl.value.trim() : "";
      if (!pts.trim() || Number.isNaN(parseFloat(pts))) {
        FL.ui.toast("Enter your assessment score in points.", "warn");
        return;
      }
      if (just.length < 10) {
        FL.ui.toast("Please write a short justification (at least 10 characters).", "warn");
        return;
      }
      const max = state.scoring && state.scoring.allowedReviewerAssessmentMaxPoints;
      if (max != null && parseFloat(pts) > max + 1e-6) {
        FL.ui.toast("Score exceeds the published maximum for this accomplishment.", "warn");
        return;
      }
      state.assessment = { points: pts.trim(), justification: just };
      state.step = "summary";
      FL.criterionBSimpleReview._renderStep(session, state);
    });
  },

  _summaryStepHtml: function (state) {
    const esc = FL.esc;
    const ui = FL.criterionBWorkspaceUi;
    const checklist = state.bundle.checklist || {};
    const missing = [];
    FL.criterionBSimpleReview.SLOT_ORDER.forEach(function (slotId) {
      const entry = checklist[slotId];
      const st = entry && entry.status;
      if (st === "missing" || !entry || !entry.documentId) {
        if (st === "missing" || (entry && !entry.documentId && st !== "not_applicable")) {
          missing.push(ui.SLOT_LABELS[slotId] || slotId);
        }
      }
    });
    const accepted = [];
    const corrections = [];
    state.items.forEach(function (item) {
      const d = state.drafts[item.slotId] || { status: item.draftStatus, note: item.draftNote };
      if (d.status === "verified") accepted.push(item.label);
      if (d.status === "reviewer_required") corrections.push(item.label + (d.note ? ": " + d.note : ""));
    });
    const vLabel = ui.validationStatusMeta(state.validation.validationStatus).label;
    const canScore = ui.canFinalizeReviewerScore(state);
    const readiness = ui.reviewReadinessChecklistHtml(state, { showJump: true, intro: "Review checklist:" });
    const sc = state.scoring || {};
    const assessPts = state.assessment && state.assessment.points
      ? state.assessment.points
      : (sc.reviewerProposedAssessment && sc.reviewerProposedAssessment.points != null
        ? String(sc.reviewerProposedAssessment.points)
        : "");
    const assessJust = state.assessment && state.assessment.justification
      ? state.assessment.justification
      : ((sc.reviewerProposedAssessment && sc.reviewerProposedAssessment.justification) || "");
    return `
      <div class="portal-page cb-simple-review">
        <header class="card cb-simple-head">
          <h1>Save review</h1>
          <p class="sub">${esc(ui.claimTitle(state.bundle))} · ${esc(state.facultyName)}</p>
          ${FL.criterionBSimpleReview._stepsBanner("summary")}
        </header>
        <section class="card">${readiness}</section>
        <section class="card">
          <p><strong>Overall:</strong> ${esc(vLabel)} (individual files must still meet all rules.)</p>
          <h3 class="cb-subhead">Assessment (one current score for faculty)</h3>
          ${canScore && assessPts
            ? `<p><strong>Reviewer Assessed (after save):</strong> ${esc(assessPts)} pts</p>${assessJust ? `<p class="note"><strong>Justification:</strong> ${esc(assessJust)}</p>` : ""}`
            : `<p><strong>Estimated (unchanged):</strong> ${sc.displayScore && sc.displayScore.points != null ? esc(String(sc.displayScore.points)) + " pts" : "Not available yet"}</p>
               <p class="note">No final assessment score will be saved until required evidence is verified${assessPts ? " (your draft score will be discarded)" : ""}.</p>`}
          <p class="note">Automated estimate preserved for audit: ${sc.systemEstimatePoints != null ? esc(String(sc.systemEstimatePoints)) + " pts" : "Not available"}. Rule-based verified points (official config): ${sc.guidelineCompliantVerifiedPoints != null ? esc(String(sc.guidelineCompliantVerifiedPoints)) + " pts" : "Not eligible yet"}.</p>
          <h3 class="cb-subhead">Accepted files</h3>
          ${accepted.length ? `<ul>${accepted.map(function (l) { return "<li>" + esc(l) + "</li>"; }).join("")}</ul>` : "<p class=\"note\">None marked accepted in this session yet.</p>"}
          <h3 class="cb-subhead">Corrections requested</h3>
          ${corrections.length ? `<ul>${corrections.map(function (l) { return "<li>" + esc(l) + "</li>"; }).join("")}</ul>` : "<p class=\"note\">None.</p>"}
          <h3 class="cb-subhead">Still missing from faculty</h3>
          ${missing.length ? `<ul>${missing.map(function (l) { return "<li>" + esc(l) + "</li>"; }).join("")}</ul>` : "<p class=\"note\">No missing required uploads detected.</p>"}
          <label class="field field-wide"><span>Feedback for faculty</span>
            <textarea id="cb-simple-remarks" rows="3">${esc(state.bundleRemarks || "")}</textarea>
          </label>
          ${state.canDecide
            ? `<div class="cb-summary-actions">
                <button type="button" class="btn btn-ghost btn-large" id="cb-simple-save-partial-summary">Save document reviews only</button>
                ${canScore && assessPts
                  ? `<button type="button" class="btn btn-primary btn-large" id="cb-simple-save">Save complete review with score</button>`
                  : ""}
              </div>`
            : ""}
        </section>
      </div>`;
  },

  _bindSummaryStep: function (session, state) {
    document.querySelectorAll("[data-goto-file]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        state.step = "files";
        state.fileIndex = parseInt(btn.getAttribute("data-goto-file"), 10) || 0;
        FL.criterionBSimpleReview._renderStep(session, state);
      });
    });
    const partial = document.getElementById("cb-simple-save-partial-summary");
    if (partial) {
      partial.addEventListener("click", function () {
        partial.disabled = true;
        const remarksEl = document.getElementById("cb-simple-remarks");
        state.bundleRemarks = remarksEl ? remarksEl.value : "";
        FL.criterionBSimpleReview._persistReview(session, state, { includeAssessment: false }).then(function () {
          FL.criterionBSimpleReview._clearStoredDraft(state.doc.id);
          FL.ui.toast("Document reviews saved. Faculty score stays Estimated.", "ok");
          window.location.href = state.backHref;
        }).catch(function (err) {
          partial.disabled = false;
          FL.ui.toast(err.message || "Could not save review.", "danger");
        });
      });
    }
    const save = document.getElementById("cb-simple-save");
    if (!save) return;
    save.addEventListener("click", function () {
      if (!FL.criterionBWorkspaceUi.canFinalizeReviewerScore(state)) {
        FL.criterionBSimpleReview._toastScoringBlocked(state);
        return;
      }
      const just = (state.assessment && state.assessment.justification) || "";
      const pts = state.assessment && state.assessment.points;
      if (!pts || just.length < 10) {
        FL.ui.toast("Complete step 2: enter your assessment score and justification.", "warn");
        state.step = "score";
        FL.criterionBSimpleReview._renderStep(session, state);
        return;
      }
      save.disabled = true;
      const remarksEl = document.getElementById("cb-simple-remarks");
      state.bundleRemarks = remarksEl ? remarksEl.value : "";
      FL.criterionBSimpleReview._persistReview(session, state, { includeAssessment: true }).then(function () {
        FL.criterionBSimpleReview._clearStoredDraft(state.doc.id);
        FL.ui.toast("Complete review saved with your assessment score.", "ok");
        window.location.href = state.backHref;
      }).catch(function (err) {
        save.disabled = false;
        FL.ui.toast(err.message || "Could not save review.", "danger");
      });
    });
  },

  _effectiveSlotDecision: function (state, item) {
    const entry = item.entry || {};
    const draft = state.drafts[item.slotId];
    return {
      status: draft ? draft.status : (item.draftStatus || entry.status || "missing"),
      note: draft ? (draft.note || "") : (item.draftNote || entry.reviewerNote || "")
    };
  },

  _checklistSlotChanged: function (state, item) {
    const entry = item.entry || {};
    const persistedStatus = entry.status || "missing";
    const persistedNote = entry.reviewerNote || "";
    const effective = FL.criterionBSimpleReview._effectiveSlotDecision(state, item);
    return effective.status !== persistedStatus || effective.note !== persistedNote;
  },

  _checklistSlotBody: function (state, item, attachRemarks) {
    if (!FL.criterionBSimpleReview._checklistSlotChanged(state, item)) return null;
    const effective = FL.criterionBSimpleReview._effectiveSlotDecision(state, item);
    if (!effective.status) return null;
    const body = {
      evidenceSlot: item.slotId,
      status: effective.status,
      reviewerNote: effective.note
    };
    if (attachRemarks) body.remarks = state.bundleRemarks || "";
    return body;
  },

  _patchBundleStep: function (session, docId, body, stepLabel) {
    if (!body || !Object.keys(body).length) return Promise.resolve(null);
    return FL.criterionBEvidence.patchBundle(session, docId, body).catch(function (err) {
      const detail = err && err.message ? err.message : "Save failed.";
      throw new Error((stepLabel ? stepLabel + " — " : "") + detail);
    });
  },

  _persistReview: function (session, state, options) {
    options = options || {};
    const includeAssessment = options.includeAssessment === true;
    const docId = state.doc.id;
    let chain = Promise.resolve();
    let remarksAttached = false;

    if (state.bundle.claimType === "academic_program") {
      chain = chain.then(function () {
        return FL.criterionBSimpleReview._patchBundleStep(session, docId, {
          rrpaCopcApplicability: state.rrpa.value,
          rrpaCopcApplicabilityNote: state.rrpa.note,
          remarks: state.bundleRemarks || ""
        }, "Program applicability");
      });
      remarksAttached = !!(state.bundleRemarks || "").trim();
    }

    const changedSlots = state.items.filter(function (item) {
      return FL.criterionBSimpleReview._checklistSlotChanged(state, item);
    });
    changedSlots.forEach(function (item, idx) {
      chain = chain.then(function () {
        const attachRemarks = !remarksAttached && idx === 0 && state.bundle.claimType !== "academic_program";
        const body = FL.criterionBSimpleReview._checklistSlotBody(state, item, attachRemarks);
        if (attachRemarks && body) remarksAttached = true;
        return FL.criterionBSimpleReview._patchBundleStep(
          session,
          docId,
          body,
          "Document verification (" + (item.label || item.slotId) + ")"
        );
      });
    });

    chain = chain.then(function () {
      if (state.bundle.claimType === "academic_program") return null;
      const meta = {};
      if (state.specializationAligned != null) {
        meta.specializationAligned = state.specializationAligned === true;
      }
      if (!remarksAttached && (state.bundleRemarks || "").trim()) {
        meta.remarks = state.bundleRemarks;
        remarksAttached = true;
      }
      if (!Object.keys(meta).length) return null;
      return FL.criterionBSimpleReview._patchBundleStep(
        session,
        docId,
        meta,
        meta.specializationAligned != null ? "Specialization alignment" : "Reviewer feedback"
      );
    });

    chain = chain.then(function () {
      return FL.criterionBEvidence.fetchBundle(session, docId);
    }).then(function (payload) {
      FL.criterionBSimpleReview._mergePayloadIntoState(state, payload);
    });

    if (includeAssessment && state.canDecide && state.assessment && state.assessment.points) {
      chain = chain.then(function () {
        if (!state.validation || state.validation.readyForScoring !== true) {
          return Promise.reject(new Error(
            FL.criterionBWorkspaceUi.scoringBlockMessages(state, true).slice(0, 2).join(" ")
              || "Mandatory evidence is not complete or verified yet."
          ));
        }
        const just = (state.assessment.justification || "").trim();
        if (just.length < 10) {
          return Promise.reject(new Error("Assessment justification must be at least 10 characters."));
        }
        const assessBody = {
          reviewerAssessmentPoints: parseFloat(state.assessment.points),
          reviewerAssessmentJustification: just
        };
        if ((state.bundleRemarks || "").trim()) assessBody.remarks = state.bundleRemarks;
        return FL.criterionBSimpleReview._patchBundleStep(session, docId, assessBody, "Assessment score");
      }).then(function (resp) {
        if (resp && resp.validation) state.validation = resp.validation;
        if (resp && resp.document && resp.document.criterionBEvidence) {
          FL.criterionBSimpleReview._mergePayloadIntoState(state, {
            document: resp.document,
            validation: resp.validation
          });
        }
        return FL.criterionBEvidence.fetchBundle(session, docId);
      }).then(function (payload) {
        FL.criterionBSimpleReview._mergePayloadIntoState(state, payload);
      });
    }

    return chain.then(function () {
      return FL.store.refreshLiveDocument(session, docId);
    });
  },

  _contributionVerificationHtml: function (state) {
    const esc = FL.esc;
    const cv = state.contributionVerification || {};
    const recorded = cv.recordedContributionPercent;
    const ocr = cv.ocrSuggestedPercent;
    const match = cv.matchStatusLabel || "Not Confirmed";
    const confirmed = cv.confirmationStatus === "confirmed";
    const mismatch = cv.confirmationStatus === "mismatch";
    const legacy = cv.confirmationStatus === "legacy_grandfathered";
    const ocrLine = ocr != null
      ? esc(String(ocr)) + "% (OCR suggestion — verify the document)"
      : (cv.ocrAmbiguous ? "Multiple values detected — verify manually" : "Not detected from OCR");
    const warnMismatch = mismatch
      ? `<p class="note warn">The recorded contribution percentage does not match the reviewed Annex C. Resolve the difference before finalizing the assessment.</p>`
      : "";
    const btn = (!confirmed && !legacy && state.canDecide)
      ? `<button type="button" class="btn btn-primary" id="cb-confirm-contribution">Confirm Contribution Percentage</button>`
      : (legacy ? `<p class="note">Historical assessment preserved. Confirm when updating this review.</p>` : "");
    return `
      <section class="card cb-contribution-verify">
        <h3 class="cb-subhead">Contribution Verification</h3>
        <p><strong>Recorded contribution:</strong> ${recorded != null ? esc(String(recorded)) + "%" : "—"}</p>
        <p><strong>Annex C OCR suggestion:</strong> ${ocrLine}</p>
        <p><strong>Match status:</strong> ${esc(match)}</p>
        ${cv.ocrAdvisoryNote ? `<p class="note">${esc(cv.ocrAdvisoryNote)}</p>` : ""}
        ${warnMismatch}
        ${btn}
      </section>`;
  },

  _bindContributionVerification: function (session, state) {
    const btn = document.getElementById("cb-confirm-contribution");
    if (!btn) return;
    btn.addEventListener("click", function () {
      const cv = state.contributionVerification || {};
      const pct = cv.recordedContributionPercent;
      if (pct == null) {
        FL.ui.toast("Recorded contribution percentage is missing on this claim.", "warn");
        return;
      }
      btn.disabled = true;
      FL.criterionBEvidence.patchBundle(session, state.doc.id, {
        confirmContributionPercentage: true,
        confirmedContributionPercent: pct
      }).then(function (resp) {
        FL.criterionBSimpleReview._mergePayloadIntoState(state, resp);
        if (resp.contributionVerification) state.contributionVerification = resp.contributionVerification;
        FL.ui.toast("Contribution percentage confirmation saved.", "ok");
        FL.criterionBSimpleReview._renderStep(session, state);
      }).catch(function (err) {
        btn.disabled = false;
        FL.ui.toast(err.message || "Could not confirm contribution.", "danger");
      });
    });
  }
};
