/**
 * Criterion C — reviewer accomplishment list and guided document review (Criterion B pattern).
 */
window.FL = window.FL || {};

FL.criterionCReview = {
  _APPROVED_LIST_TOAST_KEY: "fl_cc_accomplishment_approved_toast",

  _reviewHref: function (doc) {
    if (FL.reviewerNav && FL.reviewerNav.accomplishmentReviewUrl) {
      return FL.reviewerNav.accomplishmentReviewUrl(
        Object.assign({}, doc, { criterionId: "kra1-c", kraId: doc.kraId || "kra1" })
      );
    }
    return "documents.html";
  },

  mountWorkspaceAccomplishmentReview: function (session, state, isAdmin, host, docId) {
    var back = FL.reviewerNav.criterionWorkspaceUrl({
      facultyId: state.facultyId,
      kraId: state.kraId || "kra1",
      criterionId: "kra1-c",
      docFilter: state.docFilter || "all"
    });
    var liveHost = function () {
      return document.getElementById("evidence-body") || host;
    };
    liveHost().innerHTML = FL.ui.loading("Loading accomplishment", "Fetching Criterion C evidence…");
    var cached = FL.store.documentById(docId);
    var docPromise = cached ? Promise.resolve(cached) : FL.store.refreshLiveDocument(session, docId);
    docPromise.then(function (doc) {
      if (!doc) throw new Error("Document was not found.");
      return FL.criterionCReview.paintReviewPage(session, doc, !isAdmin && session.role === "reviewer", {
        faculty: FL.store.facultyById(state.facultyId),
        back: back,
        backLabel: "Back to accomplishments",
        mountHost: liveHost(),
        scrollDocId: state.scrollDoc || ""
      });
    }).catch(function (err) {
      liveHost().innerHTML = FL.ui.emptyWithRetry(
        "Could not load accomplishment",
        (err && err.message) || "Try again.",
        "cc-ws-review-retry"
      );
      var btn = document.getElementById("cc-ws-review-retry");
      if (btn) {
        btn.addEventListener("click", function () {
          FL.criterionCReview.mountWorkspaceAccomplishmentReview(session, state, isAdmin, liveHost(), docId);
        });
      }
    });
  },

  mountAccomplishmentListInWorkspace: function (session, state, isAdmin, host, criterion) {
    if (state.focusDoc) {
      return FL.criterionCReview.mountWorkspaceAccomplishmentReview(session, state, isAdmin, host, state.focusDoc);
    }
    var facultyId = state.facultyId;
    var person = FL.store.facultyById(facultyId);
    var docs = FL.evidence._facultyDocs(session, facultyId);
    var critLabel = criterion
      ? FL.rules.criterionUserLabel(criterion.id, criterion.name)
      : "Criterion C";
    var kra = FL.rules.findKra(state.kraId || "kra1");
    host.innerHTML = FL.ui.loading("Loading Criterion C accomplishments…");
    var configPromise = FL.store.refreshScoringConfiguration({ force: false }).catch(function () {
      return null;
    });
    var summaryPromise = FL.criterionCEvidence.fetchFacultySummary(session, facultyId).catch(function (err) {
      return { _error: err && err.message ? err.message : "Summary unavailable" };
    });
    var listPromise = FL.criterionCEvidence.fetchFacultyAccomplishments(session, facultyId).catch(function () {
      return { accomplishments: [] };
    });
    var docsPromise = FL.store.usesLiveDocuments()
      ? FL.store.loadFacultyDocuments(session, facultyId).catch(function () {
        return null;
      })
      : Promise.resolve(null);
    Promise.all([configPromise, summaryPromise, listPromise, docsPromise]).then(function (results) {
      var summary = results[1] || {};
      if (summary._error) {
        host.innerHTML = FL.ui.empty("Could not load Criterion C", FL.esc(summary._error));
        return;
      }
      var apiRows = (results[2] && results[2].accomplishments) || [];
      var freshDocs = FL.evidence._facultyDocs(session, facultyId);
      var items = FL.criterionCWorkspaceUi.mergeAccomplishmentListItems(apiRows, freshDocs.length ? freshDocs : docs);
      if (!items.length && docs.length) {
        items = FL.criterionCWorkspaceUi.buildWorkspaceModel(docs.filter(function (d) {
          return d.criterionId === "kra1-c";
        }));
      }
      host.innerHTML = FL.criterionCWorkspaceUi.criterionCReviewWorkspaceHtml({
        criterionTitle: "Criterion C — Research Advising and Mentorship Services",
        criterionLabel: critLabel,
        personName: person ? person.name : "Faculty",
        summary: summary,
        scoringConfigLabel: "",
        items: items,
        isAdmin: isAdmin,
        reviewHref: function (doc) {
          return FL.criterionCReview._reviewHref(doc);
        }
      });
      FL.criterionCReview._maybeShowApprovedListToast();
      if (FL.evidence && FL.evidence.highlightAccomplishmentCard) {
        FL.evidence.highlightAccomplishmentCard(state.highlightDoc);
      }
    });
  },

  _maybeShowApprovedListToast: function () {
    try {
      if (typeof sessionStorage === "undefined") return;
      if (!sessionStorage.getItem(FL.criterionCReview._APPROVED_LIST_TOAST_KEY)) return;
      sessionStorage.removeItem(FL.criterionCReview._APPROVED_LIST_TOAST_KEY);
      if (FL.ui && FL.ui.toast) FL.ui.toast("Accomplishment approved.", "ok");
    } catch (_e) {
      /* ignore storage errors */
    }
  },

  _navigateToCriterionCListAfterApproval: function (session, state) {
    try {
      if (typeof sessionStorage !== "undefined") {
        sessionStorage.setItem(FL.criterionCReview._APPROVED_LIST_TOAST_KEY, "1");
      }
    } catch (_e) {
      /* ignore */
    }
    var href = (state && state.backHref) || (state.ctx && state.ctx.back) || "documents.html";
    var facultyId = state.doc && state.doc.facultyId;
    var refresh =
      facultyId && FL.evidence && FL.evidence.refreshCountsAfterReview
        ? FL.evidence.refreshCountsAfterReview(session, facultyId)
        : Promise.resolve();
    refresh.finally(function () {
      window.location.href = href;
    });
  },

  paintReviewPage: function (session, doc, canDecide, ctx) {
    ctx = ctx || {};
    var page = ctx.mountHost || document.getElementById("page");
    if (!page) return Promise.reject(new Error("Review view is not available."));
    if (FL.criterionCWorkspaceUi.isFacultyDraftItem({ primary: doc })) {
      canDecide = false;
    }
    if (session.role === "administrator" && doc.criterionCEvidence) {
      FL.criterionCReview._renderReview(session, doc, false, ctx, doc.criterionCEvidence);
      return Promise.resolve();
    }
    page.innerHTML = FL.ui.loading("Loading Criterion C accomplishment…");
    var configReady = FL.store.refreshScoringConfiguration({ force: false }).catch(function () {
      return null;
    });
    var bundlePromise = FL.criterionCEvidence.fetchBundle(session, doc.id);
    var timed =
      FL.criterionCEvidence && typeof FL.criterionCEvidence._withTimeout === "function"
        ? FL.criterionCEvidence._withTimeout(bundlePromise, 25000, "Accomplishment request")
        : bundlePromise;
    Promise.all([configReady, timed]).then(function (results) {
      var payload = results[1];
      FL.criterionCReview._renderReview(session, doc, canDecide, ctx, payload);
    }).catch(function (err) {
      page.innerHTML = FL.ui.emptyWithRetry(
        "Could not load accomplishment",
        FL.esc(err.message || "Try again."),
        "cc-review-retry"
      );
      var retryBtn = document.getElementById("cc-review-retry");
      if (retryBtn) {
        retryBtn.addEventListener("click", function () {
          FL.criterionCReview.paintReviewPage(session, doc, canDecide, ctx);
        });
      }
    });
    return Promise.resolve();
  },

  _renderReview: function (session, doc, canDecide, ctx, payload) {
    var bundle = payload.bundle || {};
    var locked = bundle.scoringConfiguration;
    var lockedId = locked && locked.configurationId;
    var self = this;
    var paint = function (refKraSettings) {
      var state = self._createGuidedState(session, doc, canDecide, ctx, payload, refKraSettings);
      self._renderGuidedStep(session, state);
    };
    if (lockedId && FL.scoringConfiguration && FL.scoringConfiguration.fetchByConfigurationId) {
      FL.scoringConfiguration.fetchByConfigurationId(lockedId).then(function (hist) {
        paint(hist && hist.kraSettings);
      }).catch(function () {
        paint(null);
      });
      return;
    }
    paint(null);
  },

  _createGuidedState: function (session, doc, canDecide, ctx, payload, refKraSettings) {
    var ui = FL.criterionCWorkspaceUi;
    var bundle = payload.bundle || {};
    var slotIds = ui.requiredSlotIds(bundle);
    var state = {
      session: session,
      doc: doc,
      canDecide: !!canDecide,
      ctx: ctx,
      payload: payload,
      refKraSettings: refKraSettings,
      bundle: bundle,
      validation: payload.validation || {},
      scoring: payload.scoring || {},
      step: "details",
      evidenceIndex: 0,
      slotIds: slotIds,
      evidenceItems: ui.buildEvidenceSlotItems(bundle, doc, slotIds),
      remarks: bundle.reviewerRemarks || "",
      assessedPoints:
        bundle.reviewerAssessment && bundle.reviewerAssessment.assessedPoints != null
          ? String(bundle.reviewerAssessment.assessedPoints)
          : "",
      backHref: ctx.back || "documents.html",
      backLabel: ctx.backLabel || "Back to Criterion C",
      mountHost: ctx.mountHost || null,
      facultyName: (ctx.faculty && ctx.faculty.name) || "Faculty",
      verificationSave: { pending: false, requestId: 0, confirmedBySlot: {} },
      showGroupEditor: false
    };
    FL.criterionCWorkspaceUi.syncConfirmedSlotStatuses(state);
    return state;
  },

  _mergePayloadIntoGuidedState: function (state, payload) {
    if (!payload) return;
    state.payload = payload;
    state.bundle = payload.bundle || state.bundle;
    state.validation = payload.validation || state.validation;
    state.scoring = payload.scoring || state.scoring;
    state.evidenceItems = FL.criterionCWorkspaceUi.buildEvidenceSlotItems(
      state.bundle,
      state.doc,
      state.slotIds
    );
    if (state.bundle.reviewerRemarks) state.remarks = state.bundle.reviewerRemarks;
    var assessed = state.bundle.reviewerAssessment && state.bundle.reviewerAssessment.assessedPoints;
    if (assessed != null) state.assessedPoints = String(assessed);
    FL.criterionCWorkspaceUi.syncConfirmedSlotStatuses(state);
  },

  _confirmedSlotStatus: function (state, slotId) {
    var vs = state.verificationSave && state.verificationSave.confirmedBySlot;
    if (vs && vs[slotId]) return vs[slotId];
    var entry = state.bundle && state.bundle.checklist && state.bundle.checklist[slotId];
    return (entry && entry.status) || "missing";
  },

  _setSlotSaveIndicator: function (el, phase, savedStatus) {
    if (!el) return;
    var ui = FL.criterionCWorkspaceUi;
    el.textContent = ui.slotSaveIndicatorMessage(phase, savedStatus);
    el.className =
      "cc-save-indicator" +
      (phase === "saving" ? " cc-save-indicator--saving" : "") +
      (phase === "saved" ? " cc-save-indicator--saved" : "") +
      (phase === "error" ? " cc-save-indicator--error" : "");
  },

  _autoSaveSlotVerification: function (session, state, slotId, newStatus, selectEl, indicatorEl) {
    if (
      FL.reviewerAccomplishmentState &&
      !FL.reviewerAccomplishmentState.canVerifyEvidence(state)
    ) {
      if (selectEl) {
        selectEl.value = FL.criterionCReview._confirmedSlotStatus(state, slotId);
      }
      return Promise.resolve();
    }
    var ui = FL.criterionCWorkspaceUi;
    var confirmed = FL.criterionCReview._confirmedSlotStatus(state, slotId);
    if (!ui.slotStatusShouldPersist(newStatus, confirmed)) return Promise.resolve();
    state.verificationSave = state.verificationSave || { pending: false, requestId: 0, confirmedBySlot: {} };
    if (state.verificationSave.pending) {
      state.verificationSave.queued = { slotId: slotId, status: newStatus };
      return state.verificationSave.pendingPromise || Promise.resolve();
    }
    state.verificationSave.pending = true;
    var reqId = (state.verificationSave.requestId += 1);
    FL.criterionCReview._setSlotSaveIndicator(indicatorEl, "saving");
    if (selectEl) selectEl.disabled = true;
    var pendingPromise = FL.criterionCEvidence.patchBundle(session, state.doc.id, {
      evidenceSlot: slotId,
      status: newStatus
    })
      .then(function () {
        return FL.criterionCEvidence.fetchBundle(session, state.doc.id);
      })
      .then(function (fresh) {
        if (reqId !== state.verificationSave.requestId) return fresh;
        FL.criterionCReview._mergePayloadIntoGuidedState(state, fresh);
        var saved = FL.criterionCReview._confirmedSlotStatus(state, slotId);
        FL.criterionCReview._setSlotSaveIndicator(indicatorEl, "saved", saved);
        if (selectEl) {
          selectEl.value = saved;
          selectEl.disabled = false;
        }
        return fresh;
      })
      .catch(function (err) {
        if (reqId !== state.verificationSave.requestId) throw err;
        if (selectEl) {
          selectEl.value = confirmed;
          selectEl.disabled = false;
        }
        FL.criterionCReview._setSlotSaveIndicator(indicatorEl, "error");
        if (FL.ui && FL.ui.toast) FL.ui.toast(err.message || "Verification save failed", "danger");
        throw err;
      })
      .finally(function () {
        if (reqId !== state.verificationSave.requestId) return;
        state.verificationSave.pending = false;
        state.verificationSave.pendingPromise = null;
        var queued = state.verificationSave.queued;
        state.verificationSave.queued = null;
        if (queued && queued.slotId === slotId) {
          var sel = document.getElementById("cc-slot-status");
          var ind = document.getElementById("cc-slot-save-indicator");
          if (sel && sel.value !== FL.criterionCReview._confirmedSlotStatus(state, queued.slotId)) {
            FL.criterionCReview._autoSaveSlotVerification(
              session,
              state,
              queued.slotId,
              sel.value,
              sel,
              ind
            );
          }
        }
      });
    state.verificationSave.pendingPromise = pendingPromise;
    return pendingPromise;
  },

  _navigateWhenVerificationIdle: function (state, action) {
    if (state.verificationSave && state.verificationSave.pending) {
      if (FL.ui && FL.ui.toast) {
        FL.ui.toast("Wait for verification to finish saving.", "warn");
      }
      return;
    }
    action();
  },

  _refreshValidationAndRender: function (session, state) {
    return FL.criterionCEvidence.fetchBundle(session, state.doc.id)
      .then(function (fresh) {
        FL.criterionCReview._mergePayloadIntoGuidedState(state, fresh);
        FL.criterionCReview._renderGuidedStep(session, state);
      })
      .catch(function (err) {
        if (FL.ui && FL.ui.toast) FL.ui.toast(err.message || "Could not refresh validation", "danger");
        else alert(err.message || "Could not refresh validation");
      });
  },

  _renderGuidedStep: function (session, state) {
    var page = state.mountHost || document.getElementById("page");
    if (!page) return;
    if (state.ocrPollTimer) {
      clearInterval(state.ocrPollTimer);
      state.ocrPollTimer = null;
    }
    state.chromeHtml = FL.criterionCReview._reviewChromeCompact(state);
    page.innerHTML = FL.criterionCWorkspaceUi.compactReviewPageHtml(state);
    FL.criterionCReview._bindCompactReviewPage(session, state);
  },

  _reviewChromeCompact: function (state) {
    var ui = FL.criterionCWorkspaceUi;
    var esc = FL.esc;
    var configBanner = FL.scoringConfiguration ? FL.scoringConfiguration.bannerHtml({ compact: true }) : "";
    var locked = state.bundle && state.bundle.scoringConfiguration;
    var lockedLabel = FL.scoringConfiguration ? FL.scoringConfiguration.lockedSnapshotLabel(locked) : "";
    var draftBanner = ui.isFacultyDraftItem({ primary: state.doc })
      ? '<div class="alert alert-info">Faculty draft — approval actions stay disabled until submission.</div>'
      : "";
    return (
      configBanner +
      (lockedLabel ? '<p class="note scoring-config-locked">' + esc(lockedLabel) + "</p>" : "") +
      draftBanner
    );
  },

  _reviewChrome: function (state, activeStep) {
    return FL.criterionCReview._reviewChromeCompact(state);
  },

  _compactReviewHtml: function (state) {
    state.chromeHtml = FL.criterionCReview._reviewChromeCompact(state);
    return FL.criterionCWorkspaceUi.compactReviewPageHtml(state);
  },

  _bindOcrRetry: function (session, state) {
    var retry = document.getElementById("cc-ocr-retry");
    if (!retry || !state.canDecide) return;
    retry.addEventListener("click", function () {
      retry.disabled = true;
      FL.store.retryDocumentOcr(session, state.doc.id)
        .then(function () {
          return FL.store.refreshLiveDocument(session, state.doc.id);
        })
        .then(function (doc) {
          if (doc) state.doc = doc;
          return FL.criterionCEvidence.fetchBundle(session, state.doc.id);
        })
        .then(function (fresh) {
          FL.criterionCReview._mergePayloadIntoGuidedState(state, fresh);
          FL.criterionCReview._renderGuidedStep(session, state);
        })
        .catch(function (err) {
          retry.disabled = false;
          if (FL.ui && FL.ui.toast) FL.ui.toast(err.message || "OCR retry failed", "danger");
        });
    });
  },

  _bindResearchMetadataSave: function (session, state) {
    if (!state.canDecide) return;
    var saveBtn = document.getElementById("cc-save-research-metadata");
    if (!saveBtn) return;
    var indicator = document.getElementById("cc-metadata-save-indicator");
    saveBtn.addEventListener("click", function () {
      var namesEl = document.getElementById("cc-reviewer-student-names");
      var ayEl = document.getElementById("cc-reviewer-academic-year");
      var dateEl = document.getElementById("cc-reviewer-completion-date");
      var groupEl = document.getElementById("cc-reviewer-group-label");
      var studentNames = namesEl ? (namesEl.value || "").trim() : "";
      if (!studentNames) {
        if (FL.ui && FL.ui.toast) FL.ui.toast("Student name(s) are required.", "danger");
        else alert("Student name(s) are required.");
        return;
      }
      var body = { studentNames: studentNames };
      if (ayEl) body.academicYear = (ayEl.value || "").trim();
      if (dateEl && dateEl.value) body.completionDate = dateEl.value;
      if (groupEl) body.studentGroupLabel = (groupEl.value || "").trim();
      saveBtn.disabled = true;
      FL.criterionCReview._setSlotSaveIndicator(indicator, "saving");
      FL.criterionCEvidence.patchBundle(session, state.doc.id, body)
        .then(function () {
          return FL.criterionCEvidence.fetchBundle(session, state.doc.id);
        })
        .then(function (fresh) {
          FL.criterionCReview._mergePayloadIntoGuidedState(state, fresh);
          FL.criterionCReview._setSlotSaveIndicator(indicator, "saved", "saved");
          if (FL.ui && FL.ui.toast) FL.ui.toast("Research details saved.", "ok");
          FL.criterionCReview._renderGuidedStep(session, state);
        })
        .catch(function (err) {
          saveBtn.disabled = false;
          FL.criterionCReview._setSlotSaveIndicator(indicator, "error");
          if (FL.ui && FL.ui.toast) FL.ui.toast(err.message || "Save failed", "danger");
          else alert(err.message || "Save failed");
        });
    });
  },

  _bindOcrCompletionPoll: function (session, state) {
    if (state.ocrPollTimer) {
      clearInterval(state.ocrPollTimer);
      state.ocrPollTimer = null;
    }
    var status = (
      (state.payload && state.payload.ocrStatus) ||
      (state.doc && state.doc.ocr && state.doc.ocr.status) ||
      ""
    )
      .toString()
      .toLowerCase();
    if (status !== "pending" && status !== "processing") return;
    state.ocrPollTimer = setInterval(function () {
      FL.criterionCEvidence.fetchBundle(session, state.doc.id)
        .then(function (fresh) {
          var next = ((fresh && fresh.ocrStatus) || "").toLowerCase();
          FL.criterionCReview._mergePayloadIntoGuidedState(state, fresh);
          if (next !== "pending" && next !== "processing") {
            clearInterval(state.ocrPollTimer);
            state.ocrPollTimer = null;
            FL.criterionCReview._renderGuidedStep(session, state);
          }
        })
        .catch(function () {
          /* ignore transient poll errors */
        });
    }, 4000);
  },

  _bindCompactReviewPage: function (session, state) {
    FL.criterionCReview._bindOcrRetry(session, state);
    FL.criterionCReview._bindResearchMetadataSave(session, state);
    FL.criterionCReview._bindOcrCompletionPoll(session, state);
    var showGroup = document.getElementById("cc-show-group-field");
    if (showGroup) {
      showGroup.addEventListener("click", function () {
        state.showGroupEditor = true;
        FL.criterionCReview._renderGuidedStep(session, state);
      });
    }
    document.querySelectorAll(".cc-evidence-slot-select").forEach(function (sel) {
      var slotId = sel.getAttribute("data-cc-slot");
      if (
        !slotId
        || !state.canDecide
        || (FL.reviewerAccomplishmentState && !FL.reviewerAccomplishmentState.canVerifyEvidence(state))
      ) {
        return;
      }
      var indicator = document.querySelector('[data-cc-slot-indicator="' + slotId + '"]');
      sel.addEventListener("change", function () {
        FL.criterionCReview._autoSaveSlotVerification(session, state, slotId, sel.value, sel, indicator).then(
          function () {
            FL.criterionCReview._refreshValidationAndRender(session, state);
          }
        );
      });
    });
    var savePrepBtn = document.getElementById("kra2-save-prep-notes");
    if (savePrepBtn) {
      savePrepBtn.addEventListener("click", function () {
        var indicator = document.getElementById("kra2-save-prep-notes-indicator");
        var notesEl = document.getElementById("kra2-prep-notes");
        var remarks = notesEl ? notesEl.value : "";
        savePrepBtn.disabled = true;
        if (indicator) indicator.textContent = "Saving…";
        FL.criterionCEvidence.patchBundle(session, state.doc.id, { remarks: remarks })
          .then(function () {
            return FL.criterionCEvidence.fetchBundle(session, state.doc.id);
          })
          .then(function (fresh) {
            FL.criterionCReview._mergePayloadIntoGuidedState(state, fresh);
            if (indicator) indicator.textContent = "Notes saved";
            if (FL.ui && FL.ui.toast) FL.ui.toast("Preparation notes saved.", "ok");
          })
          .catch(function (err) {
            if (indicator) indicator.textContent = "Could not save";
            if (FL.ui && FL.ui.toast) {
              FL.ui.toast((err && err.message) || "Could not save notes.", "danger");
            }
          })
          .finally(function () {
            savePrepBtn.disabled = false;
          });
      });
    }
    if (!state.canDecide) return;
    if (FL.reviewerAccomplishmentState && FL.reviewerAccomplishmentState.isDraftAwaitingFaculty(state)) {
      return;
    }
    var approveBtn = document.getElementById("cc-approve");
    var rejectBtn = document.getElementById("cc-reject");
    var reloadDocs = function () {
      if (state.doc.facultyId && FL.store.loadFacultyDocuments) {
        return FL.store.loadFacultyDocuments(session, state.doc.facultyId);
      }
      return Promise.resolve();
    };
    if (approveBtn) {
      approveBtn.addEventListener("click", function () {
        if (state.approvalInProgress || approveBtn.disabled) return;
        var remarks = (document.getElementById("cc-remarks").value || "").trim();
        var ptsEl = document.getElementById("cc-assessed-points");
        var pts = ptsEl ? ptsEl.value : "";
        state.approvalInProgress = true;
        approveBtn.disabled = true;
        approveBtn.setAttribute("aria-busy", "true");
        if (rejectBtn) rejectBtn.disabled = true;
        FL.criterionCEvidence.patchBundle(session, state.doc.id, {
          reviewStatus: "approved",
          remarks: remarks,
          assessedPoints: pts === "" ? undefined : Number(pts)
        })
          .then(reloadDocs)
          .then(function () {
            FL.criterionCReview._navigateToCriterionCListAfterApproval(session, state);
          })
          .catch(function (err) {
            state.approvalInProgress = false;
            approveBtn.disabled = false;
            approveBtn.removeAttribute("aria-busy");
            if (rejectBtn) rejectBtn.disabled = false;
            if (FL.ui && FL.ui.toast) FL.ui.toast(err.message || "Approval failed", "danger");
            else alert(err.message || "Approval failed");
          });
      });
    }
    if (rejectBtn) {
      rejectBtn.addEventListener("click", function () {
        var remarks = (document.getElementById("cc-remarks").value || "").trim();
        rejectBtn.disabled = true;
        FL.criterionCEvidence.patchBundle(session, state.doc.id, {
          reviewStatus: "rejected",
          remarks: remarks
        })
          .then(reloadDocs)
          .then(function () {
            return FL.criterionCEvidence.fetchBundle(session, state.doc.id);
          })
          .then(function (fresh) {
            FL.criterionCReview._mergePayloadIntoGuidedState(state, fresh);
            FL.criterionCReview._renderGuidedStep(session, state);
            if (FL.ui && FL.ui.toast) FL.ui.toast("Accomplishment rejected.", "ok");
          })
          .catch(function (err) {
            rejectBtn.disabled = false;
            if (FL.ui && FL.ui.toast) FL.ui.toast(err.message || "Rejection failed", "danger");
          });
      });
    }
  },
};
