/**
 * KRA II — guided reviewer review (Criteria A, B, C).
 */
window.FL = window.FL || {};

FL.kra2AReview = {
  _APPROVED_TOAST_KEY: "fl_kra2a_accomplishment_approved_toast",
  _workspaceMountSeq: 0,
  _activeReviewState: null,
  _reviewSession: null,
  _pageDelegationBound: false,

  _reviewHref: function (doc) {
    var crit = (doc && doc.criterionId) || "kra2-a";
    var base = "document-review.html?id=" + encodeURIComponent(doc.id || doc.documentId);
    var q = [
      doc.facultyId ? "faculty=" + encodeURIComponent(doc.facultyId) : "",
      "kra=kra2",
      "criterion=" + encodeURIComponent(crit)
    ].filter(Boolean).join("&");
    return base + "&" + q;
  },

  _isKra2Criterion: function (criterionKey) {
    return criterionKey === "kra2-a" || criterionKey === "kra2-b" || criterionKey === "kra2-c";
  },

  _paintKra2Stats: function (summary) {
    var host = document.getElementById("evidence-stats");
    if (!host || !summary) return;
    var counts = summary.reviewCounts || {};
    var cards = [
      { label: "Total accomplishments", value: summary.accomplishmentCount != null ? summary.accomplishmentCount : 0 },
      { label: "Under review", value: counts.pending != null ? counts.pending : 0 },
      { label: "Approved", value: counts.approved != null ? counts.approved : 0 },
      { label: "Needs changes", value: counts.rejected != null ? counts.rejected : 0 },
      {
        label: "Reviewer-assessed points",
        value: summary.validatedPoints != null ? summary.validatedPoints : 0
      },
      { label: "Criterion max", value: summary.maxPoints != null ? summary.maxPoints : 100 }
    ];
    host.innerHTML = cards
      .map(function (c) {
        return (
          '<div class="evidence-stat is-accent-teal">' +
          '<div class="evidence-stat-body"><span>' +
          FL.esc(c.label) +
          "</span><strong>" +
          FL.esc(String(c.value)) +
          "</strong></div></div>"
        );
      })
      .join("");
  },

  mountAccomplishmentListInWorkspace: function (session, state, isAdmin, host, criterion) {
    var facultyId = state.facultyId;
    var criterionKey = (state && state.criterionId) || "kra2-a";
    var person = FL.store.facultyById(facultyId);
    var mountSeq = (FL.kra2AReview._workspaceMountSeq += 1);

    function showError(message) {
      if (mountSeq !== FL.kra2AReview._workspaceMountSeq) return;
      host.innerHTML =
        '<div class="kra2-a-workspace">' +
        '<h2 class="evidence-section-title">' +
        FL.esc(criterion ? criterion.name : "KRA II") +
        "</h2>" +
        '<div class="ca-preview-error"><p>' +
        FL.esc(message || "We couldn't load the accomplishments.") +
        '</p><button type="button" class="btn btn-ghost btn-small" data-kra2-retry>Try again</button></div></div>';
      var retry = host.querySelector("[data-kra2-retry]");
      if (retry) {
        retry.addEventListener("click", function () {
          FL.kra2AReview.mountAccomplishmentListInWorkspace(session, state, isAdmin, host, criterion);
        });
      }
    }

    host.innerHTML = FL.ui.loading("Loading KRA II accomplishments…");

    var accPromise = FL.kra2Evidence.fetchFacultyAccomplishments(session, facultyId, criterionKey);
    accPromise
      .then(function (accPayload) {
        if (mountSeq !== FL.kra2AReview._workspaceMountSeq) return;
        var rows = (accPayload && accPayload.accomplishments) || [];
        host.innerHTML = FL.kra2AWorkspaceUi.accomplishmentListHtml({
          criterionTitle: criterion ? criterion.name : "KRA II accomplishments",
          personName: person ? person.name : facultyId,
          summary: {},
          rows: rows,
          reviewHref: function (row) {
            return FL.kra2AReview._reviewHref({
              id: row.documentId,
              facultyId: facultyId,
              criterionId: criterionKey
            });
          }
        });
        FL.kra2AReview._maybeShowApprovedToast();
        return FL.kra2Evidence.fetchFacultySummary(session, facultyId, criterionKey).catch(function () {
          return {};
        });
      })
      .then(function (summary) {
        if (mountSeq !== FL.kra2AReview._workspaceMountSeq || !summary) return;
        FL.kra2AReview._paintKra2Stats(summary);
        var summarySlot = host.querySelector("[data-kra2-summary-slot]");
        if (summarySlot) {
          var name = person ? person.name : facultyId;
          summarySlot.textContent =
            name + " · " + FL.kra2AWorkspaceUi.kra2SummaryLineHtml(summary);
        }
      })
      .catch(function (err) {
        showError((err && err.message) || "We couldn't load the accomplishments.");
      });
  },

  _maybeShowApprovedToast: function () {
    try {
      if (typeof sessionStorage === "undefined") return;
      if (!sessionStorage.getItem(FL.kra2AReview._APPROVED_TOAST_KEY)) return;
      sessionStorage.removeItem(FL.kra2AReview._APPROVED_TOAST_KEY);
      if (FL.ui && FL.ui.toast) FL.ui.toast("Accomplishment approved.", "ok");
    } catch (_e) {
      /* ignore */
    }
  },

  paintReviewPage: function (session, doc, canDecide, ctx) {
    FL.kra2AReview._ensurePageDelegation(session);
    var page = document.getElementById("page");
    page.innerHTML = FL.ui.loading("Loading submission…");
    var configReady = FL.store.refreshScoringConfiguration({ force: false }).catch(function () {
      return null;
    });
    var facultyId = doc.facultyId || (ctx && ctx.faculty && ctx.faculty.id) || "";
    var docsPromise =
      facultyId && FL.store && FL.store.loadFacultyDocuments
        ? FL.store.loadFacultyDocuments(session, facultyId).catch(function () {
            return [];
          })
        : Promise.resolve([]);
    Promise.all([configReady, FL.kra2Evidence.fetchBundle(session, doc.id), docsPromise]).then(function (results) {
      FL.kra2AReview._renderReview(session, doc, canDecide, ctx, results[1], results[2]);
    }).catch(function (err) {
      page.innerHTML = FL.ui.empty(
        "Could not load",
        (err && err.message) || "This submission could not be loaded. Try again from the faculty list."
      );
    });
  },

  _renderReview: function (session, doc, canDecide, ctx, payload, facultyDocs) {
    var state = FL.kra2AReview._createState(session, doc, canDecide, ctx, payload, facultyDocs);
    FL.kra2AReview._renderPage(session, state);
  },

  _docIndex: function (facultyDocs) {
    var map = {};
    (facultyDocs || []).forEach(function (d) {
      if (d && d.id) map[d.id] = d;
    });
    return map;
  },

  _createState: function (session, doc, canDecide, ctx, payload, facultyDocs) {
    var bundle = payload.bundle || {};
    var docById = FL.kra2AReview._docIndex(facultyDocs);
    var slotIds = FL.kra2AWorkspaceUi.requiredSlotIds(bundle, payload);
    var buildOpts = { docById: docById, payload: payload };
    return {
      session: session,
      doc: doc,
      canDecide: !!canDecide,
      ctx: ctx,
      payload: payload,
      docById: docById,
      bundle: bundle,
      validation: payload.validation || {},
      scoring: payload.scoring || {},
      slotIds: slotIds,
      evidenceItems: FL.kra2AWorkspaceUi.buildEvidenceSlotItems(bundle, doc, slotIds, buildOpts),
      remarks: bundle.reviewerRemarks || "",
      backHref: ctx.back || "documents.html",
      backLabel: ctx.backLabel || "Back",
      facultyName: (ctx.faculty && ctx.faculty.name) || "Faculty",
      verificationSave: { pending: false, requestId: 0 },
      chromeHtml: ""
    };
  },

  _mergePayload: function (state, payload) {
    if (!payload) return;
    state.payload = Object.assign({}, state.payload || {}, payload);
    if (payload.bundle) state.bundle = payload.bundle;
    if (payload.validation) state.validation = payload.validation;
    if (payload.scoring) state.scoring = payload.scoring;
    if (Array.isArray(payload.requiredEvidenceSlots) && payload.requiredEvidenceSlots.length) {
      state.slotIds = payload.requiredEvidenceSlots.slice();
    }
    state.evidenceItems = FL.kra2AWorkspaceUi.buildEvidenceSlotItems(state.bundle, state.doc, state.slotIds, {
      docById: state.docById || {},
      payload: state.payload
    });
    if (state.bundle.reviewerRemarks) state.remarks = state.bundle.reviewerRemarks;
  },

  _captureFormDraft: function (state) {
    var remarksEl = document.getElementById("kra2-remarks");
    if (remarksEl) state.remarks = remarksEl.value;
    var assessedEl = document.getElementById("kra2-assessed-points");
    if (assessedEl && assessedEl.type !== "hidden") state._draftAssessedPoints = assessedEl.value;
    var reasonEl = document.getElementById("kra2-score-adjustment-reason");
    if (reasonEl) state._draftAdjustmentReason = reasonEl.value;
  },

  _syncApproveButton: function (state) {
    var remarks = (document.getElementById("kra2-remarks") || {}).value || "";
    FL.kra2AWorkspaceUi.logApprovalDiagnostics(state, remarks);
    var host = document.getElementById("kra2-approval-checklist");
    if (host && FL.kra2AWorkspaceUi.approvalChecklistHtml) {
      var tmp = document.createElement("div");
      tmp.innerHTML = FL.kra2AWorkspaceUi.approvalChecklistHtml(state, remarks);
      var fresh = tmp.firstElementChild;
      if (fresh) host.replaceWith(fresh);
    }
    var blockers = FL.kra2AWorkspaceUi.computeApprovalBlockers(state, remarks);
    var btn = document.getElementById("kra2-approve");
    var enabled = blockers.length === 0 && !!state.canDecide;
    if (btn) btn.disabled = !enabled;
    var hint = document.getElementById("kra2-approve-hint");
    if (hint) {
      hint.textContent = enabled
        ? "Ready to approve."
        : blockers.length
          ? blockers.length + " requirement(s) still outstanding (see checklist above)."
          : "Approval unavailable.";
    }
  },

  _refreshScoringDisplays: function (state) {
    var scoring = state.scoring || {};
    var systemPts =
      scoring.systemCalculatedPoints != null
        ? scoring.systemCalculatedPoints
        : scoring.estimatedPoints;
    var finalPts =
      scoring.reviewerAssessedPoints != null ? scoring.reviewerAssessedPoints : systemPts;
    var sysEl = document.getElementById("kra2-system-points-display");
    var finEl = document.getElementById("kra2-final-points-display");
    if (sysEl) sysEl.textContent = systemPts != null ? String(systemPts) : "—";
    if (finEl) finEl.textContent = finalPts != null ? String(finalPts) : "—";
    var assessedInput = document.getElementById("kra2-assessed-points");
    if (assessedInput && assessedInput.type === "hidden" && systemPts != null) {
      assessedInput.value = String(systemPts);
    }
    if (finEl && assessedInput && assessedInput.type === "number" && assessedInput.value !== "") {
      finEl.textContent = assessedInput.value;
    }
  },

  _updateReviewValidationUi: function (session, state) {
    FL.kra2AReview._syncApproveButton(state);
    var needsMeta = FL.kra2AWorkspaceUi.metadataPanelNeeded(state);
    var metaSection = document.querySelector(".kra2-metadata-edit");
    if (needsMeta && !metaSection) {
      FL.kra2AReview._renderPage(session, state);
      return;
    }
    if (!needsMeta && metaSection) {
      FL.kra2AReview._renderPage(session, state);
      return;
    }
    var items = state.evidenceItems || [];
    items.forEach(function (item) {
      var sel = document.getElementById("kra2-slot-" + item.slotId);
      if (sel && item.status) sel.value = item.status;
    });
  },

  _patchAndRefresh: function (session, state, body) {
    return FL.kra2Evidence.patchBundle(session, state.doc.id, body).then(function (resp) {
      if (resp && (resp.bundle || resp.scoring || resp.validation)) {
        FL.kra2AReview._mergePayload(state, resp);
      }
      return FL.kra2Evidence.fetchBundle(session, state.doc.id);
    }).then(function (fresh) {
      FL.kra2AReview._captureFormDraft(state);
      FL.kra2AReview._mergePayload(state, fresh);
      FL.kra2AReview._refreshScoringDisplays(state);
      FL.kra2AReview._updateReviewValidationUi(session, state);
      return fresh;
    });
  },

  _ensurePageDelegation: function (session) {
    FL.kra2AReview._reviewSession = session;
    if (FL.kra2AReview._pageDelegationBound) return;
    var page = document.getElementById("page");
    if (!page) return;
    FL.kra2AReview._pageDelegationBound = true;
    page.addEventListener("click", function (ev) {
      var btn = ev.target && ev.target.closest ? ev.target.closest("[data-kra2-action]") : null;
      if (!btn) return;
      var action = btn.getAttribute("data-kra2-action");
      var state = FL.kra2AReview._activeReviewState;
      var activeSession = FL.kra2AReview._reviewSession;
      if (!state || !activeSession) return;
      if (action === "fill-ocr") {
        ev.preventDefault();
        FL.kra2AReview._handleFillOcr(activeSession, state, btn);
      } else if (action === "save-metadata") {
        ev.preventDefault();
        FL.kra2AReview._handleSaveMetadata(activeSession, state, btn);
      }
    });
  },

  _setMetadataIndicator: function (elementId, phase, message) {
    var el = document.getElementById(elementId);
    if (!el) return;
    var text =
      message ||
      (phase === "saving"
        ? "Saving…"
        : phase === "saved"
          ? "Saved"
          : phase === "error"
            ? "Could not save — try again."
            : "");
    el.textContent = text;
    el.className =
      "cc-save-indicator" +
      (phase === "saving" ? " cc-save-indicator--saving" : "") +
      (phase === "saved" ? " cc-save-indicator--saved" : "") +
      (phase === "error" ? " cc-save-indicator--error" : "");
  },

  _handleFillOcr: function (session, state, btn) {
    if (btn) btn.disabled = true;
    FL.kra2AReview._setMetadataIndicator("kra2-fill-ocr-indicator", "saving", "Applying…");
    try {
      var result = FL.kra2AWorkspaceUi.applyOcrSuggestions(state, { onlyEmpty: true });
      if (result.filled && result.filled.length) {
        var summary = "Filled from OCR: " + result.filled.join(", ");
        FL.kra2AReview._setMetadataIndicator("kra2-fill-ocr-indicator", "saved", summary);
        if (FL.ui && FL.ui.toast) FL.ui.toast(summary, "ok");
      } else {
        var msg = result.message || "We couldn't find enough information in this document.";
        FL.kra2AReview._setMetadataIndicator("kra2-fill-ocr-indicator", "error", msg);
        if (FL.ui && FL.ui.toast) FL.ui.toast(msg, "warn");
      }
    } catch (err) {
      var fail = (err && err.message) || "Could not apply OCR suggestions.";
      FL.kra2AReview._setMetadataIndicator("kra2-fill-ocr-indicator", "error", fail);
      if (FL.ui && FL.ui.toast) FL.ui.toast(fail, "danger");
    } finally {
      if (btn) btn.disabled = false;
    }
  },

  _handleSaveMetadata: function (session, state, btn) {
    var check = FL.kra2AWorkspaceUi.validateReviewerMetadata(state);
    if (!check.ok) {
      FL.kra2AReview._setMetadataIndicator("kra2-save-metadata-indicator", "error", check.message);
      if (FL.ui && FL.ui.toast) FL.ui.toast(check.message, "danger");
      return;
    }
    var body = check.body;
    body.confirmReviewerMetadata = true;
    if (btn) btn.disabled = true;
    FL.kra2AReview._setMetadataIndicator("kra2-save-metadata-indicator", "saving");
    return FL.kra2AReview._patchAndRefresh(session, state, body)
      .then(function () {
        FL.kra2AReview._setMetadataIndicator("kra2-save-metadata-indicator", "saved");
        if (FL.ui && FL.ui.toast) FL.ui.toast("Confirmed metadata saved.", "ok");
        FL.kra2AReview._renderPage(session, state);
      })
      .catch(function (err) {
        if (btn) btn.disabled = false;
        var msg = (err && err.message) || "Could not save metadata.";
        FL.kra2AReview._setMetadataIndicator("kra2-save-metadata-indicator", "error", msg);
        if (FL.ui && FL.ui.toast) FL.ui.toast(msg, "danger");
        throw err;
      });
  },

  _renderPage: function (session, state) {
    FL.kra2AReview._reviewSession = session;
    FL.kra2AReview._activeReviewState = state;
    FL.kra2AReview._ensurePageDelegation(session);
    FL.kra2AReview._captureFormDraft(state);
    var page = document.getElementById("page");
    page.innerHTML = FL.kra2AWorkspaceUi.compactReviewPageHtml(state);
    if (state._draftAssessedPoints != null) {
      var assessedEl = document.getElementById("kra2-assessed-points");
      if (assessedEl) assessedEl.value = state._draftAssessedPoints;
    }
    if (state._draftAdjustmentReason != null) {
      var reasonEl = document.getElementById("kra2-score-adjustment-reason");
      if (reasonEl) reasonEl.value = state._draftAdjustmentReason;
    }
    FL.kra2AReview._bindPage(session, state);
  },

  _setSaveIndicator: function (slotId, phase) {
    var el = document.getElementById("kra2-save-" + slotId);
    if (!el) return;
    el.textContent = FL.kra2AWorkspaceUi.slotSaveIndicatorMessage(phase);
    el.className = "cc-save-indicator" + (phase === "error" ? " cc-save-indicator--error" : "");
  },

  _autoSaveSlot: function (session, state, slotId, status, selectEl) {
    if (state.verificationSave.pending) return Promise.resolve();
    state.verificationSave.pending = true;
    var reqId = (state.verificationSave.requestId += 1);
    FL.kra2AReview._setSaveIndicator(slotId, "saving");
    if (selectEl) selectEl.disabled = true;
    return FL.kra2Evidence
      .patchBundle(session, state.doc.id, { evidenceSlot: slotId, status: status })
      .then(function () {
        return FL.kra2Evidence.fetchBundle(session, state.doc.id);
      })
      .then(function (fresh) {
        if (reqId !== state.verificationSave.requestId) return fresh;
        FL.kra2AReview._captureFormDraft(state);
        FL.kra2AReview._mergePayload(state, fresh);
        FL.kra2AReview._setSaveIndicator(slotId, "saved");
        if (selectEl) selectEl.disabled = false;
        FL.kra2AReview._updateReviewValidationUi(session, state);
        return fresh;
      })
      .catch(function (err) {
        if (reqId !== state.verificationSave.requestId) throw err;
        FL.kra2AReview._setSaveIndicator(slotId, "error");
        if (selectEl) selectEl.disabled = false;
        if (FL.ui && FL.ui.toast) {
          FL.ui.toast("Could not save verification. Try changing the status again.", "danger");
        }
        throw err;
      })
      .finally(function () {
        if (reqId === state.verificationSave.requestId) state.verificationSave.pending = false;
      });
  },

  _approvalPayload: function (state) {
    var scoring = state.scoring || {};
    var systemPts =
      scoring.systemCalculatedPoints != null
        ? scoring.systemCalculatedPoints
        : scoring.estimatedPoints;
    var indicatorMax =
      scoring.indicatorMaxPoints != null ? scoring.indicatorMaxPoints : scoring.eligiblePoints;
    var assessedEl = document.getElementById("kra2-assessed-points");
    var remarks = (document.getElementById("kra2-remarks") || {}).value || "";
    var reasonEl = document.getElementById("kra2-score-adjustment-reason");
    var body = { reviewStatus: "approved", remarks: remarks };
    if (assessedEl && assessedEl.value !== "") {
      body.assessedPoints = parseFloat(assessedEl.value, 10);
      if (isNaN(body.assessedPoints)) {
        throw new Error("Enter a valid reviewer-assessed points value.");
      }
    }
    if (reasonEl && reasonEl.value.trim()) {
      body.scoreAdjustmentReason = reasonEl.value.trim();
    }
    if (body.assessedPoints != null && indicatorMax != null && body.assessedPoints > indicatorMax + 0.001) {
      throw new Error(
        "Assessed points cannot exceed the published indicator maximum (" + indicatorMax + ")."
      );
    }
    if (body.assessedPoints != null && systemPts != null && body.assessedPoints > systemPts + 0.001) {
      throw new Error(
        "Assessed points cannot exceed the system-calculated eligible amount (" + systemPts + ")."
      );
    }
    if (
      scoring.allowsPointAdjustment === true &&
      body.assessedPoints != null &&
      systemPts != null &&
      Math.abs(body.assessedPoints - parseFloat(systemPts, 10)) > 0.001 &&
      (!body.scoreAdjustmentReason || body.scoreAdjustmentReason.length < 10)
    ) {
      throw new Error(
        "Explain why the assessed score differs from the system-calculated eligible points (at least 10 characters)."
      );
    }
    if (
      !scoring.allowsPointAdjustment &&
      body.assessedPoints != null &&
      systemPts != null &&
      Math.abs(body.assessedPoints - parseFloat(systemPts, 10)) > 0.001
    ) {
      throw new Error("This indicator does not permit manual score adjustment.");
    }
    return body;
  },

  _revokeKra2PreviewObjectUrl: function (state) {
    if (!state || !state._kra2PreviewObjectUrl) return;
    try {
      URL.revokeObjectURL(state._kra2PreviewObjectUrl);
    } catch (_e) {
      /* ignore */
    }
    state._kra2PreviewObjectUrl = null;
    state._kra2PreviewObjectDocId = null;
  },

  _mountKra2DocumentPreview: function (session, state, docId, labelText) {
    var previewHost = document.querySelector(".kra2-doc-preview-frame[data-doc-preview-id]");
    if (!previewHost || !FL.documents || !FL.documents.mountAuthenticatedPreview) {
      return Promise.resolve();
    }
    var resolvedId = (docId || state.doc.id || "").trim();
    if (!resolvedId) return Promise.resolve();

    function resolveDocRow() {
      if (resolvedId === state.doc.id) return Promise.resolve(state.doc);
      if (state.docById && state.docById[resolvedId]) {
        return Promise.resolve(state.docById[resolvedId]);
      }
      if (FL.store && FL.store.documentById) {
        var cached = FL.store.documentById(resolvedId);
        if (cached) {
          if (!state.docById) state.docById = {};
          state.docById[resolvedId] = cached;
          return Promise.resolve(cached);
        }
      }
      if (FL.store && FL.store.refreshLiveDocument) {
        return FL.store.refreshLiveDocument(session, resolvedId).then(function (fresh) {
          if (fresh) {
            if (!state.docById) state.docById = {};
            state.docById[resolvedId] = fresh;
          }
          return fresh;
        });
      }
      return Promise.resolve(null);
    }

    if (state._kra2PreviewObjectDocId && state._kra2PreviewObjectDocId !== resolvedId) {
      FL.kra2AReview._revokeKra2PreviewObjectUrl(state);
    }

    previewHost.setAttribute("data-doc-preview-id", resolvedId);
    var labelEl = document.getElementById("kra2-preview-doc-label");
    if (labelEl) {
      labelEl.textContent = "Showing: " + (labelText || resolvedId);
    }

    return resolveDocRow().then(function (row) {
      if (!row) {
        previewHost.innerHTML =
          '<div class="ca-preview-error"><p>Couldn\'t open this document. Please try again.</p>' +
          '<button type="button" class="btn btn-ghost btn-small" data-kra2-preview-retry>Retry</button></div>';
        var retryMissing = previewHost.querySelector("[data-kra2-preview-retry]");
        if (retryMissing) {
          retryMissing.addEventListener("click", function () {
            FL.kra2AReview._mountKra2DocumentPreview(session, state, resolvedId, labelText);
          });
        }
        return;
      }
      return FL.documents.mountAuthenticatedPreview(row, previewHost, {
        session: session,
        previewDocId: resolvedId
      }).then(function () {
        if (row._objectUrl) {
          if (state._kra2PreviewObjectUrl && state._kra2PreviewObjectDocId !== resolvedId) {
            FL.kra2AReview._revokeKra2PreviewObjectUrl(state);
          }
          state._kra2PreviewObjectUrl = row._objectUrl;
          state._kra2PreviewObjectDocId = resolvedId;
        }
      });
    });
  },

  _bindPage: function (session, state) {
    FL.kra2AReview._mountKra2DocumentPreview(session, state, state.doc.id, state.doc.fileName || state.doc.title);
    document.querySelectorAll("[data-kra2-preview-doc]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var docId = btn.getAttribute("data-kra2-preview-doc");
        var label = btn.getAttribute("data-kra2-preview-label") || "";
        var host = document.querySelector(".kra2-doc-preview-frame[data-doc-preview-id]");
        if (host) host.scrollIntoView({ behavior: "smooth", block: "start" });
        FL.kra2AReview._mountKra2DocumentPreview(session, state, docId, label);
      });
    });
    document.querySelectorAll(".kra2-slot-status").forEach(function (sel) {
      sel.addEventListener("change", function () {
        var slotId = sel.getAttribute("data-slot");
        FL.kra2AReview._autoSaveSlot(session, state, slotId, sel.value, sel);
      });
    });

    var recalcBtn = document.getElementById("kra2-recalc-contribution");
    if (recalcBtn) {
      recalcBtn.addEventListener("click", function () {
        var indicator = document.getElementById("kra2-save-contribution-indicator");
        if (indicator) indicator.textContent = "Recalculating…";
        var pct = parseFloat((document.getElementById("kra2-contribution-percent") || {}).value, 10);
        FL.kra2AReview._patchAndRefresh(session, state, { declaredContributionPercent: pct })
          .then(function () {
            if (indicator) indicator.textContent = "Updated";
            FL.kra2AReview._renderPage(session, state);
          })
          .catch(function () {
            if (indicator) indicator.textContent = "Failed";
            if (FL.ui && FL.ui.toast) {
              FL.ui.toast("Could not update contribution percentage.", "danger");
            }
          });
      });
    }

    var remarksEl = document.getElementById("kra2-remarks");
    if (remarksEl) {
      remarksEl.addEventListener("input", function () {
        FL.kra2AReview._syncApproveButton(state);
      });
    }
    var assessedEl = document.getElementById("kra2-assessed-points");
    if (assessedEl) {
      assessedEl.addEventListener("input", function () {
        FL.kra2AReview._syncApproveButton(state);
        var finEl = document.getElementById("kra2-final-points-display");
        if (finEl && assessedEl.value !== "") finEl.textContent = assessedEl.value;
      });
    }
    var reasonEl = document.getElementById("kra2-score-adjustment-reason");
    if (reasonEl) {
      reasonEl.addEventListener("input", function () {
        FL.kra2AReview._syncApproveButton(state);
      });
    }
    FL.kra2AReview._syncApproveButton(state);

    var approveBtn = document.getElementById("kra2-approve");
    var rejectBtn = document.getElementById("kra2-reject");
    if (approveBtn) {
      approveBtn.addEventListener("click", function () {
        var body;
        try {
          body = FL.kra2AReview._approvalPayload(state);
        } catch (validationErr) {
          if (FL.ui && FL.ui.toast) {
            FL.ui.toast(validationErr.message || "Check scoring fields and try again.", "danger");
          }
          return;
        }
        approveBtn.disabled = true;
        FL.kra2Evidence
          .patchBundle(session, state.doc.id, body)
          .then(function () {
            try {
              sessionStorage.setItem(FL.kra2AReview._APPROVED_TOAST_KEY, "1");
            } catch (_e) {
              /* ignore */
            }
            window.location.href = state.backHref;
          })
          .catch(function (err) {
            approveBtn.disabled = false;
            var msg =
              (err && err.message) ||
              "Approval could not be completed. Verify all documents and add remarks (at least 10 characters).";
            if (FL.ui && FL.ui.toast) FL.ui.toast(msg, "danger");
          });
      });
    }
    if (rejectBtn) {
      rejectBtn.addEventListener("click", function () {
        rejectBtn.disabled = true;
        var remarks = (document.getElementById("kra2-remarks") || {}).value || "";
        FL.kra2Evidence
          .patchBundle(session, state.doc.id, { reviewStatus: "rejected", remarks: remarks })
          .then(function () {
            window.location.href = state.backHref;
          })
          .catch(function (err) {
            rejectBtn.disabled = false;
            if (FL.ui && FL.ui.toast) {
              FL.ui.toast(
                (err && err.message) || "Rejection requires remarks (at least 10 characters).",
                "danger"
              );
            }
          });
      });
    }
  }
};
