/**
 * Shared Administrator / Reviewer KRA configuration UI.
 * Renders official rules from FL.rules (DBM–CHED JC No. 01, s. 2026 — Annex A).
 * Score overrides persist via mock API / localStorage until PostgreSQL integration exists.
 */
window.FL = window.FL || {};

FL.kraConfig = {
  icons: {
    kra1: "<svg viewBox=\"0 0 24 24\" aria-hidden=\"true\"><path fill=\"currentColor\" d=\"M12 3 1 9l11 6 9-4.91V17h2V9L12 3zm0 8.18L4.74 9.5 12 5.82l7.26 3.68L12 11.18zM5 13.5v5L12 22l7-3.5v-5l-7 3.5-7-3.5z\"/></svg>",
    kra2: "<svg viewBox=\"0 0 24 24\" aria-hidden=\"true\"><path fill=\"currentColor\" d=\"M6 2h12a2 2 0 0 1 2 2v3H4V4a2 2 0 0 1 2-2zm-2 7h16v9a2 2 0 0 1-2 2h-3.5l1 2h-3l-1-2H8l-1 2H4l1-2H4a2 2 0 0 1-2-2V9zm4 2v2h2v-2H8zm4 0v2h2v-2h-2zm4 0v2h2v-2h-2z\"/></svg>",
    kra3: "<svg viewBox=\"0 0 24 24\" aria-hidden=\"true\"><path fill=\"currentColor\" d=\"M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5s-3 1.34-3 3 1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5C15 14.17 10.33 13 8 13zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z\"/></svg>",
    kra4: "<svg viewBox=\"0 0 24 24\" aria-hidden=\"true\"><path fill=\"currentColor\" d=\"M20 6h-4V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2H4c-1.1 0-2 .9-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2zM10 4h4v2h-4V4zm6 14H8v-2h8v2z\"/></svg>"
  },

  persistenceNote: function () {
    return "Official criteria and evidence come from " + FL.rules.annex + " in rules.js. "
      + "Saved point overrides are stored in this browser via the demo API (localStorage), not in PostgreSQL "
      + "kra_configuration until a Flask admin endpoint is connected.";
  },

  configStatusLabel: function (editable) {
    if (!editable) return { kind: "valid", text: "Published reference" };
    const saved = FL.store && FL.store.kraSettings ? FL.store.kraSettings : {};
    const hasOverrides = !!(saved.kras && Object.keys(saved.kras).length)
      || !!(saved.criteria && Object.keys(saved.criteria).length)
      || !!(saved.indicators && Object.keys(saved.indicators).length)
      || !!(saved.indicatorMeta && Object.keys(saved.indicatorMeta).length);
    return hasOverrides
      ? { kind: "pending", text: "Custom scores saved locally" }
      : { kind: "valid", text: "Official Annex A defaults" };
  },

  indicatorFormulaDisplay: function (indicator) {
    if (indicator.formulaNote) return indicator.formulaNote;
    return FL.documents.indicatorFormulaText(indicator);
  },

  indicatorDescription: function (indicator) {
    if (indicator.description) return indicator.description;
    return "";
  },

  mergeSettingsPayload: function (pageDraft, pageReadInputs) {
    if (pageReadInputs) pageReadInputs();
    const base = pageDraft ? JSON.parse(JSON.stringify(pageDraft)) : FL.rules.scoreDraft();
    const stored = (FL.store && FL.store.kraSettings) || {};
    base.indicatorMeta = JSON.parse(JSON.stringify(stored.indicatorMeta || {}));
    return base;
  },

  openIndicatorEditor: function (indicatorId, options) {
    const opts = options || {};
    const found = FL.rules.findIndicator(indicatorId);
    if (!found) {
      FL.ui.toast("Indicator was not found.", "danger");
      return;
    }
    const editable = !!opts.editable;
    const kra = found.kra;
    const criterion = found.criterion;
    const indicator = found.indicator;
    const saved = draftValues(indicator);
    let modalDirty = false;

    function draftValues(ind) {
      const draftEntry = (opts.draft && opts.draft.indicators && opts.draft.indicators[ind.id]) || {};
      const points = draftEntry.points != null ? draftEntry.points : ind.points;
      const multiplier = draftEntry.multiplier != null ? draftEntry.multiplier : (ind.formula && ind.formula.multiplier);
      const maxPoints = draftEntry.maxPoints != null ? draftEntry.maxPoints : ind.maxPoints;
      const meta = ((FL.store && FL.store.kraSettings && FL.store.kraSettings.indicatorMeta) || {})[ind.id] || {};
      return {
        name: meta.name || ind.name,
        description: meta.description != null ? meta.description : FL.kraConfig.indicatorDescription(ind),
        pointsLabel: meta.pointsLabel || draftEntry.pointsLabel || ind.pointsLabel || (points == null ? "" : String(points)),
        formulaNote: meta.formulaNote != null ? meta.formulaNote : FL.kraConfig.indicatorFormulaDisplay(ind),
        maxPoints: maxPoints,
        points: points,
        multiplier: multiplier,
        evidenceText: (meta.evidence || ind.evidence || []).join("\n"),
        conditionsText: (meta.conditions || ind.conditions || []).join("\n")
      };
    }

    function snapshotForm(root) {
      return {
        name: root.querySelector("[data-field='name']").value.trim(),
        description: root.querySelector("[data-field='description']").value.trim(),
        pointsLabel: root.querySelector("[data-field='pointsLabel']").value.trim(),
        formulaNote: root.querySelector("[data-field='formulaNote']").value.trim(),
        maxPoints: root.querySelector("[data-field='maxPoints']").value.trim(),
        points: root.querySelector("[data-field='points']") ? root.querySelector("[data-field='points']").value.trim() : "",
        multiplier: root.querySelector("[data-field='multiplier']") ? root.querySelector("[data-field='multiplier']").value.trim() : "",
        evidenceText: root.querySelector("[data-field='evidenceText']").value.trim(),
        conditionsText: root.querySelector("[data-field='conditionsText']").value.trim()
      };
    }

    function initialSnapshot() {
      return JSON.stringify(saved);
    }

    function checkModalDirty(root) {
      modalDirty = JSON.stringify(snapshotForm(root)) !== initialSnapshot();
    }

    const existing = document.getElementById("kra-detail-modal-root");
    if (existing) existing.remove();

    const root = document.createElement("div");
    root.id = "kra-detail-modal-root";
    root.className = "modal-root kra-detail-root";
    root.setAttribute("role", "presentation");

    const isRating = indicator.formula && indicator.formula.type === "rating";
    const pointsField = !isRating && typeof indicator.points === "number"
      ? `<label class="field"><span>Point allocation</span><input class="score-input" type="number" min="0" max="10000" step="0.01" data-field="points" value="${FL.esc(String(saved.points != null ? saved.points : ""))}"></label>`
      : "";
    const multiplierField = isRating
      ? `<label class="field"><span>Rating multiplier</span><input class="score-input" type="number" min="0" max="10000" step="0.01" data-field="multiplier" value="${FL.esc(String(saved.multiplier != null ? saved.multiplier : ""))}"></label>`
      : `<input type="hidden" data-field="multiplier" value="">`;

    const contribution = FL.documents.contributionNote(indicator);
    const contributionLocked = indicator.contribution === "declared" || indicator.contribution === "sole" || indicator.contribution === "fixed";

    root.innerHTML = `
      <div class="kra-detail-modal" role="dialog" aria-modal="true" aria-labelledby="kra-detail-title">
        <header class="kra-detail-head">
          <div>
            <p class="eyebrow">${FL.esc(kra.code)} · ${FL.esc(criterion.name)}</p>
            <h2 id="kra-detail-title">${FL.esc(indicator.name)}</h2>
          </div>
          <button type="button" class="btn btn-ghost btn-small" data-kra-detail-close aria-label="Close">Close</button>
        </header>
        <div class="kra-detail-body">
          <p class="kra-detail-note">${editable
            ? "Edits apply to this institution's saved KRA configuration (local demo storage). Official Annex A defaults remain in rules.js until restored."
            : "Read-only reference from the published KRA configuration."}</p>
          <div class="kra-detail-grid">
            <section class="kra-detail-card">
              <h3><span class="kra-detail-icon" aria-hidden="true">BI</span> Basic information</h3>
              <dl class="facts compact">
                <div><dt>KRA</dt><dd>${FL.esc(kra.code + " — " + kra.name)}</dd></div>
                <div><dt>Criterion</dt><dd>${FL.esc(criterion.name)}</dd></div>
              </dl>
              <label class="field"><span>Indicator title</span>
                <input type="text" data-field="name" value="${FL.esc(saved.name)}" ${editable ? "" : "readonly"}></label>
              <label class="field"><span>Description</span>
                <textarea rows="3" data-field="description" ${editable ? "" : "readonly"}>${FL.esc(saved.description)}</textarea></label>
              <label class="field"><span>Maximum score</span>
                <input class="score-input" type="number" min="0" max="10000" step="0.01" data-field="maxPoints" value="${FL.esc(String(saved.maxPoints))}" ${editable ? "" : "readonly"}></label>
            </section>
            <section class="kra-detail-card">
              <h3><span class="kra-detail-icon" aria-hidden="true">SC</span> Scoring and computation</h3>
              <label class="field"><span>Scoring basis</span>
                <input type="text" data-field="pointsLabel" value="${FL.esc(saved.pointsLabel)}" ${editable ? "" : "readonly"}></label>
              <label class="field"><span>Formula / computation</span>
                <textarea rows="3" data-field="formulaNote" ${editable ? "" : "readonly"}>${FL.esc(saved.formulaNote)}</textarea></label>
              ${pointsField}
              ${multiplierField}
              <div class="kra-readonly-field">
                <span>Contribution allocation</span>
                <p>${FL.esc(contribution)}${contributionLocked ? " (Official contribution rule — read-only)" : ""}</p>
              </div>
            </section>
            <section class="kra-detail-card kra-detail-wide">
              <h3><span class="kra-detail-icon" aria-hidden="true">EV</span> Evidence requirements</h3>
              <p class="sub">One required document or requirement per line.</p>
              <label class="field"><span>Supporting documents</span>
                <textarea rows="6" data-field="evidenceText" ${editable ? "" : "readonly"}>${FL.esc(saved.evidenceText)}</textarea></label>
            </section>
            <section class="kra-detail-card kra-detail-wide">
              <h3><span class="kra-detail-icon" aria-hidden="true">RL</span> Rules and limitations</h3>
              <p class="sub">Official guidelines, restrictions, and special conditions (one per line).</p>
              <label class="field"><span>Conditions</span>
                <textarea rows="6" data-field="conditionsText" ${editable ? "" : "readonly"}>${FL.esc(saved.conditionsText)}</textarea></label>
            </section>
          </div>
        </div>
        <footer class="kra-detail-foot">
          ${editable
            ? `<button type="button" class="btn btn-ghost" data-kra-detail-cancel>Cancel</button>
               <button type="button" class="btn btn-primary" data-kra-detail-save>Save changes</button>`
            : `<button type="button" class="btn btn-primary" data-kra-detail-close>Close</button>`}
        </footer>
      </div>`;

    document.body.appendChild(root);
    requestAnimationFrame(function () { root.classList.add("is-open"); });

    const closeModal = function (force) {
      if (!force && modalDirty && editable) {
        FL.ui.modal({
          title: "Discard edits?",
          body: "<p>You have unsaved changes to this indicator.</p>",
          confirmLabel: "Discard",
          danger: true,
          onConfirm: function () {
            root.classList.remove("is-open");
            setTimeout(function () { root.remove(); }, 180);
            return true;
          }
        });
        return;
      }
      root.classList.remove("is-open");
      setTimeout(function () { root.remove(); }, 180);
    };

    root.querySelectorAll("[data-kra-detail-close], [data-kra-detail-cancel]").forEach(function (btn) {
      btn.addEventListener("click", function () { closeModal(false); });
    });
    root.addEventListener("click", function (event) {
      if (event.target === root) closeModal(false);
    });

    root.querySelectorAll("input, textarea").forEach(function (field) {
      field.addEventListener("input", function () { checkModalDirty(root); });
    });

    if (editable) {
      const saveBtn = root.querySelector("[data-kra-detail-save]");
      saveBtn.addEventListener("click", function () {
        const form = snapshotForm(root);
        if (!form.name) {
          FL.ui.toast("Indicator title is required.", "danger");
          return;
        }
        const maxPoints = Number(form.maxPoints);
        if (!Number.isFinite(maxPoints) || maxPoints < 0 || maxPoints > 10000) {
          FL.ui.toast("Enter a maximum score from 0 through 10000.", "danger");
          return;
        }
        const indicatorPatch = { maxPoints: Math.round(maxPoints * 100) / 100, pointsLabel: form.pointsLabel };
        if (isRating) {
          const mult = Number(form.multiplier);
          if (!Number.isFinite(mult) || mult < 0 || mult > 10000) {
            FL.ui.toast("Enter a valid rating multiplier.", "danger");
            return;
          }
          indicatorPatch.multiplier = Math.round(mult * 100) / 100;
        } else if (typeof indicator.points === "number") {
          const pts = Number(form.points);
          if (!Number.isFinite(pts) || pts < 0 || pts > 10000) {
            FL.ui.toast("Enter valid point allocation.", "danger");
            return;
          }
          indicatorPatch.points = Math.round(pts * 100) / 100;
        }
        const meta = {
          name: form.name,
          description: form.description,
          pointsLabel: form.pointsLabel,
          formulaNote: form.formulaNote,
          evidence: form.evidenceText.split("\n").map(function (line) { return line.trim(); }).filter(Boolean),
          conditions: form.conditionsText.split("\n").map(function (line) { return line.trim(); }).filter(Boolean)
        };
        saveBtn.disabled = true;
        saveBtn.setAttribute("aria-busy", "true");
        saveBtn.innerHTML = "<span class=\"spinner\" aria-hidden=\"true\"></span> Saving…";

        const settings = FL.kraConfig.mergeSettingsPayload(opts.draft, opts.readInputs);
        settings.indicators[indicatorId] = Object.assign(settings.indicators[indicatorId] || {}, indicatorPatch);
        settings.indicatorMeta = settings.indicatorMeta || {};
        settings.indicatorMeta[indicatorId] = meta;

        FL.store.saveKraSettings(settings).then(function () {
          if (opts.session && opts.session.userId) {
            const admin = FL.store.userById(opts.session.userId);
            return FL.audit.record(admin, "Updated KRA indicator", indicatorId, "Saved configuration for " + form.name + ".");
          }
        }).then(function () {
          saveBtn.disabled = false;
          saveBtn.removeAttribute("aria-busy");
          saveBtn.textContent = "Save changes";
          modalDirty = false;
          FL.ui.toast("Indicator configuration saved locally.", "ok");
          if (opts.onSaved) opts.onSaved();
          closeModal(true);
        }).catch(function (error) {
          saveBtn.disabled = false;
          saveBtn.removeAttribute("aria-busy");
          saveBtn.textContent = "Save changes";
          FL.ui.toast(error.message || "Changes were not saved.", "danger");
        });
      });
    }

    document.addEventListener("keydown", function onKey(event) {
      if (event.key === "Escape") {
        document.removeEventListener("keydown", onKey);
        closeModal(false);
      }
    });
  },

  showIndicatorDetail: function (indicatorId, options) {
    FL.kraConfig.openIndicatorEditor(indicatorId, Object.assign({ editable: false }, options || {}));
  },

  /** Normalize score override maps for stable dirty-state comparison (numbers, 2 decimal places). */
  normalizeSettings: function (raw) {
    const copy = JSON.parse(JSON.stringify(raw || {}));
    ["kras", "criteria", "indicators"].forEach(function (bucket) {
      if (!copy[bucket]) copy[bucket] = {};
      Object.keys(copy[bucket]).forEach(function (id) {
        const row = copy[bucket][id];
        if (!row || typeof row !== "object") return;
        Object.keys(row).forEach(function (field) {
          const rawValue = row[field];
          const text = String(rawValue == null ? "" : rawValue).trim();
          if (text === "") {
            delete row[field];
            return;
          }
          const number = Number(text);
          if (Number.isFinite(number)) row[field] = Math.round(number * 100) / 100;
        });
      });
    });
    return copy;
  },

  settingsFingerprint: function (settings) {
    const norm = FL.kraConfig.normalizeSettings(settings);
    norm.indicatorMeta = (settings && settings.indicatorMeta)
      ? JSON.parse(JSON.stringify(settings.indicatorMeta))
      : {};
    return JSON.stringify(norm);
  },

  mount: function (page, session, view) {
    const editable = !(view && view.readonly);
    const draft = FL.rules.scoreDraft();
    let activeKra = FL.rules.kras[0].id;
    const openCriteria = {};
    const criterionTab = {};
    let highlightIndicator = "";
    let savedSnapshot = FL.kraConfig.settingsFingerprint(FL.kraConfig.mergeSettingsPayload(draft, null));
    let dirty = false;
    let beforeUnloadBound = false;
    let navGuardBound = false;

    if (FL.rules.kras[0].criteria[0]) openCriteria[FL.rules.kras[0].criteria[0].id] = true;

    const status = FL.kraConfig.configStatusLabel(editable);

    page.innerHTML = `
      <div class="page-head"><div>
        <p class="eyebrow">${FL.esc(FL.rules.citation)}</p>
        <h1>${editable ? "KRA Configuration" : "Official KRA Scoring Reference"}</h1>
        ${editable ? "<p class=\"lede\">Review and adjust Annex A point values used by FacultyLink scoring. Criteria, indicators, and evidence text remain official.</p>"
          : "<p class=\"lede\">These are the scores published from KRA Configuration. Reviewers can read them and cannot change them.</p>"}
      </div></div>
      <div class="kra-persist-note callout">${FL.esc(FL.kraConfig.persistenceNote())}</div>
      <details class="callout kra-source"><summary>Rule source</summary>
        <p>${editable
          ? "Scores start from " + FL.esc(FL.rules.annex) + " and can be changed here. Saved scores are what FacultyLink uses. " + FL.esc(FL.scoring.formula)
          : "Published from " + FL.esc(FL.rules.annex) + ". " + FL.esc(FL.scoring.formula)}</p>
        <p>${FL.rules.globalConditions.map(FL.esc).join(" ")}</p>
      </details>
      <div class="kra-config-shell">
        <div class="kra-toolbar-sticky">
          <label class="search kra-search"><span class="sr-only">Search rules</span>
            <input id="rule-search" type="search" placeholder="Search KRA, criterion, indicator, or evidence" autocomplete="off">
          </label>
          <div id="kra-search-results" class="kra-search-results" hidden></div>
          ${editable ? `
            <div class="kra-action-bar">
              <button class="btn btn-primary" id="save-scores" type="button">Save scores</button>
              <button class="btn btn-ghost" id="reset-scores" type="button">Restore official scores</button>
              <span id="kra-unsaved" class="kra-unsaved" hidden>Unsaved changes</span>
            </div>` : ""}
          <div id="kra-nav" class="kra-nav" role="tablist" aria-label="Key Result Areas"></div>
        </div>
        <p id="score-error" class="form-error" hidden></p>
        <div id="rule-list"></div>
      </div>`;

    const scoreInput = function (kind, id, field, value) {
      return `<input class="score-input" type="number" min="0" max="10000" step="0.01" inputmode="decimal" data-kind="${kind}" data-id="${FL.esc(id)}" data-field="${field}" value="${FL.esc(value)}" aria-label="${FL.esc(field)}">`;
    };

    const readInputs = function () {
      document.querySelectorAll(".score-input").forEach(function (input) {
        const bucket = draft[input.dataset.kind];
        const id = input.dataset.id;
        if (!bucket || !bucket[id]) return;
        bucket[id][input.dataset.field] = input.value;
      });
    };

    const syncDirtyState = function () {
      readInputs();
      dirty = FL.kraConfig.settingsFingerprint(FL.kraConfig.mergeSettingsPayload(draft, null)) !== savedSnapshot;
      const mark = document.getElementById("kra-unsaved");
      if (mark) mark.hidden = !dirty;
    };

    const bindLeaveGuards = function () {
      if (!editable) return;
      if (!beforeUnloadBound) {
        beforeUnloadBound = true;
        window.addEventListener("beforeunload", function (event) {
          syncDirtyState();
          if (!dirty) return;
          event.preventDefault();
          event.returnValue = "";
        });
      }
      if (navGuardBound) return;
      navGuardBound = true;
      document.querySelectorAll("#app .side-nav a[href]").forEach(function (link) {
        link.addEventListener("click", function (event) {
          const href = link.getAttribute("href");
          if (!href || href.charAt(0) === "#") return;
          syncDirtyState();
          if (!dirty) return;
          event.preventDefault();
          FL.ui.modal({
            title: "Unsaved changes",
            body: "<p>You have unsaved score changes. Leave KRA Configuration without saving?</p>",
            confirmLabel: "Leave without saving",
            cancelLabel: "Stay on page",
            danger: true,
            onConfirm: function () {
              dirty = false;
              window.location.href = href;
            }
          });
        });
      });
    };

    const detailText = function (indicator) {
      const conditions = (indicator.conditions || []).slice();
      const note = FL.documents.contributionNote(indicator);
      if (note) conditions.unshift(note);
      return {
        evidence: (indicator.evidence || []).join("; "),
        conditions: conditions.join(" ")
      };
    };

    const matchesQuery = function (kra, criterion, indicator, query) {
      if (!query) return true;
      const detail = detailText(indicator);
      return [kra.name, kra.code, kra.summary, criterion.name, criterion.description || "", indicator.name, detail.evidence, detail.conditions]
        .join(" ")
        .toLowerCase()
        .indexOf(query) !== -1;
    };

    const evidenceMatch = function (indicator, query) {
      if (!query) return false;
      const detail = detailText(indicator);
      return detail.evidence.toLowerCase().indexOf(query) !== -1;
    };

    const buildSearchResults = function (query) {
      const results = [];
      FL.rules.kras.forEach(function (kra) {
        kra.criteria.forEach(function (criterion) {
          criterion.indicators.forEach(function (indicator) {
            if (!matchesQuery(kra, criterion, indicator, query)) return;
            const detail = detailText(indicator);
            const viaEvidence = evidenceMatch(indicator, query) && query.length > 1;
            results.push({
              kraId: kra.id,
              kraCode: kra.code,
              criterionId: criterion.id,
              criterionName: criterion.name,
              indicatorId: indicator.id,
              indicatorName: indicator.name,
              snippet: viaEvidence ? detail.evidence : indicator.name,
              tab: viaEvidence ? "evidence" : "indicators"
            });
          });
        });
      });
      return results.slice(0, 12);
    };

    const renderSearchResults = function (query) {
      const host = document.getElementById("kra-search-results");
      if (!host) return;
      if (!query || query.length < 2) {
        host.hidden = true;
        host.innerHTML = "";
        return;
      }
      const results = buildSearchResults(query);
      if (!results.length) {
        host.hidden = false;
        host.innerHTML = FL.ui.empty("No matches", "Try another KRA, criterion, indicator, or evidence keyword.");
        return;
      }
      host.hidden = false;
      host.innerHTML = `
        <p class="kra-search-label">${results.length} result${results.length === 1 ? "" : "s"}</p>
        <ul class="kra-search-list">
          ${results.map(function (item, index) {
            return `<li><button type="button" class="kra-search-hit" data-search-index="${index}">
              <strong>${FL.esc(item.kraCode)}</strong>
              <span>${FL.esc(item.criterionName)}</span>
              <small>${FL.esc(item.snippet)}</small>
            </button></li>`;
          }).join("")}
        </ul>`;
      host.querySelectorAll(".kra-search-hit").forEach(function (button) {
        button.addEventListener("click", function () {
          const item = results[Number(button.getAttribute("data-search-index"))];
          jumpTo(item);
          host.hidden = true;
        });
      });
    };

    const jumpTo = function (item) {
      activeKra = item.kraId;
      Object.keys(openCriteria).forEach(function (key) { openCriteria[key] = false; });
      openCriteria[item.criterionId] = true;
      criterionTab[item.criterionId] = item.tab || "indicators";
      highlightIndicator = item.indicatorId || "";
      draw({ scrollTo: "fold-" + item.criterionId });
    };

    const evidenceTabHtml = function (criterion, indicators) {
      const blocks = indicators.map(function (indicator) {
        const items = indicator.evidence || [];
        const body = items.length
          ? "<ul class=\"plain\">" + items.map(function (entry) {
            return "<li>" + FL.esc(entry) + "</li>";
          }).join("") + "</ul>"
          : "<p class=\"sub\">Not configured in the official rule set.</p>";
        return `<article class="kra-evidence-block">
          <h4>${FL.esc(indicator.name)}</h4>
          ${body}
        </article>`;
      }).join("");
      return blocks || FL.ui.empty("No indicators", "This criterion has no indicators in the official configuration.");
    };

    const indicatorRowHtml = function (kra, criterion, indicator, editableMode) {
      const saved = draft.indicators[indicator.id];
      let pointsCell = FL.esc(indicator.pointsLabel || (indicator.points == null ? "—" : String(indicator.points)));
      let maxCell = FL.esc(String(indicator.maxPoints));
      if (editableMode && saved && saved.multiplier !== undefined) {
        pointsCell = `<span class="score-formula">Rating ÷ 100 × ${scoreInput("indicators", indicator.id, "multiplier", saved.multiplier)}</span>`;
      } else if (editableMode && saved && saved.points !== undefined) {
        pointsCell = scoreInput("indicators", indicator.id, "points", saved.points);
      }
      if (editableMode && saved) maxCell = scoreInput("indicators", indicator.id, "maxPoints", saved.maxPoints);
      const formula = FL.kraConfig.indicatorFormulaDisplay(indicator);
      const highlight = highlightIndicator === indicator.id ? " is-highlight" : "";
      return `<article class="kra-indicator-row${highlight}" data-indicator-row="${FL.esc(indicator.id)}">
        <div class="kra-indicator-main">
          <p class="kra-indicator-title">${FL.esc(indicator.name)}</p>
          <p class="kra-indicator-formula">${FL.esc(formula)}</p>
        </div>
        <div class="kra-indicator-fields">
          <label class="score-cap"><span>Points</span>${pointsCell}</label>
          <label class="score-cap"><span>Maximum</span>${maxCell}</label>
          <button class="btn btn-small btn-ghost" type="button" data-indicator-detail="${FL.esc(indicator.id)}">Details</button>
        </div>
      </article>`;
    };

    const draw = function (options) {
      readInputs();
      const query = (document.getElementById("rule-search").value || "").trim().toLowerCase();
      renderSearchResults(query);
      const scrollY = window.scrollY;

      const groups = FL.rules.kras.map(function (kra) {
        const criteria = kra.criteria.map(function (criterion) {
          return {
            criterion: criterion,
            indicators: criterion.indicators.filter(function (indicator) {
              return matchesQuery(kra, criterion, indicator, query);
            })
          };
        }).filter(function (group) { return group.indicators.length; });
        return { kra: kra, criteria: criteria };
      });

      const visible = groups.filter(function (group) { return group.criteria.length; });
      if (query && visible.length && !visible.some(function (group) { return group.kra.id === activeKra; })) {
        activeKra = visible[0].kra.id;
      }

      const nav = FL.rules.kras.map(function (kra) {
        const selected = kra.id === activeKra;
        const matchCount = (groups.find(function (group) { return group.kra.id === kra.id; }) || { criteria: [] })
          .criteria.reduce(function (sum, group) { return sum + group.indicators.length; }, 0);
        const icon = FL.kraConfig.icons[kra.id] || "";
        return `<button class="kra-nav-card${selected ? " is-active" : ""}" type="button" role="tab"
          id="tab-${FL.esc(kra.id)}" aria-selected="${selected ? "true" : "false"}"
          aria-controls="panel-${FL.esc(kra.id)}" data-kra-tab="${FL.esc(kra.id)}">
          <span class="kra-nav-icon">${icon}</span>
          <span class="kra-nav-text">
            <strong>${FL.esc(kra.code)}</strong>
            <small>${FL.esc(kra.name)}</small>
            <span class="kra-nav-meta">Max ${FL.esc(String(kra.maxPoints))}${query ? " · " + matchCount + " match" + (matchCount === 1 ? "" : "es") : ""}</span>
          </span>
        </button>`;
      }).join("");
      document.getElementById("kra-nav").innerHTML = nav;

      const panels = groups.map(function (group) {
        const kra = group.kra;
        const hidden = kra.id !== activeKra;
        const kraStatus = kra.id === activeKra ? status : null;
        const folds = group.criteria.map(function (item, index) {
          const criterion = item.criterion;
          const needsEvidence = query && item.indicators.some(function (indicator) { return evidenceMatch(indicator, query); });
          const stored = openCriteria[criterion.id];
          const opened = stored === true || (stored !== false && !!query && (index === 0 && kra.id === activeKra || needsEvidence));
          const tab = criterionTab[criterion.id] || "indicators";
          const indicatorCount = criterion.indicators.length;
          const maxLabel = criterion.bonus ? "Bonus maximum" : "Maximum";
          return `<article class="kra-fold${opened ? " is-open" : ""}">
            <header class="kra-fold-head">
              <button class="kra-toggle" type="button" data-toggle-criterion="${FL.esc(criterion.id)}"
                aria-expanded="${opened ? "true" : "false"}" aria-controls="fold-${FL.esc(criterion.id)}">
                <span class="kra-chevron" aria-hidden="true"></span>
                <span class="kra-fold-titles">
                  <span class="kra-fold-name">${FL.esc(criterion.name)}</span>
                  <span class="kra-fold-desc">${FL.esc(criterion.description || kra.summary)}</span>
                </span>
                <span class="kra-fold-meta">${indicatorCount} indicator${indicatorCount === 1 ? "" : "s"}</span>
              </button>
              <label class="score-cap kra-fold-cap">${maxLabel}
                ${editable ? scoreInput("criteria", criterion.id, "maxPoints", draft.criteria[criterion.id].maxPoints)
                  : "<strong>" + FL.esc(String(criterion.maxPoints)) + "</strong>"}
              </label>
            </header>
            <div class="kra-fold-body" id="fold-${FL.esc(criterion.id)}" ${opened ? "" : "hidden"}>
              <div class="kra-subtabs" role="tablist">
                <button type="button" class="kra-subtab${tab === "indicators" ? " is-active" : ""}" data-criterion-tab="${FL.esc(criterion.id)}" data-tab="indicators">Indicators</button>
                <button type="button" class="kra-subtab${tab === "evidence" ? " is-active" : ""}" data-criterion-tab="${FL.esc(criterion.id)}" data-tab="evidence">Evidence requirements</button>
              </div>
              <div class="kra-subpanel" ${tab === "indicators" ? "" : "hidden"} data-criterion-panel="${FL.esc(criterion.id)}" data-panel="indicators">
                ${item.indicators.map(function (indicator) {
                  return indicatorRowHtml(kra, criterion, indicator, editable);
                }).join("") || FL.ui.empty("No indicators", "No indicator matches this search.")}
              </div>
              <div class="kra-subpanel" ${tab === "evidence" ? "" : "hidden"} data-criterion-panel="${FL.esc(criterion.id)}" data-panel="evidence">
                ${evidenceTabHtml(criterion, item.indicators)}
              </div>
            </div>
          </article>`;
        }).join("");

        return `<section class="kra-panel card" role="tabpanel" id="panel-${FL.esc(kra.id)}" aria-labelledby="tab-${FL.esc(kra.id)}" ${hidden ? "hidden" : ""}>
          <header class="kra-banner">
            <div>
              <h2>${FL.esc(kra.code)} — ${FL.esc(kra.name)}</h2>
              <p class="sub">${FL.esc(kra.summary)}</p>
            </div>
            <div class="kra-banner-aside">
              ${kraStatus ? FL.ui.badge(kraStatus.kind, kraStatus.text) : ""}
              <label class="score-cap">KRA maximum
                ${editable ? scoreInput("kras", kra.id, "maxPoints", draft.kras[kra.id].maxPoints)
                  : "<strong>" + FL.esc(String(kra.maxPoints)) + "</strong>"}
              </label>
            </div>
          </header>
          ${folds || FL.ui.empty("No rules", "No indicator in this KRA matches the search.")}
        </section>`;
      }).join("");

      const host = document.getElementById("rule-list");
      host.innerHTML = visible.length ? panels : FL.ui.empty("No rules", "No indicator matches this search.");

      document.querySelectorAll("[data-kra-tab]").forEach(function (button) {
        button.addEventListener("click", function () {
          const target = button.getAttribute("data-kra-tab");
          if (target === activeKra) return;
          readInputs();
          activeKra = target;
          highlightIndicator = "";
          draw({ align: "banner" });
        });
      });

      host.querySelectorAll("[data-toggle-criterion]").forEach(function (button) {
        button.addEventListener("click", function () {
          const id = button.getAttribute("data-toggle-criterion");
          const expand = button.getAttribute("aria-expanded") !== "true";
          if (expand) {
            Object.keys(openCriteria).forEach(function (key) {
              if (key !== id) openCriteria[key] = false;
            });
          }
          openCriteria[id] = expand;
          draw();
        });
      });

      host.querySelectorAll("[data-criterion-tab]").forEach(function (button) {
        button.addEventListener("click", function () {
          criterionTab[button.getAttribute("data-criterion-tab")] = button.getAttribute("data-tab");
          draw();
        });
      });

      host.querySelectorAll("[data-indicator-detail]").forEach(function (button) {
        button.addEventListener("click", function () {
          FL.kraConfig.openIndicatorEditor(button.getAttribute("data-indicator-detail"), {
            editable: editable,
            draft: draft,
            readInputs: readInputs,
            session: session,
            onSaved: function () {
              const fresh = FL.rules.scoreDraft();
              draft.kras = fresh.kras;
              draft.criteria = fresh.criteria;
              draft.indicators = fresh.indicators;
              savedSnapshot = FL.kraConfig.settingsFingerprint(
                FL.kraConfig.mergeSettingsPayload(draft, readInputs)
              );
              dirty = false;
              const mark = document.getElementById("kra-unsaved");
              if (mark) mark.hidden = true;
              draw();
            }
          });
        });
      });

      document.querySelectorAll(".score-input").forEach(function (input) {
        input.addEventListener("input", syncDirtyState);
        input.addEventListener("change", syncDirtyState);
      });

      syncDirtyState();

      const scrollTarget = options && options.scrollTo;
      if (scrollTarget) {
        const el = document.getElementById(scrollTarget);
        if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
        if (highlightIndicator) {
          setTimeout(function () {
            const row = document.querySelector("[data-indicator-row=\"" + highlightIndicator + "\"]");
            if (row) {
              row.classList.add("is-highlight");
              row.scrollIntoView({ behavior: "smooth", block: "nearest" });
            }
          }, 120);
        }
      } else if (options && options.align === "banner") {
        const tools = document.querySelector(".kra-toolbar-sticky");
        const banner = document.querySelector(".kra-panel:not([hidden]) .kra-banner");
        if (tools && banner) {
          const delta = banner.getBoundingClientRect().top - tools.getBoundingClientRect().bottom - 8;
          window.scrollTo({ top: Math.max(0, window.scrollY + delta), behavior: "auto" });
        }
      } else {
        window.scrollTo({ top: scrollY, behavior: "auto" });
      }
    };

    const showError = function (message) {
      const error = document.getElementById("score-error");
      error.hidden = !message;
      error.textContent = message || "";
    };

    const numericDraft = function () {
      readInputs();
      const copy = FL.kraConfig.normalizeSettings(draft);
      let invalid = false;
      ["kras", "criteria", "indicators"].forEach(function (bucket) {
        Object.keys(copy[bucket] || {}).forEach(function (id) {
          Object.keys(copy[bucket][id] || {}).forEach(function (field) {
            const value = copy[bucket][id][field];
            if (value == null || !Number.isFinite(value) || value < 0 || value > 10000) invalid = true;
          });
        });
      });
      if (!invalid && FL.store && FL.store.kraSettings && FL.store.kraSettings.indicatorMeta) {
        copy.indicatorMeta = JSON.parse(JSON.stringify(FL.store.kraSettings.indicatorMeta));
      }
      return invalid ? null : copy;
    };

    document.getElementById("rule-search").addEventListener("input", function () {
      highlightIndicator = "";
      draw();
    });

    if (!editable) {
      draw();
      return;
    }

    document.getElementById("save-scores").addEventListener("click", function () {
      const settings = numericDraft();
      if (!settings) {
        showError("Enter scores from 0 through 10000.");
        return;
      }
      showError("");
      const button = document.getElementById("save-scores");
      const idle = button.textContent;
      button.disabled = true;
      button.setAttribute("aria-busy", "true");
      button.innerHTML = "<span class=\"spinner\" aria-hidden=\"true\"></span> Saving…";
      FL.store.saveKraSettings(settings).then(function () {
        const user = FL.store.userById(session.userId);
        return FL.audit.record(user, "Updated KRA scores", "KRA", "Saved KRA configuration scores.");
      }).then(function () {
        savedSnapshot = FL.kraConfig.settingsFingerprint(settings);
        Object.assign(draft.kras, settings.kras);
        Object.assign(draft.criteria, settings.criteria);
        Object.assign(draft.indicators, settings.indicators);
        dirty = false;
        const mark = document.getElementById("kra-unsaved");
        if (mark) mark.hidden = true;
        button.disabled = false;
        button.removeAttribute("aria-busy");
        button.textContent = idle;
        FL.ui.toast("Scores saved to local configuration.", "ok");
        draw();
      }).catch(function (error) {
        button.disabled = false;
        button.removeAttribute("aria-busy");
        button.textContent = idle;
        showError(error.message || "Scores were not saved.");
      });
    });

    document.getElementById("reset-scores").addEventListener("click", function () {
      FL.ui.modal({
        title: "Restore official scores",
        body: "<p>This replaces saved score overrides and locally edited indicator text with the official DBM–CHED Joint Circular No. 01, s. 2026 Annex A values in rules.js.</p><p>Official criteria structure and contribution rules are unchanged.</p>",
        confirmLabel: "Restore official scores",
        onConfirm: function () {
          return FL.store.saveKraSettings({ kras: {}, criteria: {}, indicators: {}, indicatorMeta: {} }).then(function () {
            const fresh = FL.rules.scoreDraft();
            draft.kras = fresh.kras;
            draft.criteria = fresh.criteria;
            draft.indicators = fresh.indicators;
            savedSnapshot = FL.kraConfig.settingsFingerprint(fresh);
            dirty = false;
            const mark = document.getElementById("kra-unsaved");
            if (mark) mark.hidden = true;
            showError("");
            draw();
            FL.ui.toast("Official scores restored.", "ok");
            return true;
          }).catch(function (error) {
            showError(error.message || "Official scores were not restored.");
            return false;
          });
        }
      });
    });

    bindLeaveGuards();
    draw();
  }
};
