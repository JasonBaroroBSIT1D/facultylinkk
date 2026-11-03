/**
 * Applicable published scoring configuration (Phase C5 / C7).
 * Backend is authoritative; this module is display and reference only.
 */
window.FL = window.FL || {};

FL.scoringConfiguration = {
  CACHE_MS: 10 * 60 * 1000,
  CRITERION_C_ID: "kra1-c",
  CRITERION_C_SERVICE_INDICATORS: [
    "kra1-c-adviser-sp",
    "kra1-c-panel-sp",
    "kra1-c-adviser-ut",
    "kra1-c-panel-ut",
    "kra1-c-adviser-mt",
    "kra1-c-panel-mt",
    "kra1-c-adviser-dd",
    "kra1-c-panel-dd",
    "kra1-c-mentor"
  ],

  _state: {
    loadedAt: 0,
    configuration: null,
    kraSettings: null,
    metadata: null,
    rankWeightsPolicy: null,
    message: null,
    error: null
  },
  _inFlight: null,
  _historicalCache: {},

  _canUseLiveApi: function () {
    const store = FL.store;
    if (!store) return false;
    return !!(store.usesLiveReviewerApi && store.usesLiveReviewerApi())
      || !!(store.usesRealAdminApi && store.usesRealAdminApi());
  },

  normalizePayload: function (raw, source) {
    const data = raw || {};
    if (source === "reviewer") {
      return {
        configuration: data.published || data.configuration || null,
        kraSettings: data.kraSettings || {},
        metadata: data.metadata || {},
        rankWeightsPolicy: data.rankWeightsPolicy || null,
        message: data.message || null
      };
    }
    return {
      configuration: data.configuration || null,
      kraSettings: data.kraSettings || {},
      metadata: data.metadata || {},
      rankWeightsPolicy: data.rankWeightsPolicy || null,
      message: data.message || null
    };
  },

  hasApplicable: function () {
    return !!(this._state.configuration && this._state.configuration.id != null);
  },

  kraSettings: function () {
    return this._state.kraSettings || (FL.store && FL.store.kraSettings) || {};
  },

  indicatorPoints: function (indicatorId, kraSettings) {
    const ks = kraSettings || this.kraSettings();
    const row = ks.indicators && ks.indicators[indicatorId];
    if (!row || row.points == null) return null;
    const num = Number(row.points);
    return Number.isFinite(num) ? num : null;
  },

  criterionMax: function (criterionId, kraSettings) {
    const ks = kraSettings || this.kraSettings();
    const row = ks.criteria && ks.criteria[criterionId];
    if (!row || row.maxPoints == null) return null;
    const num = Number(row.maxPoints);
    return Number.isFinite(num) ? num : null;
  },

  kraMax: function (kraId, kraSettings) {
    const ks = kraSettings || this.kraSettings();
    const row = ks.kras && ks.kras[kraId];
    if (!row || row.maxPoints == null) return null;
    const num = Number(row.maxPoints);
    return Number.isFinite(num) ? num : null;
  },

  criterionLabel: function (criterionId, kraSettings) {
    const ks = kraSettings || this.kraSettings();
    const row = ks.criteria && ks.criteria[criterionId];
    return row && row.name ? String(row.name) : null;
  },

  criterionCMax: function (kraSettings) {
    return this.criterionMax(this.CRITERION_C_ID, kraSettings);
  },

  criterionCIndicatorsComplete: function (kraSettings) {
    const ks = kraSettings || this.kraSettings();
    if (this.criterionCMax(ks) == null) return false;
    const self = this;
    return this.CRITERION_C_SERVICE_INDICATORS.every(function (id) {
      return self.indicatorPoints(id, ks) != null;
    });
  },

  applyToStore: function (payload) {
    const store = FL.store;
    if (!store || !payload) return;
    if (payload.kraSettings && FL.rules && FL.rules.applySettings) {
      store.kraSettings = payload.kraSettings;
      FL.rules.applySettings(payload.kraSettings);
    }
    store.scoringConfiguration = payload.configuration || null;
    store.scoringConfigurationMetadata = payload.metadata || null;
    store.scoringConfigurationMessage = payload.message || null;
    store.scoringConfigurationRankWeightsPolicy = payload.rankWeightsPolicy || null;
    if (payload.configuration) {
      store.kraConfigurationPublished = payload.configuration;
    }
  },

  clear: function () {
    this._state.loadedAt = 0;
    this._state.configuration = null;
    this._state.kraSettings = null;
    this._state.metadata = null;
    this._state.rankWeightsPolicy = null;
    this._state.message = null;
    this._state.error = null;
    this._historicalCache = {};
    if (FL.store) {
      FL.store.scoringConfiguration = null;
      FL.store.scoringConfigurationMetadata = null;
    }
  },

  refresh: function (options) {
    const opts = options || {};
    const self = this;
    if (!this._canUseLiveApi()) {
      return Promise.resolve(null);
    }
    const force = !!opts.force;
    const now = Date.now();
    if (!force && self._state.loadedAt && (now - self._state.loadedAt) < self.CACHE_MS) {
      return Promise.resolve(self._state);
    }
    if (self._inFlight) return self._inFlight;

    const source = opts.source === "applicable" ? "applicable" : "reviewer";
    let path = source === "applicable"
      ? "/api/scoring-configuration/applicable"
      : "/api/reviewer/kra-configuration";
    if (opts.asOf) {
      path += (path.indexOf("?") >= 0 ? "&" : "?") + "asOf=" + encodeURIComponent(opts.asOf);
    }
    if (opts.configurationId != null) {
      path += (path.indexOf("?") >= 0 ? "&" : "?") + "configurationId=" + encodeURIComponent(String(opts.configurationId));
    }

    self._inFlight = FL.apiClient.adminRequest("GET", path).then(function (data) {
      const payload = self.normalizePayload(data, source);
      self._state.configuration = payload.configuration;
      self._state.kraSettings = payload.kraSettings;
      self._state.metadata = payload.metadata || {};
      self._state.rankWeightsPolicy = payload.rankWeightsPolicy;
      self._state.message = payload.message;
      self._state.error = null;
      self._state.loadedAt = Date.now();
      if (!opts.skipStoreApply) {
        self.applyToStore(payload);
      }
      return self._state;
    }).catch(function (err) {
      self._state.error = err.message || "Configuration unavailable";
      throw err;
    }).finally(function () {
      self._inFlight = null;
    });
    return self._inFlight;
  },

  fetchByConfigurationId: function (configurationId) {
    const key = String(configurationId);
    if (this._historicalCache[key]) {
      return Promise.resolve(this._historicalCache[key]);
    }
    const self = this;
    if (!this._canUseLiveApi()) {
      return Promise.resolve(null);
    }
    const path = "/api/scoring-configuration/applicable?configurationId=" + encodeURIComponent(key);
    return FL.apiClient.adminRequest("GET", path).then(function (data) {
      const payload = self.normalizePayload(data, "applicable");
      self._historicalCache[key] = payload;
      return payload;
    });
  },

  versionLabel: function (metadata) {
    const meta = metadata || this._state.metadata || {};
    if (meta.version != null) return "v" + String(meta.version);
    if (meta.configurationId != null) return "id " + String(meta.configurationId);
    return "—";
  },

  bannerHtml: function (options) {
    const opts = options || {};
    const esc = FL.esc;
    if (!this._canUseLiveApi()) return "";
    if (this._state.error) {
      return `<p class="note scoring-config-banner scoring-config-banner--warn">${esc("Official scoring configuration could not be loaded. Point references may be unavailable until you refresh.")}</p>`;
    }
    if (!this.hasApplicable()) {
      const msg = this._state.message || "No applicable official scoring configuration.";
      return `<p class="note scoring-config-banner scoring-config-banner--warn">${esc(msg)}</p>`;
    }
    const meta = this._state.metadata || {};
    const cfg = this._state.configuration || {};
    const guideline = cfg.guidelineLabel || meta.guidelineLabel || "";
    const parts = [
      "Applicable scoring " + this.versionLabel(meta),
      meta.effectiveFrom ? "effective " + meta.effectiveFrom : ""
    ].filter(Boolean);
    if (!opts.compact && guideline) parts.push(guideline);
    return `<p class="note scoring-config-banner">${esc(parts.join(" · "))}</p>`;
  },

  lockedSnapshotLabel: function (snapshot) {
    if (!snapshot || typeof snapshot !== "object") {
      return "Historical scoring version unknown (legacy record).";
    }
    const parts = ["Locked scoring configuration"];
    if (snapshot.version != null) parts.push("v" + String(snapshot.version));
    if (snapshot.effectiveFrom) parts.push("effective " + snapshot.effectiveFrom);
    if (snapshot.provenance) parts.push("(" + String(snapshot.provenance).replace(/_/g, " ") + ")");
    parts.push("— finalized assessments use this version, not the currently applicable config.");
    return parts.join(" ");
  },

  /** @deprecated Reviewer Web no longer renders the full Criterion C comparison table; use per-accomplishment context instead. */
  criterionCReferenceTableHtml: function (kraSettings) {
    const esc = FL.esc;
    const ks = kraSettings || this.kraSettings();
    const ui = FL.criterionCWorkspaceUi;
    const rows = (ui && ui.RESEARCH_TYPE_LABELS) ? Object.keys(ui.RESEARCH_TYPE_LABELS) : [];
    const typeToIndicators = {
      sp_cp: ["kra1-c-adviser-sp", "kra1-c-panel-sp"],
      ut: ["kra1-c-adviser-ut", "kra1-c-panel-ut"],
      mt: ["kra1-c-adviser-mt", "kra1-c-panel-mt"],
      dd: ["kra1-c-adviser-dd", "kra1-c-panel-dd"]
    };
    const body = rows.map(function (rt) {
      const ids = typeToIndicators[rt] || [];
      const adv = ids[0] ? this.indicatorPoints(ids[0], ks) : null;
      const pan = ids[1] ? this.indicatorPoints(ids[1], ks) : null;
      const label = ui.RESEARCH_TYPE_LABELS[rt] || rt;
      return `<tr><td>${esc(label)}</td><td>${adv != null ? esc(String(adv)) : "—"}</td><td>${pan != null ? esc(String(pan)) : "—"}</td></tr>`;
    }.bind(this)).join("");
    const mentor = this.indicatorPoints("kra1-c-mentor", ks);
    const cap = this.criterionCMax(ks);
    return `<section class="card cc-annex-reference">
      <h3>Published Criterion C point reference</h3>
      <p class="note">Display only — reviewer-assessed points are saved by the backend.</p>
      <table class="data"><thead><tr><th>Service</th><th>Adviser</th><th>Panel</th></tr></thead><tbody>
        ${body}
        <tr><td>Mentorship (per eligible service)</td><td>${mentor != null ? esc(String(mentor)) : "—"}</td><td>—</td></tr>
      </tbody></table>
      <p class="note"><strong>Criterion C maximum:</strong> ${cap != null ? esc(String(cap)) + " points" : "—"}</p>
    </section>`;
  }
};
