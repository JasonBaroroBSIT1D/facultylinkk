/**
 * Document validation against the FacultyLink rules in the manuscript
 * and the evidence requirements of the DBM–CHED Joint Circular.
 * Distinguishes OCR gaps from genuinely missing document content.
 */
window.FL = window.FL || {};

FL.validation = {
  textOf: function (document) {
    const ocr = document.ocr || {};
    const info = document.extractedInfo || {};
    const excerpt = info["OCR excerpt"] || info.OCR || "";
    return [ocr.title, ocr.content, excerpt, document.name].join(" ");
  },

  infoValue: function (document, key) {
    const info = document.extractedInfo || {};
    const value = info[key];
    return value == null ? "" : String(value).trim();
  },

  effectiveTitle: function (document) {
    return FL.validation.infoValue(document, "Extracted title")
      || (document.ocr && document.ocr.title ? String(document.ocr.title).trim() : "")
      || (document.name ? String(document.name).trim() : "");
  },

  effectiveAuthor: function (document) {
    const fromInfo = FL.validation.infoValue(document, "Extracted names")
      || FL.validation.infoValue(document, "Extracted author(s)");
    if (fromInfo) return fromInfo;
    const authors = document.ocr && Array.isArray(document.ocr.authors) ? document.ocr.authors.filter(Boolean) : [];
    return authors.join("; ");
  },

  effectiveDate: function (document) {
    return FL.validation.infoValue(document, "Extracted date")
      || FL.validation.infoValue(document, "Academic year")
      || (document.ocr && document.ocr.date ? String(document.ocr.date).trim() : "");
  },

  effectiveRating: function (document) {
    return FL.validation.infoValue(document, "Extracted rating");
  },

  classify: function (document) {
    if (!document.ocr || document.ocr.status === "processing" || document.ocr.status === "pending") {
      return { status: "pending", matches: [], detected: null, rule: null };
    }
    const text = this.textOf(document);
    const matches = FL.rules.classification.filter(function (rule) {
      return rule.keywords.some(function (keyword) {
        return text.toLowerCase().indexOf(keyword.toLowerCase()) !== -1;
      });
    }).sort(function (a, b) { return a.priority - b.priority; });
    if (!matches.length) {
      return { status: "unclassified", matches: [], detected: null, rule: null };
    }
    const detected = matches[0];
    return {
      status: matches.length > 1 ? "priority" : "classified",
      matches: matches,
      detected: detected,
      rule: detected
    };
  },

  fields: function (document) {
    const title = !!FL.validation.effectiveTitle(document);
    const author = !!FL.validation.effectiveAuthor(document);
    const date = !!FL.validation.effectiveDate(document);
    return {
      title: title,
      author: author,
      date: date,
      titleValue: FL.validation.effectiveTitle(document),
      authorValue: FL.validation.effectiveAuthor(document),
      dateValue: FL.validation.effectiveDate(document),
      ratingValue: FL.validation.effectiveRating(document)
    };
  },

  indicatorRequirements: function (document) {
    const items = [];
    const indicatorId = document.indicatorId;
    if (!indicatorId) {
      items.push({ kind: "ineligible", label: "Indicator", message: "Match an applicable DBM–CHED indicator." });
      return items;
    }
    const found = FL.rules.findIndicator(indicatorId);
    if (!found) {
      items.push({ kind: "ineligible", label: "Indicator", message: "The selected indicator is not in the official rule set." });
      return items;
    }
    const iid = indicatorId.toLowerCase();
    const fields = FL.validation.fields(document);
    const rating = fields.ratingValue;
    const info = document.extractedInfo || {};

    if (iid.indexOf("student") >= 0 || iid.indexOf("supervisor") >= 0 || (found.indicator.formula && found.indicator.formula.type === "rating")) {
      if (!rating) {
        items.push({
          kind: "ocr_gap",
          label: "Evaluation rating",
          message: "Overall SET/SEF rating is missing from extracted metadata. Correct it if the rating is visible in the original document."
        });
      }
      if (!fields.date) {
        items.push({
          kind: "ocr_gap",
          label: "Academic period",
          message: "Academic year or semester is missing from extracted metadata."
        });
      }
      if (!fields.author) {
        items.push({
          kind: "ocr_gap",
          label: "Faculty name",
          message: "Faculty name is missing from extracted metadata."
        });
      }
      return items;
    }

    if (!fields.author) {
      items.push({
        kind: "ocr_gap",
        label: "Named party",
        message: "The identity name for this indicator was not extracted."
      });
    }
    if (!fields.title) {
      items.push({
        kind: "ocr_gap",
        label: "Title",
        message: "Document title was not extracted."
      });
    }
    if (!fields.date) {
      items.push({
        kind: "ocr_gap",
        label: "Date / period",
        message: "Document date or coverage period was not extracted."
      });
    }

    const evidence = found.indicator.evidence || [];
    if (evidence.length > 1 && info["Supporting evidence verified"] !== "yes") {
      items.push({
        kind: "missing_evidence",
        label: "Supporting documents",
        message: "Annex A requires additional supporting documents: " + evidence.join("; ")
      });
    }

    const identity = info["Identity verification"] || "";
    if (identity && identity.toLowerCase().indexOf("does not match") >= 0) {
      items.push({ kind: "invalid", label: "Identity", message: identity });
    } else if (identity && identity.toLowerCase().indexOf("not read") >= 0 && !info["Reviewer verified extraction"]) {
      items.push({ kind: "ocr_gap", label: "Identity", message: identity });
    }

    return items;
  },

  evidence: function (document) {
    if (!document.indicatorId) return { status: "missing", missing: ["An applicable DBM–CHED indicator has not been matched."] };
    const found = FL.rules.findIndicator(document.indicatorId);
    if (!found) return { status: "missing", missing: ["The selected indicator is not in the Joint Circular rule set."] };
    const info = document.extractedInfo || {};
    const evidence = found.indicator.evidence || [];
    if (evidence.length > 1 && info["Supporting evidence verified"] !== "yes") {
      return { status: "missing", missing: evidence };
    }
    if (document.evidenceComplete === false) {
      return { status: "missing", missing: found.indicator.evidence };
    }
    if (document.status === "rejected" || document.status === "revision") {
      return { status: "missing", missing: ["The reviewer found that the attached file does not satisfy the evidence for this indicator."] };
    }
    return { status: "complete", missing: [] };
  },

  duplicate: function (document) {
    if (document.duplicateOf) {
      return { status: "duplicate", matchId: document.duplicateOf };
    }
    const match = FL.store.documents.find(function (other) {
      return other.id !== document.id && other.hash && other.hash === document.hash && other.dateSubmitted <= document.dateSubmitted;
    });
    if (match) return { status: "duplicate", matchId: match.id };
    return { status: "clear", matchId: null };
  },

  evaluate: function (document) {
    const classification = this.classify(document);
    const fields = this.fields(document);
    const requirements = this.indicatorRequirements(document);
    const evidence = this.evidence(document);
    const duplicate = this.duplicate(document);
    const reasons = [];
    let overall = "valid";
    const info = document.extractedInfo || {};
    const backendValidation = (info["Validation status"] || "").trim().toLowerCase();
    if (backendValidation === "valid" && document.status === "system_approved") {
      return {
        fields: fields,
        requirements: requirements,
        classification: classification,
        evidenceStatus: evidence.status,
        evidenceMissing: evidence.missing,
        duplicateStatus: duplicate.status === "duplicate" ? "duplicate" : "clear",
        duplicateOf: duplicate.matchId,
        overall: "valid",
        reasons: reasons,
        backendAuthoritative: true
      };
    }
    if (backendValidation === "needs verification") {
      overall = "reviewer-required";
      if (info["Review reasons"]) {
        reasons.push(String(info["Review reasons"]));
      }
    }
    if (backendValidation === "invalid") {
      overall = "invalid";
    }

    if (document.ocr && (document.ocr.status === "processing" || document.ocr.status === "pending")) {
      overall = "reviewer-required";
      reasons.push("OCR extraction is not finished, so the document cannot be validated yet.");
    } else {
      requirements.forEach(function (item) {
        reasons.push(item.message);
      });
      if (duplicate.status === "duplicate") {
        overall = "invalid";
        reasons.push("Duplicate file hash of " + duplicate.matchId + ". Duplicate documents are ignored.");
      } else if (requirements.some(function (item) { return item.kind === "invalid"; })) {
        overall = "invalid";
      } else if (requirements.some(function (item) { return item.kind === "missing_evidence"; })) {
        overall = "reviewer-required";
      } else if (requirements.some(function (item) { return item.kind === "ocr_gap"; })) {
        overall = "reviewer-required";
      } else if (classification.status === "unclassified" && !document.indicatorId) {
        overall = "reviewer-required";
        reasons.push("The document cannot be classified from the extracted text.");
      }
    }

    if (evidence.status === "missing" && overall === "valid") {
      reasons.push("Required documentary evidence is incomplete.");
      overall = "reviewer-required";
    }

    return {
      fields: fields,
      requirements: requirements,
      classification: classification,
      evidenceStatus: evidence.status,
      evidenceMissing: evidence.missing,
      duplicateStatus: duplicate.status === "duplicate" ? "duplicate" : "clear",
      duplicateOf: duplicate.matchId,
      overall: overall,
      reasons: reasons
    };
  },

  approvalGate: function (document) {
    const result = this.evaluate(document);
    const blockers = [];
    const fields = result.fields;
    if (result.duplicateStatus === "duplicate") {
      blockers.push({ kind: "invalid", message: "Duplicate file hash. This document cannot be approved." });
    }
    if (!document.indicatorId) {
      blockers.push({ kind: "ineligible", message: "Match an Annex I indicator before approval." });
    }
    result.requirements.forEach(function (item) {
      if (item.kind === "missing_evidence" || item.kind === "invalid") {
        blockers.push({ kind: item.kind, message: item.message });
      }
    });
    if (!fields.title) {
      blockers.push({
        kind: "ocr_gap",
        message: "Title is missing from extracted metadata. Correct extracted information if the title is visible on the original document, or request revision if it is absent."
      });
    }
    if (!fields.author) {
      blockers.push({
        kind: "ocr_gap",
        message: "Identity name is missing from extracted metadata. Correct extracted information if the faculty or author name is visible on the document."
      });
    }
    if (!fields.date) {
      blockers.push({
        kind: "ocr_gap",
        message: "Date or academic period is missing from extracted metadata. Correct extracted information if it appears on the document."
      });
    }
    const found = document.indicatorId ? FL.rules.findIndicator(document.indicatorId) : null;
    const needsRating = found && found.indicator.formula && found.indicator.formula.type === "rating";
    if (needsRating && !fields.ratingValue) {
      blockers.push({
        kind: "ocr_gap",
        message: "Evaluation rating is missing. Enter the verified rating under Correct extracted information before approval."
      });
    }
    return {
      ok: blockers.length === 0,
      blockers: blockers,
      validation: result
    };
  },

  formatBlockers: function (blockers) {
    if (!blockers || !blockers.length) return "";
    return blockers.map(function (item) { return item.message; }).join(" ");
  }
};
