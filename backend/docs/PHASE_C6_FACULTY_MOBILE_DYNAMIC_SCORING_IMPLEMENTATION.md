# Phase C6 — Faculty Mobile Dynamic Scoring Configuration Integration

**Date:** 2026-11-03  
**Scope:** FacultyLink Flutter mobile application only (no Flask, Admin Web, or Reviewer Web changes).

---

## 1. Executive Summary

Phase C6 connects the Faculty Mobile app to the Phase C5 read-only scoring configuration APIs. A single in-app configuration pipeline loads the **applicable published** official configuration, exposes KRA/criterion/indicator caps and points for **display and previews**, and keeps **all authoritative totals** on the Flask backend (Criterion C summaries, reviewer-assessed points, rank simulation).

Criterion C hub, add-work wizard, and point tables now use published indicator values when configuration is applicable. When the server reports no applicable configuration or incomplete Criterion C indicators, the UI shows errors and blocks live uploads rather than silently using Annex A defaults. Mock/offline widget tests still use Annex A fallbacks only when no configuration holder is set.

---

## 2. Files Modified

| Path | Change |
|---|---|
| `mobile/lib/data/scoring_configuration.dart` | **New** — Phase C5 JSON parsing, `ScoringConfigurationHolder`, test fixture |
| `mobile/lib/data/kra_scoring_display.dart` | **New** — KRA/criterion max and label display helpers |
| `mobile/lib/widgets/scoring_configuration_banner.dart` | **New** — version / effective date / error banner |
| `mobile/lib/data/api_client.dart` | `fetchScoringConfiguration`, `fetchApplicableScoringConfiguration` |
| `mobile/lib/data/app_state.dart` | Load/cache/clear scoring config; sync on faculty workspace |
| `mobile/lib/data/criterion_c_catalog.dart` | Dynamic points/max from holder; Annex fallback only when holder empty |
| `mobile/lib/data/criterion_c_mapper.dart` | Nullable `previewPoints` |
| `mobile/lib/data/criterion_c_evidence.dart` | Non-const `CriterionCSummary` max default via catalog |
| `mobile/lib/screens/criterion_c/criterion_c_hub_screen.dart` | Config refresh, banner, dynamic max |
| `mobile/lib/screens/criterion_c/criterion_c_add_work_screen.dart` | Dynamic previews/table; config gate on upload |
| `mobile/lib/screens/criterion_c/criterion_c_track_screen.dart` | Server estimate labels; locked `scoringConfiguration` hint |
| `mobile/lib/screens/simulation/simulation_screen.dart` | Refresh config before rank sim; banner |
| `mobile/lib/screens/assessment/assessment_screen.dart` | Banner on KRA scores tab; config refresh |
| `mobile/lib/screens/documents/kra_explorer_screen.dart` | KRA/criterion max labels from published config |
| `mobile/lib/navigation/main_shell.dart` | Force config refresh on app resume |
| `mobile/test/scoring_configuration_test.dart` | **New** |
| `mobile/test/criterion_c_mobile_test.dart` | Holder fixture for dynamic point tests |
| `mobile/test/widget_test.dart` | Simulation tab expectations (offstage-safe) |

---

## 3. API Integration Details

| Endpoint | Use in mobile |
|---|---|
| `GET /api/faculty/me/scoring-configuration` | Primary fetch in `AppState.refreshScoringConfiguration()` |
| `GET /api/scoring-configuration/applicable?asOf=` | Implemented on `ApiClient` for future date-specific previews (faculty route used by default) |

**Parsed top-level fields (Phase C5 contract):**

- `configuration` — header (`id`, `status`, `guidelineLabel`, `publishedAt`, nested `metadata`)
- `kraSettings` — `kras`, `criteria`, `indicators` with `maxPoints` / `points` / `name`
- `metadata` — `configurationId`, `version`, `effectiveFrom`, `provenance`, `asOfDate`, etc.
- `rankWeightsPolicy` — informational (rank sim remains API-driven)
- `message` — when no applicable configuration

Backend resolution (evaluation period binding, document lock, effective dates) is **not reimplemented** in Flutter; the faculty endpoint returns the already-resolved applicable configuration for the signed-in faculty context.

---

## 4. Configuration Provider Architecture

- **`AppState`** owns fetch lifecycle: loading/error flags, 10-minute TTL cache (bypass with `force: true`), cleared on logout.
- **`ScoringConfigurationHolder.current`** mirrors the last successful parse so catalogs/widgets avoid circular imports with `AppState`.
- **`ScoringConfiguration.fromApi`** is the single parser; **`scoringConfigurationFixture()`** supports unit tests.
- Refresh triggers: faculty workspace sync (post-login), Criterion C hub (force), add-work open, rank simulation screen, assessment KRA tab, KRA explorer, app resume (`MainShell` + `force`).

---

## 5. Criterion C Dynamic Scoring Changes

- **Indicator points** (SP/CP, UT, MT, DD adviser/panel, mentorship) read from `kraSettings.indicators`.
- **Criterion C maximum** from `kraSettings.criteria['kra1-c'].maxPoints`, with API summary `maxPoints` preferred on hub when present.
- **Wizard previews** use `CriterionCMapper.previewPoints` → published values; null → configuration error on live API paths.
- **Accomplishment totals** remain from backend `scoring.estimatedPoints` / `reviewerAssessedPoints` in bundle APIs.
- **Track screen** shows locked bundle `scoringConfiguration` (version/effective date) when present, distinct from current applicable config banner elsewhere.

---

## 6. Criterion A/B Integration

- **Criterion A:** SET/SEF and teaching effectiveness cards unchanged; scores still from `/api/faculty/me/teaching-effectiveness` (and related SET/SEF indicator APIs). Published config does not replace SET/SEF formulas.
- **Criterion B:** Contribution allocation, evidence bundles, and wizard flows unchanged. No indicator point tables were moved to dynamic config in this phase (backend-driven scoring unchanged).

---

## 7. KRA II–IV Display Integration

- **KRA explorer** shows published **KRA max** on the KRA header and **criterion max** (and criterion name when provided) on criterion folder cards via `KraScoringDisplay`.
- **Indicator-level scoring** for KRA II–IV is unchanged and still depends on backend verification/reviewer logic; mobile does not compute those points locally.

---

## 8. Configuration Refresh Behavior

| Event | Behavior |
|---|---|
| Login / `_syncFacultyWorkspace` | `refreshScoringConfiguration(quiet: true)` |
| App resume | `refreshScoringConfiguration(quiet: true, force: true)` |
| Criterion C hub | `force: true` on load |
| Rank simulation tab | `force: true` before rank sim API |
| TTL | 10 minutes unless `force` |

Network failures set `scoringConfigurationError`; banner warns that previews may be unavailable. Live Criterion C upload path requires `criterionCScoringReady` (complete applicable indicators + cap).

---

## 9. Historical Version Handling

- **Evaluation-bound** configurations: `metadata.provenance` `explicit_id` or `evaluation_period` → `ScoringConfiguration.isEvaluationBound`.
- **Document accomplishments:** bundle JSON `scoringConfiguration` displayed on track screen; estimated/assessed points are historical server values, not recalculated with newly published config in Flutter.
- **Current applicable config** shown via `ScoringConfigurationBanner` on hub, add-work, simulation, and assessment tabs.

---

## 10. Rank Simulation Integration

- Simulation screen refreshes scoring configuration then calls existing `refreshRankSimulationFromApi()`.
- Results and KRA breakdown remain entirely from backend rank simulation payload; config banner is informational only.

---

## 11. Test Results

**Command:** `cd mobile && flutter test`

**Result:** **75 tests passed** (all suites).

**Command:** `cd mobile && flutter analyze`

**Result:** No new errors from Phase C6 changes. Remaining items are pre-existing infos/warnings (deprecated `withOpacity`, unused elements in unrelated files, etc.).

**New/updated coverage:**

- Phase C5 payload parsing and indicator/criterion lookups
- Dynamic Criterion C max and preview points with holder fixture
- Missing applicable config (no Annex fallback on live-shaped holder)
- Annex fallback when holder cleared (mock/tests)
- Evaluation-period provenance flag
- `CriterionCSummary.maxPoints` API vs catalog fallback
- Criterion C mobile regression tests with fixture
- Widget shell simulation tab (offstage-safe assertions)

---

## 12. Known Limitations

1. **`fetchApplicableScoringConfiguration(asOf:)`** is available but not yet used for “future effective” UI drills; backend still governs applicability on the faculty route.
2. **Criterion A/B** dynamic caps from `kraSettings` are not surfaced beyond existing API-driven score cards.
3. **KRA dashboard folder overview** cards do not yet append max labels (explorer only).
4. **Explicit pull-to-refresh** for scoring-only (without workspace refresh) is not a dedicated control; users rely on screen entry/resume/hub refresh.
5. **Mock auth** skips configuration fetch entirely (banner hidden); Annex A fallbacks apply in tests when holder is empty.

---

## 13. Manual Device Testing Instructions

1. Sign in with a **live** faculty account (not mock). Confirm backend has a **published** scoring configuration (Phase C5).
2. Open **Assessment → KRA scores** — verify gray banner shows config version and effective date.
3. Open **KRA I → Criterion C hub** — confirm max points match Admin published cap; banner matches assessment.
4. **Add accomplishment** — point preview and annex table match published indicators; attempt upload with backend stopped → error banner, no silent Annex points on live account.
5. Submit or open an existing **Criterion C accomplishment** — track screen shows server estimated points and, if locked, bundle scoring configuration version text.
6. Open **Rank simulation** — pull refresh; confirm simulation still loads and banner appears.
7. Publish a **new** configuration version in Admin (staging only if available) — return to app (background/foreground) or re-open Criterion C hub; confirm version updates without reinstalling the app.
8. For an evaluation tied to an **older bound config**, confirm accomplishment track still shows locked version while banner may show currently applicable config for new work.

---

**Phase C7 (Reviewer Web) is out of scope for this deliverable.**
