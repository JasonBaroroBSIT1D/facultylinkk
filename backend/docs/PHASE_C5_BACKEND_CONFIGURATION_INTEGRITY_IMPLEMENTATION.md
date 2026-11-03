# Phase C5 — Backend Configuration Integrity & Historical Scoring Protection

**Date:** 2026-11-03  
**Scope:** Flask/Python backend and PostgreSQL only (no Mobile/Web UI changes).

---

## 1. Executive Summary

Phase C5 centralizes **applicable** official scoring configuration resolution (effective-date aware), adds **historical version binding** for evaluation periods and finalized documents, makes **Criterion C criterion maximum** authoritative from published Admin config, records **Admin publish audit events**, extends **publish validation**, and exposes **read-only scoring configuration APIs** for Phases C6–C7.

Existing scoring formulas (SET/SEF, Criterion B contribution logic, reviewer-assessed stored points) are unchanged. Legacy records without version bindings continue to use stored reviewer/verified points and Annex A fallbacks only when no applicable published configuration is present.

---

## 2. Files Modified / Added

| Path | Change |
|---|---|
| `kra_configuration/resolver.py` | **New** — effective-date resolution, explicit ID, provenance |
| `kra_configuration/statuses.py` | **New** — status constants |
| `kra_configuration/version_lock.py` | **New** — period/document binding helpers |
| `kra_configuration/publish_integrity.py` | **New** — extended publish validation |
| `kra_configuration/read_api.py` | **New** — read-only payload builder |
| `kra_configuration/read_routes.py` | **New** — `GET /api/scoring-configuration/applicable` |
| `kra_configuration/service.py` | Applicable `get_published_row`, publish audit, draft guard |
| `kra_configuration/published_limits.py` | Resolver-backed `published_settings_blob` |
| `kra_configuration/criterion_c_annex.py` | `published_criterion_c_max_points`, stricter indicator lookup |
| `kra_configuration/verified_scoring.py` | Integrates publish integrity checks |
| `kra_configuration/routes.py` | New error messages |
| `documents/criterion_c_evidence/scoring.py` | Dynamic Criterion C cap |
| `documents/scoring/criterion_c_simulation_adapter.py` | Passes `applicable_config_present` |
| `documents/criterion_c_evidence/service.py` | Version lock on C approval; summary uses resolver |
| `documents/criterion_c_evidence/reviewer_assessment.py` | Annex fallback policy |
| `documents/service.py` | Lock on generic document approve |
| `documents/scoring/config_loader.py` | Lazy import (break circular deps) |
| `evaluation_periods/service.py` | Bind config when period published |
| `faculty/kra_document_aggregate.py` | Faculty simulation settings via version lock |
| `faculty/rank_simulation_engine.py` | Shared resolution + rank weight policy metadata |
| `faculty_routes.py` | `GET /api/faculty/me/scoring-configuration` |
| `reviewer_routes.py` | Enhanced `/kra-configuration` metadata |
| `factory.py` | Register scoring read blueprint |
| `models.py` | Additive FK columns |
| `migrations/versions/20261103_scoring_configuration_version_lock.py` | **New** migration |
| `tests/kra_configuration/test_phase_c5_resolver.py` | **New** |
| `tests/faculty/test_kra1_simulation_max.py` | Patch update |
| `tests/faculty/test_rank_simulation_criterion_b_wiring.py` | Patch update |

---

## 3. Database Changes and Migration Details

**Migration:** `20261103_scoring_version_lock` (applied via `flask db upgrade`).

| Table | Column | Purpose |
|---|---|---|
| `documents` | `scoring_kra_configuration_id` (nullable FK → `kra_configuration.id`) | Set once when scoring is finalized (approved + points or Criterion C approval) |
| `evaluation_periods` | `kra_configuration_id` (nullable FK) | Set once when Admin publishes the evaluation period |

**No backfill.** Legacy rows remain `NULL` → provenance `legacy` / `applicable_as_of` in API metadata.

---

## 4. Configuration Resolution Rules

**Module:** `kra_configuration/resolver.py`

1. **Draft** — never used for scoring.
2. **Explicit ID** (`kra_configuration_id`) — used for bound evaluation periods, locked documents, or API `configurationId` query (historical superseded rows allowed).
3. **Default** — among `published` + `superseded` rows with `published_at`:
   - `effectiveFrom <= as_of` (default as_of = today, Asia/Manila via `local_today()`)
   - `effectiveTo` null or `effectiveTo >= as_of`
   - Choose **latest `effectiveFrom`**, tie-break **latest `published_at`**.

`get_published_row()` now returns the **applicable** row, not merely the newest by publish timestamp.

---

## 5. Effective-Date Behavior

| Scenario | Behavior |
|---|---|
| Future `effectiveFrom` | Excluded until calendar date reaches `effectiveFrom` |
| Superseded row with valid window | Selectable for historical `configurationId` or past `asOf` |
| Current simulation | Uses published evaluation period binding if set; else applicable-as-of-today |

Query params on read API: `asOf=YYYY-MM-DD`, `configurationId=<int>`.

---

## 6. Historical Version-Locking Strategy

| Layer | When bound | Immutable? |
|---|---|---|
| **Evaluation period** | First Admin publish of period (`evaluation_periods/service.py`) | FK not overwritten |
| **Document** | On approve with finalized points, or Criterion C reviewer approval | FK not overwritten |
| **Criterion C bundle JSON** | On reviewer accomplishment decision | `scoringConfiguration` snapshot in bundle |

**Finalized scores** (`verified_points`, `reviewer_score`, bundle `assessedPoints`) are not recalculated by Phase C5.

---

## 7. Legacy Assessment Compatibility

- Documents without `scoring_kra_configuration_id`: scoring uses **evaluation period binding** or **applicable-as-of-today** for **estimates** only.
- `effective_document_points()` unchanged — still prefers stored verified/reviewer values.
- Annex A defaults used **only** when `allow_annex_fallback=True` (no applicable published row or tests without full config).

---

## 8. Criterion C Dynamic Scoring Integration

- Per-indicator points: `published_points_for_indicator(..., allow_annex_fallback=...)`.
- Criterion maximum: `published_criterion_c_max_points()` / `published_criterion_max_points("kra1-c")`.
- Aggregation cap uses published max; returns `scoringSource: configuration_incomplete` if applicable config exists but max missing.

Official Annex A reference values remain in `ANNEX_A_DEFAULT_POINTS` as **documented fallback only**.

---

## 9. Criterion A/B Regression Protection

- SET/SEF: `config_loader.indicator_scoring_config()` unchanged in formula; uses applicable row via lazy `get_published_row()`.
- Criterion B: same published settings blob path via `resolve_settings_for_faculty_simulation()` — no contribution formula changes.
- Tests: `test_criterion_c_phase_c1.py`, `test_rank_simulation_criterion_b_wiring.py`, `test_kra1_simulation_max.py` — **pass**.

---

## 10. Rank Simulation Behavior

- Uses `resolve_settings_for_faculty_simulation()` (evaluation period → applicable config).
- Response adds `scoringConfiguration` (resolution metadata) and `rankWeightsPolicy`.
- **Rank weights:** if published `rankWeights` (settings JSON or `rank_weights` column) empty → **Table 2.2 engine defaults** (`TABLE_22_DEFAULTS`) — same as pre–Phase C5, explicitly documented in API policy object.

---

## 11. Admin Publication Audit Trail

On successful `publish_draft()` (same transaction):

- `AuditLog.action`: `"Official scoring configuration published"`
- Detail JSON: `configurationId`, `version`, `effectiveFrom`, `effectiveTo`, `guidelineLabel`, `publishedAt`, `previousActiveConfigurationId`

Failed publish attempts do **not** write this audit entry.

---

## 12. Published Version Immutability

- Only **draft** rows are updated by `save_draft()`.
- Publish always **inserts** a new row; prior `published` → `superseded`.
- `save_draft` rejects non-draft row conflicts (`draft_immutable_conflict`).
- No API path modifies `settings_json` on published/superseded rows.

---

## 13. Read-Only API Contracts for C6/C7

### Faculty

`GET /api/faculty/me/scoring-configuration`  
`Cache-Control: no-store`

### Faculty & Reviewer (shared)

`GET /api/scoring-configuration/applicable?asOf=YYYY-MM-DD&configurationId=<id>`  
Roles: faculty or reviewer JWT.

### Reviewer (existing, extended)

`GET /api/reviewer/kra-configuration` — adds `metadata`, `rankWeightsPolicy`.

**Response shape (applicable endpoints):**

```json
{
  "configuration": { "id", "status", "guidelineLabel", "publishedAt", "metadata" },
  "kraSettings": { "kras", "criteria", "indicators", "indicatorMeta", ... },
  "metadata": {
    "configurationId", "version", "effectiveFrom", "effectiveTo",
    "provenance", "asOfDate", "scoringVersionProvenance"
  },
  "rankWeightsPolicy": {
    "source": "published_admin_configuration | table_22_defaults_in_engine",
    "publishedRankWeightsPresent": false,
    "note": "..."
  }
}
```

---

## 14. Test Results

Executed ( `--noconftest` ):

```
tests/kra_configuration/** 
tests/documents/test_criterion_c_phase_c1.py
tests/faculty/test_kra1_simulation_max.py
tests/faculty/test_rank_simulation_criterion_b_wiring.py
→ 79 passed
```

**Not executed in this pass:** full `tests/documents` with conftest, staging e2e, Flutter/Web tests (out of scope).

**DB migration:** `flask db upgrade` → `20261103_scoring_version_lock` applied successfully.

---

## 15. Known Limitations

1. **Per-document mixed config in one KRA total** — simulation uses period-level config; individual locked documents retain points but do not yet drive per-document config in a single aggregate pass.
2. **KRA II–IV** — still document-stored points with published caps only (unchanged by design in Phase C5).
3. **Publish validation** — Criterion C integrity checks apply when Criterion C appears in draft (`kra1-c` criteria or `kra1-c-*` indicators); minimal SET/SEF-only test drafts remain valid.
4. **Rank thresholds** — still optional in published JSON; empty thresholds → incomplete progress messaging (unchanged).

---

## 16. Manual Verification Instructions

1. **Migration:** `flask --app factory:create_app db upgrade` — confirm columns on `documents` and `evaluation_periods`.
2. **Applicable config:** `GET /api/faculty/me/scoring-configuration` with faculty JWT — verify `metadata.version` matches DB published row effective today.
3. **Future effective:** Publish draft with `effectiveFrom` in the future; confirm simulation still uses prior superseded row until date.
4. **Publish audit:** Publish draft; inspect `audit_logs` for `"Official scoring configuration published"`.
5. **Criterion C cap:** Change `criteria.kra1-c.maxPoints` in draft, publish, call `GET /api/faculty/me/documents/criterion-c/summary` — `maxPoints` should match published value.
6. **Document lock:** Approve Criterion C accomplishment; confirm `documents.scoring_kra_configuration_id` set once; republish config; confirmed `assessedPoints` unchanged.

---

**STOP — Phase C6 (Faculty Mobile integration) not started.**
