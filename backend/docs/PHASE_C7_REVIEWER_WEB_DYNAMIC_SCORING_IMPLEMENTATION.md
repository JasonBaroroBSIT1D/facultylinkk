# Phase C7 — Reviewer Web Dynamic Scoring Configuration Integration

**Date:** 2026-11-03  
**Scope:** Reviewer Web (static JS under `web/`) only. No Flask formula changes, no Faculty Mobile changes, no Admin publish UI changes.

---

## 1. Executive Summary

Phase C7 connects the Reviewer Web to the Phase C5 applicable published scoring configuration. A shared **`FL.scoringConfiguration`** loader fetches `GET /api/reviewer/kra-configuration` (and supports `GET /api/scoring-configuration/applicable` with `configurationId` / `asOf` for historical reference). Parsed settings are applied to **`FL.rules`** for read-only display while **reviewer-assessed points, estimates, and approvals remain backend-authoritative**.

Criterion C accomplishment lists, review workspace, and reference tables now show **published indicator points and caps**. Locked `bundle.scoringConfiguration` snapshots are shown distinctly from the **currently applicable** configuration banner. Official KRA Scoring Reference (`kra-reference.html`) continues to use the same loader via `loadPublishedKraConfiguration()`.

---

## 2. Files Modified

| Path | Change |
|---|---|
| `web/js/scoring-configuration.js` | **New** — central loader, cache, historical fetch, Criterion C reference table |
| `web/js/data.js` | Reviewer publish load delegates to loader; `refreshScoringConfiguration()` |
| `web/js/criterion-c-workspace-ui.js` | Dynamic points/cap; config banner on summary |
| `web/js/criterion-c-review.js` | Locked version display; published reference; review panel |
| `web/js/evidence-workspace.js` | Config refresh on mount; criterion max labels |
| `web/js/main.js` | Prefetch scoring config on reviewer/admin boot |
| `web/js/kra-config.js` | Publish banner uses `scoringConfigurationMetadata` |
| `web/js/auth.js` | Clear scoring cache on logout |
| `web/tests/scoring-configuration.test.js` | **New** — Node unit checks |
| `web/pages/**/*.html` | Include `scoring-configuration.js` before `data.js` |
| `backend/tests/kra_configuration/test_reviewer_scoring_api.py` | **New** — mocked read API payload tests |

---

## 3. API Integration

| Endpoint | Role |
|---|---|
| `GET /api/reviewer/kra-configuration` | Primary reviewer fetch (`published`, `kraSettings`, `metadata`, `rankWeightsPolicy`) |
| `GET /api/scoring-configuration/applicable?configurationId=` | Historical locked configuration for accomplishment review (does not replace global applicable cache) |
| `GET /api/scoring-configuration/applicable?asOf=` | Supported by loader for future dated reference |

Contracts match Phase C5 (`configuration` / `published` header, `kraSettings`, `metadata`, `rankWeightsPolicy`).

---

## 4. Central Configuration Loader

**Module:** `FL.scoringConfiguration`

- **Cache:** 10 minutes; bypass with `{ force: true }`.
- **Dedup:** Single in-flight request shared across callers.
- **Store sync:** Updates `FL.store.kraSettings`, applies `FL.rules.applySettings`, stores `scoringConfigurationMetadata`.
- **Helpers:** `indicatorPoints`, `criterionMax`, `kraMax`, `criterionCMax`, `bannerHtml`, `lockedSnapshotLabel`, `fetchByConfigurationId`, `criterionCReferenceTableHtml`.
- **Live vs mock:** Mock/demo mode skips live fetch; Annex A values in `rules.js` remain for offline demos only.

---

## 5. Criterion C Dynamic Display

- Accomplishment cards: estimated line uses published indicator points when applicable.
- Summary bar: max from API summary or published `kra1-c` cap.
- Review page: backend **estimated** and **assessed** points unchanged; reference default for assessed input uses **locked** config when `configurationId` present, else applicable published points.
- **Published Criterion C point reference** table at bottom of review page (read-only).
- Labels updated from “Annex A reference” to **published configuration reference** where dynamic values are shown.

---

## 6. Historical Version Handling

When `bundle.scoringConfiguration` exists:

- Show **locked snapshot** line (version, effective date, provenance).
- Fetch indicator reference via `configurationId` without overwriting applicable global config.
- Finalized **reviewer-assessed** values displayed from backend only — no browser recalculation.
- Missing snapshot: “Historical scoring version unknown (legacy record).”

---

## 7. Criterion A/B Integration

- **Criterion A:** SET/SEF workspace and teaching effectiveness APIs unchanged; no local formula changes.
- **Criterion B:** Evidence and contribution workflows unchanged; scoring still backend-driven.
- Published caps/names from `kraSettings` apply wherever `FL.rules.applySettings` already merges Admin overrides (shared with KRA reference page).

---

## 8. KRA II–IV Integration

- Evidence workspace criterion picker appends **max N pts** from published `criteria.*.maxPoints` when available.
- Indicator-level KRA II–IV scoring formulas unchanged (not inferred in JS).

---

## 9. Reviewer Assessment Integrity

- Approve/reject/patch flows unchanged (`FL.criterionCEvidence.patchBundle`).
- Backend validation, duplicate/policy flags, and history preservation unchanged.
- No frontend-only bypass of blockers or assessed-point authority.

---

## 10. Configuration Refresh

| Trigger | Action |
|---|---|
| App boot (reviewer/admin live API) | `FL.scoringConfiguration.refresh({ source: "reviewer" })` |
| Evidence Workspace mount | Same (cached) |
| Criterion C list / review page | `FL.store.refreshScoringConfiguration()` |
| Official KRA reference page | `loadPublishedKraConfiguration()` → loader |
| Logout | `FL.scoringConfiguration.clear()` |

---

## 11. Test Results

**Node (Phase C7 JS unit checks):**

```text
node web/tests/scoring-configuration.test.js  →  all checks passed
```

**Python (no DB, `--noconftest`):**

```text
python -m pytest tests/kra_configuration/test_reviewer_scoring_api.py tests/kra_configuration/test_phase_c5_resolver.py -q --noconftest
→ 10 passed
```

**Browser QA:** Not automated in CI — see §13 (pending manual pass).

**Regression:** Existing Criterion C backend tests unchanged; Reviewer Web does not alter Flask routes or scoring engines.

---

## 12. Known Limitations

1. **Rank simulation** on Reviewer Web (if shown via estimated assessment) still uses backend payloads; no separate sim config panel added in C7.
2. **`asOf` query** exposed on loader but not yet wired to evaluation-period UI pickers.
3. **Mock/offline** demo continues to use Annex A embedded in `rules.js` when no live token.
4. **Admin published route** (`/api/admin/kra-configuration/published`) bypasses the new loader (admin draft workflow unchanged).
5. Full **HTTP integration tests** for reviewer JWT + PostgreSQL are skipped per project DB safety policy.

---

## 13. Manual Browser QA Steps

1. Sign in as **Reviewer** against a live backend with a **published** scoring configuration.
2. Open **Official KRA Scoring Reference** — confirm version/effective date banner and point values match Admin publish.
3. Open **Evidence Workspace** → assigned faculty → **KRA I** → **Criterion C** — confirm config banner and summary max.
4. Open an accomplishment — verify **Published reference** points, **backend estimated/assessed**, and locked snapshot line if bundle has `scoringConfiguration`.
5. Approve/reject with remarks — confirm backend errors still block invalid approvals; history preserved.
6. Publish a new configuration version in Admin — refresh Reviewer reference page without redeploying static assets; version should update after cache TTL or hard refresh (`force` on re-entry).
7. Compare indicator points with **Faculty Mobile** Criterion C hub for the same applicable config.

---

**Phase C8 is out of scope. Stopped for approval.**
