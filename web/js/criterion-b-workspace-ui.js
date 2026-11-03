/**
 * KRA I Criterion B — reviewer workspace presentation (Phase 3).
 * Pure helpers; no API calls.
 */
window.FL = window.FL || {};

FL.criterionBWorkspaceUi = {
  IM_GROUPS: [
    {
      id: "textbook",
      label: "Textbook",
      indicatorIds: ["kra1-b-textbook-sole", "kra1-b-textbook-co"]
    },
    {
      id: "module",
      label: "Module",
      indicatorIds: ["kra1-b-module-sole", "kra1-b-module-co"]
    },
    {
      id: "manual",
      label: "Instructional Manual",
      indicatorIds: ["kra1-b-manual-sole", "kra1-b-manual-co"]
    },
    {
      id: "multimedia",
      label: "Multimedia Teaching Material",
      indicatorIds: ["kra1-b-multimedia-sole", "kra1-b-multimedia-co"]
    }
  ],

  PROGRAM_GROUP: {
    id: "academic_programs",
    label: "Academic Programs",
    indicatorIds: ["kra1-b-program-lead", "kra1-b-program-contributor"]
  },

  SLOT_LABELS: {
    primary_material: "Instructional material (primary file)",
    imdc_evaluation_approval: "IMDC or equivalent evaluation and approval",
    approved_syllabus: "Approved syllabus or course guide",
    library_certification: "Library certification",
    annex_c_contribution: "Annex C — Certificate of Contribution",
    complete_set_attestation: "Complete Set Supporting Document",
    originality_proof: "Originality proof",
    pedagogical_validity_proof: "Pedagogical validity proof",
    primary_contribution_document: "Primary contribution document",
    feasibility_study: "Feasibility study",
    benchmarking_report: "Benchmarking report",
    approved_program_outcomes: "Approved program outcomes",
    curriculum_obe_mapping: "Curriculum design / OBE mapping",
    revised_curriculum_stakeholder_consultation: "Revised curriculum & stakeholder consultation",
    dean_contribution_certification: "Dean certification of role and contribution",
    academic_council_resolution: "Academic Council resolution",
    governing_board_resolution: "Governing Board resolution",
    rrpa_or_copc: "RRPA or COPC (as applicable)",
    implementation_evidence: "Implementation evidence"
  },

  isCriterionBIndicator: function (indicatorId) {
    return !!(indicatorId && String(indicatorId).indexOf("kra1-b-") === 0);
  },

  isPrimaryClaimDocument: function (doc, allDocs) {
    if (!doc || doc.criterionId !== "kra1-b") return false;
    if (doc.criterionBEvidence && doc.criterionBEvidence.isSupportingDocument) return false;
    const apiLink = doc.criterionBEvidence && doc.criterionBEvidence.link;
    if (apiLink && apiLink.role === "supporting") return false;
    const link = doc.extractedInfo && (doc.extractedInfo.criterionBEvidenceLink || doc.extractedInfo.criterion_b_evidence_link);
    if (link && link.role === "supporting") return false;
    if (allDocs && FL.criterionBWorkspaceUi.isReferencedAsSupportingInAnyChecklist(doc.id, allDocs)) {
      return false;
    }
    const bundle = doc.criterionBEvidence && doc.criterionBEvidence.bundle;
    if (bundle && bundle.checklist) {
      const mainSlot = bundle.checklist.primary_material || bundle.checklist.primary_contribution_document;
      if (mainSlot && mainSlot.documentId && mainSlot.documentId !== doc.id) return false;
    }
    return true;
  },

  isReferencedAsSupportingInAnyChecklist: function (docId, docs) {
    if (!docId) return false;
    return (docs || []).some(function (primary) {
      const bundle = primary.criterionBEvidence && primary.criterionBEvidence.bundle;
      const checklist = bundle && bundle.checklist;
      if (!checklist) return false;
      return Object.keys(checklist).some(function (slotId) {
        if (slotId === "primary_material" || slotId === "primary_contribution_document") return false;
        const entry = checklist[slotId];
        return entry && entry.documentId === docId;
      });
    });
  },

  isCriterionBSupportingDocument: function (doc, allDocs) {
    if (!doc || doc.criterionId !== "kra1-b") return false;
    return !FL.criterionBWorkspaceUi.isPrimaryClaimDocument(doc, allDocs);
  },

  requiredEvidenceListHtml: function (item) {
    const ui = FL.criterionBWorkspaceUi;
    const esc = FL.esc;
    const validation = item.validation || {};
    const summary = validation.checklistSummary || {};
    const checklist = (item.bundle && item.bundle.checklist) || {};
    const slotIds = Object.keys(summary);
    if (!slotIds.length) {
      return item.supporting.length
        ? `<p class="note">Evidence requirements follow the active Criterion B rules for this accomplishment type. Linked files are listed below.</p>`
        : `<p class="note">No required evidence slots reported yet. Faculty should complete the evidence checklist on the primary upload.</p>`;
    }
    const rows = slotIds.map(function (slotId) {
      const st = summary[slotId] || (checklist[slotId] && checklist[slotId].status) || "missing";
      const meta = ui.evidenceRequirementStatusMeta(st);
      const label = ui.SLOT_LABELS[slotId] || slotId.replace(/_/g, " ");
      return `<li>
        <span class="cb-accomplishment-file-label">${esc(label)}</span>
        ${FL.ui.statusBadge(meta.badge === "approved" ? "approved" : meta.badge === "invalid" ? "invalid" : meta.badge === "reviewer-required" ? "reviewer-required" : "pending")}
        <span class="cb-evidence-status-text">${esc(meta.label)}</span>
      </li>`;
    }).join("");
    const flagNotes = (validation.flags || []).filter(function (f) {
      return f.indexOf("missing_") !== 0 && f.indexOf("reviewer_required_") !== 0;
    }).slice(0, 4).map(function (f) {
      return `<li class="note">${esc(ui.humanizeFlag(f))}</li>`;
    }).join("");
    return `<ul class="cb-required-evidence-list">${rows}</ul>${flagNotes ? `<ul class="cb-evidence-flag-notes">${flagNotes}</ul>` : ""}`;
  },

  evidenceRequirementStatusMeta: function (status) {
    const key = (status || "missing").toLowerCase();
    const map = {
      missing: { badge: "invalid", label: "Missing" },
      present_unverified: { badge: "pending", label: "Uploaded — pending review" },
      reviewer_required: { badge: "reviewer-required", label: "Pending review" },
      verified: { badge: "approved", label: "Verified" },
      not_applicable: { badge: "info", label: "Not applicable" }
    };
    return map[key] || { badge: "info", label: status || "Unknown" };
  },

  /** Reviewer-facing readiness rows (merges unsaved file decisions with bundle state). */
  buildReviewReadinessRows: function (state) {
    const ui = FL.criterionBWorkspaceUi;
    const rows = [];
    (state.items || []).forEach(function (item, fileIndex) {
      const draft = state.drafts && state.drafts[item.slotId];
      const persisted = (item.entry && item.entry.status) || "missing";
      const effective = draft ? draft.status : persisted;
      const docId = item.entry && item.entry.documentId;
      const fileDoc = item.fileDoc || (docId && FL.store ? FL.store.documentById(docId) : null);
      const docName = fileDoc
        ? (fileDoc.name || fileDoc.title || fileDoc.fileName || "Uploaded file")
        : (docId ? "Uploaded file" : "—");
      let upload = docId ? "Uploaded" : "Missing";
      let review = "Pending review";
      let action = "Open file " + (fileIndex + 1) + " and accept or request correction.";
      let ok = false;
      if (!docId) {
        review = "Missing";
        action = "Ask the faculty member to upload this document.";
      } else if (effective === "verified") {
        review = "Verified";
        action = "No further action for this file.";
        ok = true;
      } else if (effective === "reviewer_required") {
        review = "Needs correction";
        action = "Explain what must change, or wait for a replacement upload.";
      } else {
        review = "Pending review";
      }
      var rowLabel = item.label;
      if (item.slotId === "complete_set_attestation") {
        rowLabel = "Complete Set Supporting Document";
      }
      rows.push({
        slotId: item.slotId,
        label: rowLabel,
        documentName: docName,
        upload: upload,
        review: review,
        action: action,
        fileIndex: fileIndex,
        ok: ok
      });
    });
    const spec = state.specializationAligned != null
      ? state.specializationAligned
      : (state.bundle && state.bundle.specializationAligned);
    if (spec == null) {
      rows.push({
        slotId: "",
        label: "Field of specialization",
        documentName: "—",
        upload: "—",
        review: "Pending review",
        action: "Confirm whether this work aligns with the faculty member's specialization (step 2).",
        fileIndex: null,
        ok: false
      });
    } else if (spec === false) {
      rows.push({
        slotId: "",
        label: "Field of specialization",
        documentName: "—",
        upload: "—",
        review: "Not aligned",
        action: "This claim cannot score until alignment is resolved.",
        fileIndex: null,
        ok: false
      });
    }
    const bundle = state.bundle || {};
    const cv = state.contributionVerification;
    if (bundle.authorship === "co") {
      let okContrib = false;
      let review = "Not confirmed";
      let action = "Open the Annex C file, compare the certificate to the recorded percentage, then confirm.";
      if (cv && cv.confirmationStatus === "confirmed") {
        okContrib = true;
        review = "Confirmed";
        action = "Contribution percentage matches Annex C (reviewer confirmed).";
      } else if (cv && cv.confirmationStatus === "legacy_grandfathered") {
        okContrib = true;
        review = "Contribution Confirmation Required (historical)";
        action = "Existing assessment is preserved. Confirm Annex C when you next update this review.";
      } else if (cv && cv.confirmationStatus === "mismatch") {
        review = "Mismatch";
        action = "The recorded contribution percentage does not match the reviewed Annex C. Resolve the difference before finalizing the assessment.";
      } else if (cv && cv.confirmationStatus === "needs_clarification") {
        review = "Needs Clarification";
        action = "Clarify the contribution percentage with the faculty member before finalizing the assessment.";
      }
      rows.push({
        slotId: "annex_c_contribution",
        label: "Annex C contribution %",
        documentName: cv && cv.recordedContributionPercent != null
          ? String(cv.recordedContributionPercent) + "% recorded"
          : "—",
        upload: "—",
        review: review,
        action: action,
        fileIndex: null,
        ok: okContrib
      });
    }
    if (bundle.materialType === "module" || bundle.materialType === "instructional_manual") {
      var facultyComplete = bundle.completeSetDeclared === true;
      rows.push({
        slotId: "faculty_completeness_confirmation",
        label: "Faculty Completeness Confirmation",
        documentName: "—",
        upload: "—",
        review: facultyComplete ? "Confirmed" : "Not yet confirmed",
        action: facultyComplete
          ? "Faculty declared that the module or manual is a complete stand-alone material or complete set, as applicable."
          : "Ask the faculty member to confirm complete instructional material on their claim (mobile add-work or claim details).",
        fileIndex: null,
        ok: facultyComplete
      });
    }
    return rows;
  },

  canFinalizeReviewerScore: function (state) {
    const rows = FL.criterionBWorkspaceUi.buildReviewReadinessRows(state);
    return rows.length > 0 && rows.every(function (row) { return row.ok; });
  },

  scoringBlockMessages: function (state, preferServer) {
    const ui = FL.criterionBWorkspaceUi;
    if (preferServer && state.validation && state.validation.scoringBlockers && state.validation.scoringBlockers.length) {
      return state.validation.scoringBlockers.map(function (b) { return b.message; });
    }
    return ui.buildReviewReadinessRows(state).filter(function (r) { return !r.ok; }).map(function (r) {
      return r.label + ": " + r.review + ". " + r.action;
    });
  },

  reviewReadinessChecklistHtml: function (state, options) {
    const ui = FL.criterionBWorkspaceUi;
    const esc = FL.esc;
    const opt = options || {};
    const rows = ui.buildReviewReadinessRows(state);
    const canScore = ui.canFinalizeReviewerScore(state);
    const intro = opt.intro || "Before you can finish this review, please check:";
    const list = rows.map(function (row) {
      const jump = row.fileIndex != null && opt.showJump
        ? ` <button type="button" class="btn btn-ghost btn-small" data-goto-file="${row.fileIndex}">Open file</button>`
        : "";
      return `<li class="cb-readiness-row${row.ok ? " is-ok" : ""}">
        <strong>${esc(row.label)}</strong>
        <span class="cb-readiness-doc">${esc(row.documentName)}</span>
        <span class="cb-readiness-meta">${esc(row.upload)} · ${esc(row.review)}</span>
        <p class="note cb-readiness-action">${esc(row.action)}${jump}</p>
      </li>`;
    }).join("");
    return `<section class="cb-readiness${canScore ? " is-ready" : ""}">
      <h3 class="cb-subhead">${esc(intro)}</h3>
      <ul class="cb-readiness-list">${list}</ul>
      ${canScore
        ? "<p class=\"note\">All required evidence is verified. You may enter your assessment score.</p>"
        : "<p class=\"note warn\">You can save document decisions and feedback now. The faculty score stays <strong>Estimated</strong> until everything above is complete.</p>"}
    </section>`;
  },

  /** Group primaries with checklist-linked files; orphans are not guessed onto a claim. */
  buildCriterionBWorkspaceModel: function (docs) {
    const ui = FL.criterionBWorkspaceUi;
    const cbDocs = (docs || []).filter(function (d) {
      return d.criterionId === "kra1-b";
    });
    const docById = {};
    cbDocs.forEach(function (d) {
      docById[d.id] = d;
    });
    const primaries = cbDocs.filter(function (d) {
      return ui.isPrimaryClaimDocument(d, cbDocs);
    });
    const checklistLinkedIds = {};

    const supportingForPrimary = function (primary) {
      const bundle = primary.criterionBEvidence && primary.criterionBEvidence.bundle;
      const checklist = (bundle && bundle.checklist) || {};
      const items = [];
      Object.keys(checklist).forEach(function (slotId) {
        const entry = checklist[slotId];
        if (!entry || !entry.documentId) return;
        if (slotId === "primary_material" || slotId === "primary_contribution_document") return;
        checklistLinkedIds[entry.documentId] = true;
        const st = entry.status || "missing";
        items.push({
          slotId: slotId,
          slotLabel: ui.SLOT_LABELS[slotId] || slotId.replace(/_/g, " "),
          documentId: entry.documentId,
          document: docById[entry.documentId] || null,
          status: st,
          statusMeta: ui.slotStatusMeta(st)
        });
      });
      items.sort(function (a, b) {
        return a.slotLabel.localeCompare(b.slotLabel);
      });
      return items;
    };

    const accomplishments = primaries.map(function (primary) {
      const bundle = primary.criterionBEvidence && primary.criterionBEvidence.bundle;
      const checklist = (bundle && bundle.checklist) || {};
      const mainSlot = checklist.primary_material || checklist.primary_contribution_document;
      const mainDocId = (mainSlot && mainSlot.documentId) || primary.id;
      return {
        primary: primary,
        bundle: bundle,
        validation: primary.criterionBEvidence && primary.criterionBEvidence.validation,
        scoring: primary.criterionBEvidence && primary.criterionBEvidence.scoring,
        mainDocumentId: mainDocId,
        mainDocument: docById[mainDocId] || primary,
        supporting: supportingForPrimary(primary)
      };
    });

    accomplishments.sort(function (a, b) {
      const ta = ui.claimTitle(a.bundle || {});
      const tb = ui.claimTitle(b.bundle || {});
      return ta.localeCompare(tb);
    });

    const needsLinking = cbDocs.filter(function (d) {
      if (ui.isPrimaryClaimDocument(d, cbDocs)) return false;
      if (checklistLinkedIds[d.id]) return false;
      return true;
    });

    return { accomplishments: accomplishments, needsLinking: needsLinking };
  },

  accomplishmentReviewCardHtml: function (item, options) {
    const ui = FL.criterionBWorkspaceUi;
    const esc = FL.esc;
    const opt = options || {};
    const primary = item.primary;
    const bundle = item.bundle || {};
    const validation = item.validation || {};
    const vMeta = ui.validationStatusMeta(validation.validationStatus);
    const kind = bundle.claimType === "academic_program" ? "Academic Program" : "Teaching Material";
    const mainDoc = item.mainDocument || primary;
    const mainName = (mainDoc && (mainDoc.name || mainDoc.title || mainDoc.fileName)) || ui.linkedDocumentLabel(item.mainDocumentId);
    const reviewHref = opt.reviewHref ? opt.reviewHref(primary) : "#";
    const reviewLabel = opt.isAdmin ? "Open review" : "Review & Give Score";
    const scoring = item.scoring || {};
    const display = scoring.displayScore || {};
    const displayPts = display.points != null ? String(display.points) : null;
    const displayLabel = display.label || "Estimated";
    const evidenceHtml = ui.requiredEvidenceListHtml(item);
    const supportingHtml = item.supporting.length
      ? `<ul class="cb-accomplishment-files">${item.supporting.map(function (row) {
          const fileName = row.document
            ? (row.document.name || row.document.title || row.document.fileName || "Uploaded file")
            : ui.linkedDocumentLabel(row.documentId) + " (not in document list)";
          return `<li>
            <span class="cb-accomplishment-file-label">${esc(row.slotLabel)}</span>
            <span class="cb-accomplishment-file-name">${esc(fileName)}</span>
            ${FL.ui.statusBadge(row.statusMeta.badge === "approved" ? "approved" : row.statusMeta.badge === "invalid" ? "invalid" : row.statusMeta.badge === "reviewer-required" ? "reviewer-required" : "pending")}
          </li>`;
        }).join("")}</ul>`
      : `<p class="note cb-accomplishment-no-support">No supporting files linked in the evidence checklist yet.</p>`;
    return `<article class="card cb-accomplishment-card">
      <header class="cb-accomplishment-head">
        <div>
          <p class="cb-eyebrow">${esc(kind)}</p>
          <h3>${esc(ui.claimTitle(bundle))}</h3>
        </div>
        ${FL.ui.statusBadge(vMeta.badge === "approved" ? "approved" : vMeta.badge === "invalid" ? "invalid" : vMeta.badge === "reviewer-required" ? "reviewer-required" : "pending")}
      </header>
      <p class="cb-accomplishment-main"><strong>Main document:</strong> ${esc(mainName)}</p>
      <h4 class="cb-subhead">Required evidence</h4>
      ${evidenceHtml}
      <h4 class="cb-subhead">Linked supporting files</h4>
      ${supportingHtml}
      <div class="cb-accomplishment-scoring">
        <p class="cb-current-score"><strong>${esc(displayLabel)}:</strong> ${displayPts != null ? esc(displayPts) + " pts" : "Not available yet"}</p>
        <p class="note">One score per accomplishment. Reviewer assessment replaces the estimated display after you save a completed review. Official verified points follow published rules separately.</p>
      </div>
      <div class="cb-accomplishment-actions">
        <a class="btn btn-primary" href="${esc(reviewHref)}">${esc(reviewLabel)}</a>
      </div>
    </article>`;
  },

  needsLinkingSectionHtml: function (orphanDocs) {
    const ui = FL.criterionBWorkspaceUi;
    const esc = FL.esc;
    const list = orphanDocs || [];
    if (!list.length) return "";
    return `<section class="cb-needs-linking">
      <h3 class="evidence-section-title">Needs linking</h3>
      <p class="note">These Criterion B uploads are not attached to any accomplishment checklist. Do not treat them as separate accomplishments.</p>
      <ul class="cb-needs-linking-list">${list.map(function (doc) {
        const link = doc.criterionBEvidence && doc.criterionBEvidence.link;
        const slot = link && link.evidenceSlot ? ui.SLOT_LABELS[link.evidenceSlot] || link.evidenceSlot : null;
        const name = doc.name || doc.title || doc.fileName || doc.id;
        const hint = link && link.primaryDocumentId
          ? `Metadata points to primary ${link.primaryDocumentId}${slot ? " (" + slot + ")" : ""} but this file is not in that claim checklist.`
          : "No checklist slot on a primary accomplishment.";
        return `<li class="cb-needs-linking-item">
          <strong>${esc(name)}</strong>
          <p class="sub">${esc(hint)}</p>
        </li>`;
      }).join("")}</ul>
    </section>`;
  },

  criterionBReviewWorkspaceHtml: function (params) {
    const ui = FL.criterionBWorkspaceUi;
    const esc = FL.esc;
    const critLabel = params.criterionLabel || "Criterion B";
    const personName = params.personName || "this faculty member";
    const model = ui.buildCriterionBWorkspaceModel(params.documents || []);
    const cards = model.accomplishments.map(function (item) {
      return ui.accomplishmentReviewCardHtml(item, {
        reviewHref: params.reviewHref,
        isAdmin: params.isAdmin
      });
    }).join("");
    const linking = ui.needsLinkingSectionHtml(model.needsLinking);
    return `
      <h2 class="evidence-section-title">${esc(critLabel)}</h2>
      <p class="note">Review workspace for ${esc(personName)}. Each card is one faculty accomplishment with its linked supporting files. Use <strong>Review &amp; Give Score</strong> to verify documents and enter your professional assessment.</p>
      ${model.accomplishments.length
        ? `<div class="cb-accomplishment-list">${cards}</div>`
        : FL.ui.empty("No accomplishments yet", "This faculty member has not saved a teaching material or academic program under Criterion B.")}
      ${linking}`;
  },

  validationStatusMeta: function (status) {
    const key = (status || "incomplete").toLowerCase();
    const map = {
      incomplete: { badge: "pending", label: "Incomplete" },
      reviewer_required: { badge: "reviewer-required", label: "Reviewer review required" },
      valid: { badge: "approved", label: "Ready for scoring (reviewer verified)" },
      invalid: { badge: "invalid", label: "Invalid / disqualified" }
    };
    return map[key] || { badge: "info", label: status || "Unknown" };
  },

  slotStatusMeta: function (status) {
    const key = (status || "missing").toLowerCase();
    const map = {
      missing: { badge: "invalid", label: "Not uploaded" },
      present_unverified: { badge: "pending", label: "Uploaded — verify" },
      reviewer_required: { badge: "reviewer-required", label: "Needs more evidence" },
      verified: { badge: "approved", label: "Verified" },
      not_applicable: { badge: "info", label: "Not applicable" }
    };
    return map[key] || { badge: "info", label: status };
  },

  humanizeFlag: function (flag) {
    const map = {
      rrpa_copc_applicability_undetermined:
        "Decide whether RRPA or COPC applies before this program claim can score.",
      missing_imdc_evaluation_approval: "IMDC or equivalent approval is still required.",
      missing_library_certification: "Library certification is still required.",
      missing_approved_syllabus: "Approved syllabus or course guide is still required.",
      missing_complete_set_attestation: "Complete set attestation is still required.",
      missing_dean_contribution_certification: "Dean certification is still required.",
      missing_implementation_evidence: "Implementation evidence is still required."
    };
    if (map[flag]) return map[flag];
    if (flag && flag.indexOf("missing_") === 0) {
      const slot = flag.slice("missing_".length);
      const label = FL.criterionBWorkspaceUi.SLOT_LABELS[slot] || slot.replace(/_/g, " ");
      return "Still required: " + label;
    }
    return (flag || "").replace(/_/g, " ");
  },

  linkedDocumentLabel: function (docId) {
    if (!docId) return "—";
    const docs = FL.store && FL.store.documents ? FL.store.documents : [];
    const hit = docs.find(function (d) { return d.id === docId; });
    if (hit && (hit.name || hit.title)) return hit.name || hit.title;
    return "Uploaded file";
  },

  slotPurpose: function (slotId) {
    const purposes = {
      primary_material: "Main instructional file for this claim.",
      imdc_evaluation_approval: "IMDC or equivalent evaluation and approval.",
      approved_syllabus: "Official syllabus or course guide.",
      library_certification: "Library availability certification.",
      rrpa_or_copc: "RRPA or COPC when applicable (reviewer decides).",
      implementation_evidence: "Evidence the program change is implemented.",
      dean_contribution_certification: "Dean certification of role and contribution."
    };
    return purposes[slotId] || "";
  },

  claimTitle: function (bundle) {
    if (!bundle) return "Criterion B claim";
    if (bundle.claimType === "academic_program") {
      return bundle.programName || "Academic program claim";
    }
    return bundle.materialTitle || "Instructional material claim";
  },

  claimTypeLabel: function (bundle) {
    if (!bundle) return "—";
    if (bundle.claimType === "academic_program") return "Academic program development / revision";
    return "Instructional material";
  },

  programKindLabel: function (kind) {
    if (kind === "new_program") return "New program";
    if (kind === "substantial_revision") return "Substantial revision";
    return "Not specified";
  },

  rrpaApplicabilityLabel: function (bundle, validation) {
    const key =
      (validation && validation.rrpaCopcApplicability) ||
      (bundle && bundle.rrpaCopcApplicability) ||
      (bundle &&
        bundle.rrpaCopcApplicabilityDecision &&
        bundle.rrpaCopcApplicabilityDecision.status) ||
      "unknown";
    const map = {
      unknown: "Undetermined — reviewer must decide",
      applicable: "Applicable — RRPA or COPC required when verified",
      not_applicable: "Not applicable — documented exemption"
    };
    return map[key] || key;
  },

  rrpaApplicabilityControlsHtml: function (bundle, canEdit) {
    if (!bundle || bundle.claimType !== "academic_program" || !canEdit) return "";
    const ui = FL.criterionBWorkspaceUi;
    const esc = FL.esc;
    const decision = bundle.rrpaCopcApplicabilityDecision || {};
    const current =
      decision.status || bundle.rrpaCopcApplicability || "unknown";
    const note = bundle.rrpaCopcApplicabilityNote || decision.note || "";
    return `<div class="cb-rrpa-applicability">
      <h3 class="cb-subhead">RRPA / COPC applicability (reviewer)</h3>
      <p class="note">Annex A requires RRPA or COPC when applicable. Missing documents do not imply exemption.</p>
      <label for="cb-rrpa-applicability">Applicability decision</label>
      <select id="cb-rrpa-applicability">
        <option value="unknown"${current === "unknown" ? " selected" : ""}>Undetermined</option>
        <option value="applicable"${current === "applicable" ? " selected" : ""}>Applicable</option>
        <option value="not_applicable"${current === "not_applicable" ? " selected" : ""}>Not applicable (exemption)</option>
      </select>
      <label for="cb-rrpa-applicability-note">Applicability note (required for exemption)</label>
      <textarea id="cb-rrpa-applicability-note" rows="2" placeholder="Audit trail for exemption or applicability context">${esc(note)}</textarea>
    </div>`;
  },

  informationalScoringPreview: function (bundle, validation, indicatorId) {
    const hit = FL.rules && FL.rules.findIndicator ? FL.rules.findIndicator(indicatorId) : null;
    const indicator = hit && hit.indicator;
    const base = indicator && typeof indicator.points === "number" ? indicator.points : null;
    const note = "Informational preview only. Official eligibility is determined by reviewer-verified evidence, not OCR or uploads alone.";
    if (!validation || !validation.readyForScoring) {
      return {
        points: null,
        basePoints: base,
        note: note + " Bundle is not ready for scoring yet."
      };
    }
    let points = base;
    if (bundle && bundle.authorship === "co" && bundle.contributionPercent != null && base != null) {
      points = Math.round(base * (Number(bundle.contributionPercent) / 100) * 100) / 100;
    }
    return {
      points: points,
      basePoints: base,
      note: note
    };
  },

  indicatorNavHtml: function (criterion, docs, options) {
    const ui = FL.criterionBWorkspaceUi;
    const esc = FL.esc;
    const allDocs = docs || [];
    const primaryDocs = allDocs.filter(function (d) {
      return ui.isPrimaryClaimDocument(d, allDocs);
    });
    const countFor = function (indicatorId) {
      return primaryDocs.filter(function (d) { return d.indicatorId === indicatorId; }).length;
    };
    const renderButtons = function (indicatorIds) {
      return indicatorIds.map(function (id) {
        const hit = FL.rules.findIndicator(id);
        const name = hit ? hit.indicator.name : id;
        const count = countFor(id);
        return `<button type="button" class="evidence-ind-open" data-indicator="${esc(id)}">
          <span>${esc(name)}</span>
          <small>${count} primary claim${count === 1 ? "" : "s"}</small>
        </button>`;
      }).join("");
    };
    const imHtml = ui.IM_GROUPS.map(function (group) {
      return `<div class="cb-ind-group">
        <h3 class="cb-ind-group-title">${esc(group.label)}</h3>
        <div class="evidence-ind-grid">${renderButtons(group.indicatorIds)}</div>
      </div>`;
    }).join("");
    const progHtml = `<div class="cb-ind-group">
      <h3 class="cb-ind-group-title">${esc(ui.PROGRAM_GROUP.label)}</h3>
      <div class="evidence-ind-grid">${renderButtons(ui.PROGRAM_GROUP.indicatorIds)}</div>
    </div>`;
    return `<div class="cb-indicator-nav" aria-label="Criterion B indicators">
      <p class="note">Instructional materials and academic programs use separate evidence bundles. Supporting files are linked to a primary claim and do not earn separate points.</p>
      <section class="cb-ind-category" aria-label="Instructional materials">
        <h2 class="evidence-section-title">Instructional Materials</h2>
        ${imHtml}
      </section>
      <section class="cb-ind-category" aria-label="Academic programs">
        <h2 class="evidence-section-title">Academic Programs</h2>
        ${progHtml}
      </section>
    </div>`;
  },

  crossKraWarningsHtml: function (warnings) {
    const list = warnings || [];
    if (!list.length) {
      return `<p class="note">No cross-KRA overlap hints for this claim.</p>`;
    }
    return `<ul class="cb-cross-kra-list">${list.map(function (w) {
      const conf = w.confidence === "confirmed" ? "Confirmed hint" : "Uncertain — review manually";
      return `<li class="cb-cross-kra-item">
        <span class="ev-pill ev-pill-warn">${FL.esc(conf)}</span>
        <p>${FL.esc(w.message || w.code || "Cross-KRA warning")}</p>
        ${w.relatedDocumentId ? `<p class="sub">Related document: ${FL.esc(w.relatedDocumentId)}</p>` : ""}
      </li>`;
    }).join("")}</ul>`;
  },

  checklistHtml: function (bundle, checklistSummary, options) {
    const ui = FL.criterionBWorkspaceUi;
    const esc = FL.esc;
    const checklist = (bundle && bundle.checklist) || {};
    const slots = Object.keys(checklist).sort();
    if (!slots.length) {
      return `<p class="note">No checklist initialized for this claim.</p>`;
    }
    const canEdit = options && options.canEdit;
    return `<div class="cb-checklist-cards">${slots.map(function (slotId) {
        const entry = checklist[slotId] || {};
        const st = (checklistSummary && checklistSummary[slotId]) || entry.status || "missing";
        const meta = ui.slotStatusMeta(st);
        const docId = entry.documentId || "";
        const label = ui.SLOT_LABELS[slotId] || slotId.replace(/_/g, " ");
        const purpose = ui.slotPurpose(slotId);
        const ocrHint = entry.ocrHintOnly ? `<p class="sub">Automatic text read — not verified</p>` : "";
        const note = entry.reviewerNote ? `<p class="sub">${esc(entry.reviewerNote)}</p>` : "";
        const fileLabel = ui.linkedDocumentLabel(docId);
        const actionBlock = canEdit
          ? `<div class="cb-checklist-actions">
              <label class="cb-checklist-action-label">Your verification</label>
              <select class="cb-slot-status" data-cb-slot="${esc(slotId)}" aria-label="${esc(label)} verification">
              <option value="present_unverified"${st === "present_unverified" ? " selected" : ""}>Uploaded — not verified yet</option>
              <option value="reviewer_required"${st === "reviewer_required" ? " selected" : ""}>Ask faculty for more evidence</option>
              <option value="verified"${st === "verified" ? " selected" : ""}>Verified — acceptable</option>
              <option value="missing"${st === "missing" ? " selected" : ""}>Not received</option>
              ${slotId === "rrpa_or_copc" ? `<option value="not_applicable"${st === "not_applicable" ? " selected" : ""}>Not applicable</option>` : ""}
            </select>
            <input type="text" class="cb-slot-note" data-cb-slot-note="${esc(slotId)}" placeholder="Note to faculty (optional)" value="${esc(entry.reviewerNote || "")}" /></div>`
          : "";
        return `<article class="cb-checklist-card">
          <header class="cb-checklist-card-head">
            <h4>${esc(label)}</h4>
            ${FL.ui.statusBadge(meta.badge === "approved" ? "approved" : meta.badge === "invalid" ? "invalid" : meta.badge === "reviewer-required" ? "reviewer-required" : "pending")}
          </header>
          ${purpose ? `<p class="note">${esc(purpose)}</p>` : ""}
          <p class="cb-checklist-status"><strong>Status:</strong> ${esc(meta.label)}</p>
          <p class="cb-checklist-file"><strong>File:</strong> ${esc(fileLabel)}</p>
          ${ocrHint}${note}${actionBlock}
        </article>`;
      }).join("")}</div>`;
  },

  claimSummaryHtml: function (doc, bundle, validation, crossWarnings, preview, ocrDoc, options) {
    const canEdit = options && options.canEdit;
    const sourceDoc = ocrDoc || doc;
    const ui = FL.criterionBWorkspaceUi;
    const esc = FL.esc;
    const vMeta = ui.validationStatusMeta(validation && validation.validationStatus);
    const isProgram = bundle && bundle.claimType === "academic_program";
    let detailRows = "";
    if (isProgram) {
      detailRows = `
        ${FL.documents.kvRow("Program name", esc(bundle.programName || "—"), false)}
        ${FL.documents.kvRow("Development type", esc(ui.programKindLabel(bundle.programDevelopmentKind)), false)}
        ${FL.documents.kvRow("Faculty role", esc(bundle.facultyRole || "—"), false)}
        ${FL.documents.kvRow("Contribution description", esc(bundle.contributionDescription || "—"), false)}
        ${FL.documents.kvRow("Committee name", esc(bundle.committeeName || "—"), false)}
        ${FL.documents.kvRow("RRPA/COPC applicability", esc(ui.rrpaApplicabilityLabel(bundle, validation)), false)}
        ${(validation && validation.rrpaCopcApplicabilityNote) || (bundle.rrpaCopcApplicabilityNote)
          ? FL.documents.kvRow(
              "RRPA/COPC applicability note",
              esc((validation && validation.rrpaCopcApplicabilityNote) || bundle.rrpaCopcApplicabilityNote || "—"),
              false
            )
          : ""}`;
    } else {
      detailRows = `
        ${FL.documents.kvRow("Material title", esc(bundle.materialTitle || "—"), false)}
        ${FL.documents.kvRow("Material type", esc(bundle.materialType || "—"), false)}
        ${FL.documents.kvRow("Authorship", esc(bundle.authorship || "—"), false)}
        ${bundle.authorship === "co" ? FL.documents.kvRow("Contribution %", esc(bundle.contributionPercent == null ? "—" : String(bundle.contributionPercent)), false) : ""}
        ${FL.documents.kvRow("Faculty completeness confirmation", bundle.completeSetDeclared === true ? "Confirmed" : bundle.completeSetDeclared === false ? "Not confirmed" : "—", false)}
        ${FL.documents.kvRow("Specialization aligned", bundle.specializationAligned === true ? "Yes" : bundle.specializationAligned === false ? "No" : "Pending", false)}`;
    }
    const flags = (validation && validation.flags) || [];
    const blockers = (validation && validation.blockers) || [];
    const flagHtml = flags.length
      ? `<ul class="cb-flag-list">${flags.map(function (f) { return `<li>${esc(ui.humanizeFlag(f))}</li>`; }).join("")}</ul>`
      : "";
    const previewPts = preview && preview.points != null ? String(preview.points) : "Not available yet";
    const nextAction = validation && validation.readyForScoring
      ? "This accomplishment is ready for informational scoring preview."
      : validation && validation.validationStatus === "incomplete"
        ? "Faculty must upload missing documents before you can verify all items."
        : "Review each checklist item and save your decisions.";
    const ocrAside = sourceDoc && sourceDoc.ocr && sourceDoc.ocr.status === "completed"
      ? `<details class="cb-ocr-details"><summary>Optional: automatic text extraction</summary>
         <p class="note">OCR status: ${esc(sourceDoc.ocr.status || "pending")}. This does not verify documents.</p></details>`
      : "";
    return `<section class="card review-section cb-evidence-panel" id="criterion-b-evidence-panel">
      <div class="card-head">
        <div>
          <p class="cb-eyebrow">${esc(ui.claimTypeLabel(bundle))}</p>
          <h2>${esc(ui.claimTitle(bundle))}</h2>
        </div>
        ${FL.ui.statusBadge(vMeta.badge === "approved" ? "approved" : vMeta.badge === "invalid" ? "invalid" : vMeta.badge === "reviewer-required" ? "reviewer-required" : "pending")}
      </div>
      <div class="cb-review-next alert alert-info"><strong>Next step:</strong> ${esc(nextAction)}</div>
      <p class="note">Verify each uploaded document. Automatic text reading is optional background information only.</p>
      <div class="cb-review-grid">
        <div class="cb-review-summary">
          <h3 class="cb-subhead">Accomplishment summary</h3>
          <div class="kv-grid kv-grid--compact">${detailRows}</div>
          <div class="kv-grid kv-grid--compact cb-review-meta">
            ${FL.documents.kvRow("Validation", esc(vMeta.label), false)}
            ${FL.documents.kvRow("Ready for scoring (informational)", validation && validation.readyForScoring ? "Yes" : "No", false)}
            ${FL.documents.kvRow("Points preview (informational)", previewPts, false)}
          </div>
          ${preview && preview.note ? `<p class="note">${esc(preview.note)}</p>` : ""}
          ${blockers.length ? `<div class="alert alert-danger"><strong>Cannot proceed until resolved</strong><ul>${blockers.map(function (b) { return `<li>${esc(ui.humanizeFlag(b))}</li>`; }).join("")}</ul></div>` : ""}
          ${flagHtml ? `<h3 class="cb-subhead">Outstanding for faculty</h3>${flagHtml}` : ""}
          ${ocrAside}
        </div>
        <div class="cb-review-checklist">
          ${isProgram ? ui.rrpaApplicabilityControlsHtml(bundle, canEdit) : ""}
          <h3 class="cb-subhead">Evidence checklist</h3>
          <div id="cb-checklist-host"></div>
          <div class="cb-remarks">
            <label for="cb-bundle-remarks">Comments for faculty</label>
            <textarea id="cb-bundle-remarks" rows="3" placeholder="Explain what you verified or what is still needed">${esc((bundle && bundle.reviewerRemarks) || "")}</textarea>
          </div>
          ${isProgram ? `<label class="cb-disqualify"><input type="checkbox" id="cb-disqualify" ${bundle.reviewerDisqualificationConfirmed ? "checked" : ""} /> Confirm this claim is not eligible (disqualify)</label>` : ""}
        </div>
      </div>
      ${isProgram ? `<h3 class="cb-subhead">Cross-KRA notices</h3>${ui.crossKraWarningsHtml(crossWarnings)}` : ""}
      <div class="cb-evidence-actions" id="cb-evidence-actions"></div>
    </section>`;
  }
};
