# KRA I Criterion B — scoring helper API (Phase 2a)

Reference: **DBM–CHED Joint Circular No. 01, s. 2026** (Annex A, §§11–14).  
This module does **not** replace Criterion A (SET/SEF) or persist scores. It prepares reviewer validation and evidence-bundle work in Phase 2b+.

## Modules

| Module | Role |
|--------|------|
| `kra_configuration.criterion_b_annex` | Ten indicator IDs → six Annex A rows |
| `kra_configuration.criterion_b_scoring` | Points math, caps, aggregation helpers |

## Annex mapping

Each **Annex A row** has one `base_indicator_id` in published Admin config. Co-author IDs (`*-co`) share that base; points use **Annex C** contribution percentage.

| `row_id` | `base_indicator_id` | Co indicator |
|----------|---------------------|--------------|
| `textbook` | `kra1-b-textbook-sole` | `kra1-b-textbook-co` |
| `module` | `kra1-b-module-sole` | `kra1-b-module-co` |
| `instructional_manual` | `kra1-b-manual-sole` | `kra1-b-manual-co` |
| `multimedia` | `kra1-b-multimedia-sole` | `kra1-b-multimedia-co` |
| `program_lead` | `kra1-b-program-lead` | — |
| `program_contributor` | `kra1-b-program-contributor` | — |

## Published configuration inputs

- **Criterion B maximum:** `settings.criteria["kra1-b"].maxPoints` (default fallback 30 if missing).
- **Indicator base points:** `settings.indicators[base_indicator_id].points` or `.maxPoints`.
- **KRA I overall maximum:** `settings.kras["kra1"].maxPoints` (fallback 100).

Co indicators must **not** rely on a separate official base in config; the helper reads the sole/program row only.

## `compute_criterion_b_indicator_points`

```python
compute_criterion_b_indicator_points(
    indicator_id: str,
    *,
    contribution_percent: float | int | str | None = None,
    evidence_verified: bool = False,
    settings: dict | None = None,
) -> CriterionBScoreResult
```

### Parameters

| Parameter | Meaning |
|-----------|---------|
| `indicator_id` | One of the ten legacy Criterion B IDs |
| `contribution_percent` | Required for `*-co` indicators; ignored for sole/program rows |
| `evidence_verified` | **False** by default; when false, `points` is always `None` |
| `settings` | Published `kraSettings` blob; omit to load from DB (not used in unit tests) |

### Rules

1. **Sole / program:** `points = base` when `evidence_verified` is true and base is published.
2. **Co-author:** `points = base × (contribution_percent / 100)` when verified; contribution must be in **0–100**.
3. **Missing contribution** on co rows → `eligible=False`, reason `contribution_percent_required`.
4. **Out of range contribution** → `contribution_percent_out_of_range`.
5. **Unverified evidence** → `evidence_not_verified` (no silent scoring).

### Result fields (`CriterionBScoreResult.as_dict()`)

- `points` — capped-ready score for this indicator claim, or `null`
- `basePoints`, `contributionPercent`, `rawPoints`, `annexRowId`, `eligible`, `reasons`

## Ceiling helpers

```python
cap_criterion_b_total(component_points, settings=None) -> (capped_total, raw_sum)
cap_kra1_instruction_total(criterion_a_points=..., criterion_b_points=..., criterion_c_points=..., settings=None)
aggregate_criterion_b_from_results(results, settings=None, dedupe_keys=None) -> (capped_total, raw_sum)
```

- Criterion B sum is capped at published **30** (or configured max).
- KRA I sum (A+B+C) is capped at published **100**; A is not computed here.

## Phase 2b evidence bundles

Instructional material claims use JSON bundles on the primary `Document` row. See **`CRITERION_B_EVIDENCE.md`**.

Scoring helpers remain **not** wired to rank simulation until checklist validation and reviewer verification are complete.

## Later integration (planned)

1. Reviewer approval sets `evidence_verified=True` only when bundle `validation.readyForScoring` is true.
2. Rank simulation may call `aggregate_criterion_b_from_results` after explicit approval.

## Non-goals (Phase 2a)

- No PostgreSQL writes, migrations, or changes to `rank_simulation_engine.py`.
- No UI changes (Reviewer Web / Flutter).
- No automatic verification from OCR or upload status.
