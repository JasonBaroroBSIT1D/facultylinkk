/**
 * FacultyLink scoring.
 * Final Score = Base Points × Contribution Percentage.
 * Caps are the maximums stated in DBM–CHED Joint Circular No. 01, s. 2026.
 */
window.FL = window.FL || {};

FL.scoring = {
  formula: "Final Score = Base Points × Contribution Percentage",
  weightedFormula: "Weighted Final Score = Σ (KRA points × Table 2.2 rank weight %)",

  // DBM–CHED Joint Circular Table 2.2 — percentages by faculty rank band.
  table22Defaults: {
    "Instructor": { kra1: 60, kra2: 10, kra3: 20, kra4: 10 },
    "Asst. Professor": { kra1: 50, kra2: 20, kra3: 20, kra4: 10 },
    "Assoc. Professor": { kra1: 40, kra2: 30, kra3: 20, kra4: 10 },
    "Professor": { kra1: 30, kra2: 40, kra3: 20, kra4: 10 },
    "College/University Professor": { kra1: 20, kra2: 50, kra3: 20, kra4: 10 }
  },

  round(value) {
    return Math.round((value + Number.EPSILON) * 100) / 100;
  },

  resolveRankBand(rank) {
    const text = String(rank || "").toLowerCase();
    if (!text) return "Instructor";
    if (text.indexOf("college") >= 0 || text.indexOf("university professor") >= 0 || text.indexOf("col./univ") >= 0) {
      return "College/University Professor";
    }
    if (text.indexOf("assoc") >= 0) return "Assoc. Professor";
    if (text.indexOf("asst") >= 0 || text.indexOf("assistant") >= 0) return "Asst. Professor";
    if (text.indexOf("professor") >= 0) return "Professor";
    return "Instructor";
  },

  weightsForRank(rank) {
    const band = this.resolveRankBand(rank);
    const published = (FL.store && FL.store.kraSettings && FL.store.kraSettings.rankWeights) || {};
    const source = published[band] || this.table22Defaults[band] || this.table22Defaults.Instructor;
    const map = {};
    ["kra1", "kra2", "kra3", "kra4"].forEach(function (kraId) {
      const mobile = { kra1: "instruction", kra2: "research", kra3: "extension", kra4: "professionalDevelopment" }[kraId];
      const value = source[kraId] != null ? source[kraId] : source[mobile];
      map[kraId] = Number(value) || 0;
    });
    return { band: band, weights: map };
  },

  weightedScore(kras, rank) {
    const resolved = this.weightsForRank(rank);
    let total = 0;
    kras.forEach(function (kra) {
      const percent = resolved.weights[kra.id] || 0;
      const capped = kra.credited != null
        ? Number(kra.credited)
        : Math.min(Number(kra.maxPoints) || 0, (Number(kra.earned) || 0) + (Number(kra.bonus) || 0));
      total += capped * (percent / 100);
    });
    return {
      band: resolved.band,
      weights: resolved.weights,
      score: this.round(total)
    };
  },

  basePoints(indicator, document) {
    if (!indicator) return null;
    if (indicator.formula && indicator.formula.type === "rating") {
      const rating = Number(document.ratingInput);
      if (!Number.isFinite(rating)) return null;
      return this.round((rating / 100) * indicator.formula.multiplier);
    }
    if (typeof indicator.points === "number") return indicator.points;
    return null;
  },

  subjectContribution(document) {
    const rows = document.contribution || [];
    const subject = rows.find(function (row) { return row.subject; }) || rows[0];
    if (!subject || typeof subject.percent !== "number") return null;
    return subject;
  },

  scoreDocument(document) {
    if (document.review && typeof document.review.finalScore === "number" && document.status === "approved") {
      const review = document.review;
      const found = review.indicatorId ? FL.rules.findIndicator(review.indicatorId) : null;
      const validation = FL.validation.evaluate(document);
      return {
        kra: found ? found.kra : null,
        criterion: found ? found.criterion : null,
        indicator: found ? found.indicator : null,
        basePoints: review.assignedScore,
        contributionPercent: review.contributionPercent,
        finalScore: review.finalScore,
        officialMax: review.officialMax,
        officialLabel: review.officialLabel || "",
        historical: true,
        countable: validation.duplicateStatus !== "duplicate",
        rows: (document.contribution || []).map(function (row) {
          return { author: row.author, percent: row.percent, subject: !!row.subject, computed: row.subject ? review.finalScore : null };
        }),
        validation: validation
      };
    }
    if (typeof document.databasePoints === "number") {
      const found = document.indicatorId ? FL.rules.findIndicator(document.indicatorId) : null;
      const validation = FL.validation.evaluate(document);
      return {
        kra: found ? found.kra : null,
        criterion: found ? found.criterion : null,
        indicator: found ? found.indicator : null,
        basePoints: document.databasePoints,
        contributionPercent: 100,
        finalScore: document.databasePoints,
        countable: (document.status === "approved" || document.status === "system-approved")
          && validation.duplicateStatus !== "duplicate",
        rows: (document.contribution || []).map(function (row) {
          return { author: row.author, percent: row.percent, subject: !!row.subject, computed: document.databasePoints };
        }),
        validation: validation
      };
    }
    const found = document.indicatorId ? FL.rules.findIndicator(document.indicatorId) : null;
    const indicator = found ? found.indicator : null;
    const validation = FL.validation.evaluate(document);
    const countable = validation.overall === "valid" && document.status === "approved" && validation.duplicateStatus !== "duplicate";
    const base = indicator ? this.basePoints(indicator, document) : null;
    let percent = null;
    if (indicator && indicator.contribution === "declared") {
      const subject = this.subjectContribution(document);
      percent = subject ? subject.percent : null;
    } else if (indicator && (indicator.contribution === "sole" || indicator.contribution === "fixed" || indicator.contribution === "not-applicable")) {
      percent = 100;
    }
    let finalScore = null;
    if (base !== null && percent !== null) {
      finalScore = this.round(base * (percent / 100));
    }
    const rows = (document.contribution || []).map(function (row) {
      const computed = base === null ? null : FL.scoring.round(base * (row.percent / 100));
      return { author: row.author, percent: row.percent, subject: !!row.subject, computed: computed };
    });
    return {
      kra: found ? found.kra : null,
      criterion: found ? found.criterion : null,
      indicator: indicator,
      basePoints: base,
      contributionPercent: percent,
      finalScore: finalScore,
      countable: countable,
      rows: rows,
      validation: validation
    };
  },

  aggregateFaculty(facultyId) {
    const documents = FL.store.documents.filter(function (doc) { return doc.facultyId === facultyId; });
    const kras = FL.rules.kras.map(function (kra) {
      const criteria = kra.criteria.map(function (criterion) {
        return { id: criterion.id, name: criterion.name, maxPoints: criterion.maxPoints, bonus: !!criterion.bonus, earned: 0, locked: 0, documents: [] };
      });
      return {
        id: kra.id,
        code: kra.code,
        name: kra.name,
        maxPoints: kra.maxPoints,
        bonusMax: kra.bonusMax || 0,
        criteria: criteria,
        earned: 0,
        bonus: 0
      };
    });
    const byId = {};
    kras.forEach(function (kra) { byId[kra.id] = kra; });
    const groupTotals = {};
    const bestByIndicator = {};
    const provisionalByIndicator = {};

    documents.forEach(function (doc) {
      if (
        doc.status === "system-approved"
        && (typeof doc.databasePoints === "number" || typeof doc.effectiveSimulationScore === "number")
        && doc.indicatorId
      ) {
        const found = FL.rules.findIndicator(doc.indicatorId);
        if (found) {
          const indicatorKey = doc.indicatorId;
          const review = {
            indicatorId: doc.indicatorId,
            kraId: found.kra.id,
            criterionId: found.criterion.id,
            finalScore: doc.databasePoints,
            assignedScore: doc.databasePoints,
            contributionPercent: 100,
            officialMax: found.indicator.maxPoints
          };
          const current = bestByIndicator[indicatorKey];
          if (!current || review.finalScore > current.review.finalScore) {
            bestByIndicator[indicatorKey] = { doc: doc, review: review };
          }
        }
        return;
      }
      if (doc.review && typeof doc.review.finalScore === "number" && doc.status === "approved") {
        const review = doc.review;
        const indicatorKey = review.indicatorId || doc.indicatorId || doc.id;
        const current = bestByIndicator[indicatorKey];
        if (!current || review.finalScore > current.review.finalScore) {
          bestByIndicator[indicatorKey] = { doc: doc, review: review };
        }
        return;
      }
      if (doc.status === "pending-review" || doc.status === "pendingReview") {
        const effective = FL.documents.effectiveSimulationScore(doc);
        if (effective !== null && doc.indicatorId) {
          const found = FL.rules.findIndicator(doc.indicatorId);
          if (found) {
            const review = {
              indicatorId: doc.indicatorId,
              kraId: found.kra.id,
              criterionId: found.criterion.id,
              finalScore: effective,
              assignedScore: effective,
              contributionPercent: 100,
              officialMax: found.indicator.maxPoints
            };
            const indicatorKey = doc.indicatorId;
            const current = bestByIndicator[indicatorKey];
            if (!current || review.finalScore > current.review.finalScore) {
              bestByIndicator[indicatorKey] = { doc: doc, review: review, autoScored: true };
            }
          }
          return;
        }
        const provisional = FL.scoring.scoreDocument(doc);
        if (provisional.finalScore !== null && provisional.indicator && provisional.kra) {
          const key = provisional.indicator.id;
          const previous = provisionalByIndicator[key];
          if (!previous || provisional.finalScore > previous.scored.finalScore) {
            provisionalByIndicator[key] = { doc: doc, scored: provisional };
          }
        }
        return;
      }
      if (typeof doc.databasePoints === "number") {
        if (doc.status !== "approved" || !doc.kraId || !byId[doc.kraId]) return;
        const kra = byId[doc.kraId];
        const criterion = kra.criteria[0];
        criterion.earned = FL.scoring.round(criterion.earned + doc.databasePoints);
        criterion.documents.push({ id: doc.id, name: doc.name, points: doc.databasePoints });
        return;
      }
      const scored = FL.scoring.scoreDocument(doc);
      if (!scored.countable || scored.finalScore === null || !scored.kra) return;
      const kra = byId[scored.kra.id];
      const criterion = kra.criteria.find(function (item) { return item.id === scored.criterion.id; });
      let points = scored.finalScore;
      const group = scored.indicator.groupMax;
      if (group) {
        const key = facultyId + ":" + group.group;
        const used = groupTotals[key] || 0;
        const room = Math.max(0, group.max - used);
        points = Math.min(points, room);
        groupTotals[key] = used + points;
      }
      const roomInCriterion = Math.max(0, criterion.maxPoints - criterion.earned);
      points = FL.scoring.round(Math.min(points, roomInCriterion));
      criterion.earned = FL.scoring.round(criterion.earned + points);
      criterion.documents.push({ id: doc.id, name: doc.name, points: points });
    });

    const verifiedKeys = Object.keys(bestByIndicator).sort(function (left, right) {
      const difference = bestByIndicator[right].review.finalScore - bestByIndicator[left].review.finalScore;
      return difference || left.localeCompare(right);
    });
    verifiedKeys.forEach(function (indicatorKey) {
      const entry = bestByIndicator[indicatorKey];
      const review = entry.review;
      const doc = entry.doc;
      const kra = byId[review.kraId];
      if (!kra) return;
      const criterion = kra.criteria.find(function (item) { return item.id === review.criterionId; }) || kra.criteria[0];
      if (!criterion) return;
      const found = review.indicatorId ? FL.rules.findIndicator(review.indicatorId) : null;
      let points = review.finalScore;
      if (found && typeof found.indicator.maxPoints === "number") {
        points = Math.min(points, found.indicator.maxPoints);
      }
      const group = found && found.indicator.groupMax;
      if (group) {
        const key = facultyId + ":" + group.group;
        const used = groupTotals[key] || 0;
        const room = Math.max(0, group.max - used);
        points = Math.min(points, room);
        groupTotals[key] = used + points;
      }
      const roomInCriterion = Math.max(0, criterion.maxPoints - criterion.earned);
      points = FL.scoring.round(Math.min(points, roomInCriterion));
      if (points <= 0) return;
      criterion.earned = FL.scoring.round(criterion.earned + points);
      criterion.locked = FL.scoring.round(criterion.locked + points);
      criterion.documents.push({ id: doc.id, name: doc.name, points: points, provisional: false });
    });

    Object.keys(provisionalByIndicator).forEach(function (indicatorKey) {
      if (bestByIndicator[indicatorKey]) return;
      const entry = provisionalByIndicator[indicatorKey];
      const scored = entry.scored;
      const kra = byId[scored.kra.id];
      if (!kra) return;
      const criterion = kra.criteria.find(function (item) { return item.id === scored.criterion.id; }) || kra.criteria[0];
      if (!criterion) return;
      criterion.documents.push({ id: entry.doc.id, name: entry.doc.name, points: 0, provisional: true });
      kra.provisional = true;
    });

    kras.forEach(function (kra) {
      let regular = 0;
      let bonus = 0;
      kra.criteria.forEach(function (criterion) {
        criterion.earned = FL.scoring.round(Math.min(criterion.earned, criterion.maxPoints));
        criterion.locked = FL.scoring.round(Math.min(criterion.locked || 0, criterion.earned));
        if (criterion.bonus) {
          bonus += criterion.earned;
        } else {
          regular += criterion.earned;
        }
      });
      const bonusCeiling = kra.bonusMax || 0;
      kra.earned = FL.scoring.round(Math.min(kra.maxPoints, regular));
      kra.bonus = FL.scoring.round(Math.min(bonusCeiling, bonus));
      kra.credited = FL.scoring.round(Math.min(kra.maxPoints, kra.earned + kra.bonus));
    });

    const rawTotal = this.round(kras.reduce(function (sum, kra) { return sum + (kra.credited || 0); }, 0));
    return { kras: kras, rawTotal: rawTotal, total: rawTotal, documents: documents };
  },

  simulation(facultyId) {
    const faculty = FL.store.facultyById(facultyId);
    const aggregate = this.aggregateFaculty(facultyId);
    const weighted = this.weightedScore(aggregate.kras, faculty ? faculty.rank : "");
    aggregate.weightBand = weighted.band;
    aggregate.appliedWeights = weighted.weights;
    aggregate.weightedScore = Math.round(weighted.score);
    aggregate.total = aggregate.weightedScore;
    const gaps = [];
    aggregate.documents.forEach(function (doc) {
      const scored = FL.scoring.scoreDocument(doc);
      const validation = scored.validation;
      if (validation.duplicateStatus === "duplicate") {
        gaps.push({ tone: "info", text: doc.id + " is a duplicate of " + (doc.duplicateOf || "an existing file") + " and is ignored." });
        return;
      }
      if (validation.overall === "invalid") {
        gaps.push({ tone: "danger", text: doc.id + " is invalid. " + validation.reasons.join(" ") });
      } else if (validation.overall === "reviewer-required") {
        gaps.push({ tone: "warning", text: doc.id + " requires reviewer validation. " + validation.reasons.join(" ") });
      } else if (doc.status === "revision") {
        gaps.push({ tone: "warning", text: doc.id + " was returned for revision." });
      } else if (doc.status === "rejected") {
        gaps.push({ tone: "danger", text: doc.id + " was rejected and is not included in the estimate." });
      } else if (doc.status === "pending-review" || doc.status === "pendingReview") {
        const effective = FL.documents.effectiveSimulationScore(doc);
        if (effective === null) {
          gaps.push({ tone: "info", text: doc.id + " is incomplete or invalid — score unavailable for simulation." });
        } else {
          gaps.push({ tone: "ok", text: doc.id + " is automatically scored in the simulation (" + effective + " pts) while awaiting reviewer check." });
        }
      }
      if (validation.evidenceStatus === "missing") {
        gaps.push({ tone: "danger", text: doc.id + " is missing required documentary evidence." });
      }
    });
    aggregate.kras.forEach(function (kra) {
      if (kra.earned === 0) {
        gaps.push({ tone: "warning", text: kra.code + " — " + kra.name + " has no approved points in this estimate." });
      }
    });
    gaps.push({
      tone: "info",
      text: "Table 2.2 weight band: " + weighted.band +
        " (Instruction " + weighted.weights.kra1 +
        "%, Research " + weighted.weights.kra2 +
        "%, Extension " + weighted.weights.kra3 +
        "%, Professional Development " + weighted.weights.kra4 + "%)."
    });
    if (gaps.filter(function (gap) { return gap.tone !== "info" && gap.tone !== "ok"; }).length === 0) {
      gaps.push({ tone: "ok", text: "No missing-field, classification, or duplicate gaps were found in the approved documents. Official sub-rank determination remains with the evaluation committees and the governing board." });
    }
    return { faculty: faculty, aggregate: aggregate, gaps: gaps };
  }
};
