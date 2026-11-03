/**
 * KRA I Criterion B — reviewer API integration and document review panel.
 */
window.FL = window.FL || {};

FL.criterionBEvidence = {
  bundlePath: function (session, docId) {
    if (!docId) return "";
    if (session && session.role === "reviewer") {
      return "/api/reviewer/documents/" + encodeURIComponent(docId) + "/criterion-b/evidence-bundle";
    }
    if (session && session.role === "administrator") {
      return "/api/admin/documents/" + encodeURIComponent(docId) + "/criterion-b/evidence-bundle";
    }
    return "";
  },

  fetchBundle: function (session, docId) {
    const path = FL.criterionBEvidence.bundlePath(session, docId);
    if (!path || !FL.store.usesLiveDocuments()) {
      return Promise.reject(new Error("Criterion B evidence bundles require a live reviewer session."));
    }
    return FL.apiClient.adminRequest("GET", path);
  },

  patchBundle: function (session, docId, body) {
    const path = FL.criterionBEvidence.bundlePath(session, docId);
    if (!path || !FL.store.usesLiveDocuments()) {
      return Promise.reject(new Error("Criterion B evidence updates require a live reviewer session."));
    }
    return FL.apiClient.adminRequest("PATCH", path, body || {});
  },

  supportingDocsForPrimary: function (primaryDocId, facultyId) {
    return (FL.store.documents || []).filter(function (d) {
      if (facultyId && d.facultyId !== facultyId) return false;
      const ev = d.criterionBEvidence;
      if (ev && ev.link && ev.link.primaryDocumentId === primaryDocId) return true;
      const link = d.extractedInfo && d.extractedInfo.criterionBEvidenceLink;
      return link && link.role === "supporting" && link.primaryDocumentId === primaryDocId;
    });
  },

  mountReviewPanel: function (session, doc, canDecide, hostId) {
    const host = document.getElementById(hostId || "criterion-b-evidence-slot");
    if (!host) return Promise.resolve();
    if (doc.criterionId !== "kra1-b" || !FL.criterionBWorkspaceUi.isPrimaryClaimDocument(doc)) {
      host.innerHTML = "";
      return Promise.resolve();
    }
    if (!FL.store.usesLiveDocuments()) {
      host.innerHTML = `<section class="card review-section"><p class="note">Criterion B evidence bundles are available when signed in to the live API.</p></section>`;
      return Promise.resolve();
    }
    if (session.role === "administrator" && doc.criterionBEvidence) {
      FL.criterionBEvidence._renderReviewPanel(session, doc, false, host, doc.criterionBEvidence);
      return Promise.resolve();
    }
    host.innerHTML = FL.ui.loading("Loading Criterion B evidence bundle…");
    return FL.criterionBEvidence.fetchBundle(session, doc.id).then(function (payload) {
      FL.criterionBEvidence._renderReviewPanel(session, doc, canDecide, host, payload);
    }).catch(function (err) {
      host.innerHTML = `<section class="card review-section"><p class="alert alert-danger">${FL.esc(err.message || "Could not load evidence bundle.")}</p></section>`;
    });
  },

  _renderReviewPanel: function (session, doc, canDecide, host, payload) {
    const bundle = payload.bundle;
    const validation = payload.validation || {};
    const cross = payload.crossKraWarnings || [];
    const preview = FL.criterionBWorkspaceUi.informationalScoringPreview(bundle, validation, doc.indicatorId);
    host.innerHTML = FL.criterionBWorkspaceUi.claimSummaryHtml(
      doc,
      bundle,
      validation,
      cross,
      preview,
      doc,
      { canEdit: !!canDecide }
    );
    const checklistHost = document.getElementById("cb-checklist-host");
    if (checklistHost) {
      checklistHost.innerHTML = FL.criterionBWorkspaceUi.checklistHtml(
        bundle,
        validation.checklistSummary,
        { canEdit: !!canDecide }
      );
    }
    const supporting = FL.criterionBEvidence.supportingDocsForPrimary(doc.id, doc.facultyId);
    const actions = document.getElementById("cb-evidence-actions");
    if (actions) {
      const reviewBase = session.role === "administrator" ? "document-view.html" : "document-review.html";
      const list = supporting.length
        ? `<ul class="cb-supporting-list">${supporting.map(function (s) {
            const href = FL.evidence.reviewDocHref(s, reviewBase);
            var slot = (s.criterionBEvidence && s.criterionBEvidence.link && s.criterionBEvidence.link.evidenceSlot) || "";
            var slotLabel = slot && FL.criterionBWorkspaceUi.SLOT_LABELS[slot]
              ? FL.criterionBWorkspaceUi.SLOT_LABELS[slot]
              : "Supporting file";
            return `<li><a href="${href}">${FL.esc(s.name || s.title || "Uploaded file")}</a> <span class="sub">(${FL.esc(slotLabel)})</span></li>`;
          }).join("")}</ul>`
        : `<p class="note">No linked supporting uploads found in the local document list.</p>`;
      actions.innerHTML = `<h3 class="cb-subhead">Linked supporting documents</h3>${list}
        ${canDecide ? `<button type="button" class="btn btn-primary btn-small" id="cb-save-checklist">Save verification &amp; comments</button>` : ""}`;
    }
    if (canDecide) {
      FL.criterionBEvidence._bindReviewPanel(session, doc, bundle);
    }
  },

  _bindReviewPanel: function (session, doc, bundle) {
    const saveBtn = document.getElementById("cb-save-checklist");
    if (!saveBtn) return;
    saveBtn.addEventListener("click", function () {
      const selects = Array.prototype.slice.call(document.querySelectorAll(".cb-slot-status"));
      const remarks = (document.getElementById("cb-bundle-remarks") || {}).value || "";
      const disqualify = document.getElementById("cb-disqualify");
      const rrpaSelect = document.getElementById("cb-rrpa-applicability");
      const rrpaNoteEl = document.getElementById("cb-rrpa-applicability-note");
      let chain = Promise.resolve();
      if (bundle.claimType === "academic_program" && rrpaSelect) {
        chain = chain.then(function () {
          return FL.criterionBEvidence.patchBundle(session, doc.id, {
            rrpaCopcApplicability: rrpaSelect.value,
            rrpaCopcApplicabilityNote: rrpaNoteEl ? rrpaNoteEl.value : "",
            remarks: remarks
          });
        });
      }
      selects.forEach(function (sel, idx) {
        chain = chain.then(function () {
          const slot = sel.getAttribute("data-cb-slot");
          const noteEl = document.querySelector('[data-cb-slot-note="' + slot + '"]');
          const body = {
            evidenceSlot: slot,
            status: sel.value,
            reviewerNote: noteEl ? noteEl.value : ""
          };
          if (!rrpaSelect && idx === 0) body.remarks = remarks;
          if (idx === selects.length - 1 && bundle.claimType === "academic_program" && disqualify) {
            body.disqualificationConfirmed = !!disqualify.checked;
          }
          return FL.criterionBEvidence.patchBundle(session, doc.id, body);
        });
      });
      chain.then(function () {
        return FL.store.refreshLiveDocument(session, doc.id);
      }).then(function (fresh) {
        if (fresh) Object.assign(doc, fresh);
        return FL.criterionBEvidence.fetchBundle(session, doc.id);
      }).then(function (payload) {
        const host = document.getElementById("criterion-b-evidence-slot");
        FL.criterionBEvidence._renderReviewPanel(session, doc, true, host, payload);
        FL.ui.toast("Verification saved. Faculty will see your updates after refresh.", "ok");
      }).catch(function (err) {
        FL.ui.toast(err.message || "Could not save checklist.", "danger");
      });
    });
  }
};
