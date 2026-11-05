/**
 * Evidence Workspace navigation — accomplishment list and KRA accomplishment review (Admin monitor + Reviewer review).
 * Standalone document-review.html / document-view.html redirect here; do not use tabbed Document Review UI.
 */
window.FL = window.FL || {};

FL.reviewerNav = {
  criterionToKra: function (criterionId) {
    var cid = (criterionId || "").trim();
    if (cid.indexOf("kra4-") === 0) return "kra4";
    if (cid.indexOf("kra3-") === 0) return "kra3";
    if (cid.indexOf("kra2-") === 0) return "kra2";
    if (cid.indexOf("kra1-") === 0) return "kra1";
    return "";
  },

  criterionWorkspaceUrl: function (opts) {
    opts = opts || {};
    var params = new URLSearchParams();
    if (opts.facultyId) params.set("faculty", opts.facultyId);
    if (opts.kraId) params.set("kra", opts.kraId);
    if (opts.criterionId) params.set("criterion", opts.criterionId);
    if (opts.indicatorId) params.set("indicator", opts.indicatorId);
    if (opts.docFilter && opts.docFilter !== "all") params.set("filter", opts.docFilter);
    if (opts.focusDoc) params.set("focusDoc", opts.focusDoc);
    if (opts.scrollDoc) params.set("scrollDoc", opts.scrollDoc);
    if (opts.highlightDoc) params.set("highlightDoc", opts.highlightDoc);
    if (opts.tev) params.set("tev", opts.tev);
    var qs = params.toString();
    return "documents.html" + (qs ? "?" + qs : "");
  },

  evidenceLink: function (doc) {
    var info = doc && doc.extractedInfo;
    if (!info) return null;
    return (
      info.kra2EvidenceLink ||
      info.kra3EvidenceLink ||
      info.kra4EvidenceLink ||
      info.criterionBEvidenceLink ||
      info.criterionCEvidenceLink ||
      null
    );
  },

  isLinkedSupportingDocument: function (doc) {
    if (!doc) return false;
    if (doc.kra2Evidence && doc.kra2Evidence.isSupportingDocument) return true;
    if (doc.criterionBEvidence && doc.criterionBEvidence.isSupportingDocument) return true;
    if (doc.criterionCEvidence && doc.criterionCEvidence.isSupportingDocument) return true;
    var link = FL.reviewerNav.evidenceLink(doc);
    return !!(link && link.role === "supporting" && link.primaryDocumentId);
  },

  primaryDocumentIdFor: function (doc) {
    var link = FL.reviewerNav.evidenceLink(doc);
    if (link && link.primaryDocumentId) return link.primaryDocumentId;
    return "";
  },

  isPrimaryAccomplishmentDocument: function (doc) {
    if (!doc || !doc.criterionId) return false;
    var cid = doc.criterionId;
    if (cid === "kra1-b" && FL.criterionBWorkspaceUi && FL.criterionBWorkspaceUi.isPrimaryClaimDocument) {
      return FL.criterionBWorkspaceUi.isPrimaryClaimDocument(doc);
    }
    if (cid === "kra1-c" && FL.criterionCWorkspaceUi && FL.criterionCWorkspaceUi.isPrimaryClaimDocument) {
      return FL.criterionCWorkspaceUi.isPrimaryClaimDocument(doc);
    }
    if (FL.documents) {
      if (FL.documents._isKra2Criterion && FL.documents._isKra2Criterion(cid)) {
        return FL.documents._isKra2PrimaryAccomplishment(doc);
      }
      if (FL.documents._isKra3Criterion && FL.documents._isKra3Criterion(cid)) {
        return FL.documents._isKra3PrimaryAccomplishment(doc);
      }
      if (FL.documents._isKra4Criterion && FL.documents._isKra4Criterion(cid)) {
        return FL.documents._isKra4PrimaryAccomplishment(doc);
      }
    }
    return false;
  },

  isAccomplishmentCriterion: function (criterionId) {
    var cid = criterionId || "";
    return (
      cid === "kra1-b"
      || cid === "kra1-c"
      || cid.indexOf("kra2-") === 0
      || cid.indexOf("kra3-") === 0
      || cid.indexOf("kra4-") === 0
    );
  },

  /** Resolve faculty / KRA / criterion and primary accomplishment for in-workspace review. */
  resolveAccomplishmentReviewTarget: function (doc) {
    doc = doc || {};
    var criterionId = doc.criterionId || "";
    var kraId = doc.kraId || FL.reviewerNav.criterionToKra(criterionId);
    var facultyId = doc.facultyId || "";
    var docId = doc.id || doc.documentId || "";

    if (criterionId === "kra1-a") {
      return {
        mode: "criterion-a",
        url: FL.reviewerNav.criterionWorkspaceUrl({
          facultyId: facultyId,
          kraId: kraId || "kra1",
          criterionId: "kra1-a",
          indicatorId: doc.indicatorId,
          tev: doc.teachingEvaluationId || doc.tevId || "",
          docFilter: "all"
        })
      };
    }

    if (
      criterionId === "kra1-b"
      && FL.criterionBWorkspaceUi
      && !FL.criterionBWorkspaceUi.isPrimaryClaimDocument(doc)
      && !FL.reviewerNav.isLinkedSupportingDocument(doc)
    ) {
      return {
        mode: "classify",
        url: FL.reviewerNav.criterionWorkspaceUrl({
          facultyId: facultyId,
          kraId: kraId || "kra1",
          criterionId: criterionId,
          highlightDoc: docId,
          docFilter: "all"
        })
      };
    }

    if (!FL.reviewerNav.isAccomplishmentCriterion(criterionId)) {
      return {
        mode: "workspace",
        url: FL.reviewerNav.criterionWorkspaceUrl({
          facultyId: facultyId,
          kraId: kraId,
          criterionId: criterionId,
          indicatorId: doc.indicatorId,
          highlightDoc: docId,
          docFilter: "all"
        })
      };
    }

    var focusDocId = docId;
    var scrollDocId = "";
    if (FL.reviewerNav.isLinkedSupportingDocument(doc) || !FL.reviewerNav.isPrimaryAccomplishmentDocument(doc)) {
      var primary = FL.reviewerNav.primaryDocumentIdFor(doc);
      if (primary) {
        focusDocId = primary;
        scrollDocId = docId;
      } else if (!FL.reviewerNav.isPrimaryAccomplishmentDocument(doc)) {
        return {
          mode: "classify",
          url: FL.reviewerNav.criterionWorkspaceUrl({
            facultyId: facultyId,
            kraId: kraId,
            criterionId: criterionId,
            highlightDoc: docId,
            docFilter: "all"
          })
        };
      }
    }

    return {
      mode: "accomplishment",
      url: FL.reviewerNav.criterionWorkspaceUrl({
        facultyId: facultyId,
        kraId: kraId,
        criterionId: criterionId,
        indicatorId: doc.indicatorId,
        focusDoc: focusDocId,
        scrollDoc: scrollDocId,
        docFilter: "all"
      }),
      focusDocId: focusDocId,
      scrollDocId: scrollDocId
    };
  },

  /** All reviewer document / Review / Open Review links for accomplishment workflows. */
  accomplishmentReviewUrl: function (doc) {
    var target = FL.reviewerNav.resolveAccomplishmentReviewTarget(doc);
    return (target && target.url) || "documents.html";
  },

  /** @deprecated alias — use accomplishmentReviewUrl */
  documentReviewUrl: function (doc) {
    return FL.reviewerNav.accomplishmentReviewUrl(doc);
  },

  reviewUrlFromDoc: function (doc) {
    return FL.reviewerNav.accomplishmentReviewUrl(doc);
  },

  /** Merge URL query context onto a document record (faculty, KRA, criterion, indicator, TEV). */
  enrichDocFromUrlParams: function (doc, params) {
    doc = Object.assign({}, doc || {});
    params = params || new URLSearchParams(window.location.search);
    if (!doc.id && !doc.documentId) {
      var fromUrl = params.get("id") || params.get("documentId");
      if (fromUrl) doc.id = fromUrl;
    }
    if (!doc.facultyId && params.get("faculty")) doc.facultyId = params.get("faculty");
    if (!doc.kraId && params.get("kra")) doc.kraId = params.get("kra");
    if (!doc.criterionId && params.get("criterion")) doc.criterionId = params.get("criterion");
    if (!doc.indicatorId && params.get("indicator")) doc.indicatorId = params.get("indicator");
    var tev = params.get("tev");
    if (tev) doc.teachingEvaluationId = tev;
    return doc;
  },

  redirectLegacyDocumentReview: function (session) {
    var params = new URLSearchParams(window.location.search);
    var docId = params.get("id") || params.get("documentId");
    if (!docId) {
      window.location.replace("documents.html");
      return Promise.resolve();
    }
    var load = FL.store.usesLiveDocuments()
      ? FL.store.refreshLiveDocument(session, docId)
      : Promise.resolve(FL.store.documentById(docId));
    return load.then(function (doc) {
      if (!doc) {
        throw new Error("Document was not found.");
      }
      doc = FL.reviewerNav.enrichDocFromUrlParams(doc, params);
      window.location.replace(FL.reviewerNav.accomplishmentReviewUrl(doc));
    });
  }
};
