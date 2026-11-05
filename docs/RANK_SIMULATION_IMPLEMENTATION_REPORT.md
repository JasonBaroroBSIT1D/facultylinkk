# Rank Upgrade Simulation — Implementation Report

**Date:** 2026-11-05  
**Scope:** Parts 1–13 (FacultyLink existing codebase)

## 1. Files modified / added

| Path | Change |
|------|--------|
| `backend/faculty/rank_simulation_engine.py` | Table 2.2 normalization, Table 3.1 brackets, breakdown, readiness, API fields |
| `backend/faculty/rank_hierarchy.py` | **New** — rank ladder, sub-rank increment, category transition gate |
| `backend/tests/faculty/test_rank_simulation_weighted_scoring.py` | **New** — unit tests |
| `backend/kra_configuration/read_api.py` | Document Table 3.1 published override |
| `mobile/lib/models/models.dart` | Extended `RankSimulation` model |
| `mobile/lib/data/faculty_api_mapper.dart` | Parse new simulation fields; fix verified weighted score |
| `mobile/lib/data/app_state.dart` | Debounced `openSimulation` + quiet refresh |
| `mobile/lib/widgets/simulation_result_card.dart` | Compact home card layout + full-surface tap |
| `mobile/lib/widgets/rank_upgrade_simulation_card.dart` | Brackets, est/verified totals, preparation readiness |
| `mobile/lib/widgets/weighted_kra_breakdown_table.dart` | **New** — Excel-style table |
| `mobile/lib/screens/simulation/simulation_screen.dart` | Breakdown tables + readiness checklist |
| `mobile/lib/data/mock_data.dart` | Mock weighted contributions for offline preview |

## 2. Backend calculation changes

- **Weighted contribution:** `(KRA score ÷ applicable KRA max) × Table 2.2 weight in points` (sum out of 100).
- **Estimated vs verified:** Separate totals and per-KRA contributions (`estimatedWeightedContributions`, `verifiedWeightedContributions`).
- **Table 3.1:** Default brackets in engine; overridable via published `scoreBrackets` / `table31SubrankIncrements`.
- **Possible rank:** Ladder in `rank_hierarchy.py`; increment from estimated weighted total; category transitions require published `rankCategoryTransitions` (otherwise increment stops at category ceiling with `rankTransitionNote`).
- **Preparation readiness:** Separate checklist (% complete) — not mixed with weighted score or threshold `progressPercent`.

## 3. Rank hierarchy and transition rules

- Ladder: Instructor I–III → Assistant Professor I–IV → Associate Professor I–V → Professor I–VI → College/University Professor.
- **Category transitions:** Blocked unless Admin published JSON includes `rankCategoryTransitions` (e.g. `allowedCategoryTransitions` or per-category lists).
- **Eligibility:** Existing `_eligibility_state` unchanged; simulation does not auto-approve promotion.

## 4. Official scoring reference mapping

| Reference | Implementation |
|-----------|------------------|
| Table 2.2 weights | `TABLE_22_DEFAULTS` + published `rankWeights` / DB column |
| Table 3.1 brackets | `TABLE_31_DEFAULTS` + optional published `scoreBrackets` |
| KRA maxima | Published KRA/criterion caps via existing scoring engine |

## 5. Readiness formula and checklist

`preparationReadinessPercentage = (completed applicable items / total applicable items) × 100`

Applicable items (when config complete):

- SET / SEF semester coverage (when required or uploads exist)
- KRA I–IV “evidence assessed” flags

Returns `null` + label when published config incomplete or no applicable denominator.

## 6. Home Screen UI

- Dark green card preserved; compact row of four **weighted contributions**; weighted total, preparation readiness, status chip text.
- **Possible Rank** label (not “Eligible For”).
- Entire card wrapped in `InkWell` → `AppState.openSimulation` (tab index 2 + debounced refresh).

## 7. Simulation screen

- Rank header card: bracket, sub-rank increment, est/verified weighted totals, preparation progress ring.
- Estimated and verified weighted breakdown tables.
- Readiness checklist + existing missing requirements + disclaimer.

## 8. Navigation

| Check | Result |
|-------|--------|
| Tap home card → Simulation tab | **PASS** (code) |
| Tab index 2 = `SimulationScreen` | **PASS** |
| Debounced navigation | **PASS** |
| Backend refresh on open | **PASS** |
| Android device manual test | **NOT TESTED** (no adb run in this session) |

## 9. Admin configuration

- Existing publish pipeline unchanged.
- Published JSON may include: `rankWeights`, `scoreBrackets`, `rankCategoryTransitions`, `rankUpgradeThresholds`.
- Empty weights/brackets fall back to engine Table 2.2 / 3.1 defaults (documented in read API note).

## 10. Tests executed

| Test | Result |
|------|--------|
| `tests/faculty/test_rank_simulation_weighted_scoring.py` | **PASS** (5) |
| `tests/faculty/test_rank_simulation_criterion_b_wiring.py` | **PASS** (10) |
| Flutter `dart analyze` (changed paths) | **PASS** |
| On-device Flutter layout / tap | **NOT TESTED** |
| QA DB live rank sim script | **NOT RUN** (this session) |

## 11. Verification matrix (summary)

| Area | Status |
|------|--------|
| Instructor / AP / Assoc / Prof / Col-Univ weights | **PASS** (defaults + published hook) |
| Table 3.1 boundaries | **PASS** (unit tests) |
| Possible rank display | **PASS** (backend + Flutter) |
| Readiness separate from weighted score | **PASS** |
| Est vs verified labeling | **PASS** |
| Home card compact + clickable | **PASS** (code) |
| Full DBM–CHED compliance claim | **BLOCKED** — requires verified official transition/eligibility rules in Admin config |

## 12. Mobile UI redesign (2026-11-05)

- Replaced dark stacked tables with light cards: rank progress, 2×2 KRA grid, readiness bar, friendly checklist.
- **Estimated | Reviewer-Verified** segmented toggle (display rules mirror backend for verified rank path).
- Technical scoring moved under **“How was my score calculated?”** expansion.
- Files: `simulation_screen.dart`, `widgets/simulation/simulation_ui_sections.dart`, `simulation/simulation_view_model.dart`, `simulation/simulation_friendly_requirements.dart`, `simulation/simulation_display_rules.dart`.
- **Flutter test:** `test/simulation_view_model_test.dart` — **PASS**.
- **360dp device test:** **NOT TESTED** (no adb this session).

## 13. Remaining blockers

1. Publish **`rankCategoryTransitions`** in Admin when cross-category possible ranks should appear (e.g. Instructor III → Assistant Professor I).
2. Populate **`rankUpgradeThresholds`** if threshold-based `progressPercent` should drive UI alongside readiness.
3. Physical Android verification recommended for overflow and tap targets.
