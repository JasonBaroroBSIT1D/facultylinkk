# Phase 5 — Criterion B rank simulation integration plan

Status: **Phase 5B wired** — adapter integrated in `kra_document_aggregate`; **`CRITERION_B_SIMULATION_ADAPTER_ENABLED` remains `False`** (production behavior unchanged).

## Current behavior (pre–5B)

| Component | Criterion B behavior |
|-----------|----------------------|
| `faculty/kra_document_aggregate.py` | Sums `effective_document_points()` per indicator (best per `indicator_id`), criterion cap via `published_criterion_max_points`. Supporting docs already excluded. |
| `faculty/rank_simulation_engine.py` | KRA I = SET/SEF (Criterion A) + `aggregate_criterion_documents(..., "kra1-b")` + Criterion C. **No bundle gate.** |
| `documents/scoring/document_evidence_points.py` | May return OCR/legacy estimates for `kra1-b` primaries — **can bypass evidence bundles today.** |

## Target behavior (5B)

1. When `CRITERION_B_SIMULATION_ADAPTER_ENABLED` is true, Criterion B simulation uses **`documents/scoring/criterion_b_simulation_adapter.py`** only.
2. Points flow: `criterionBEvidenceBundle` → validate → `readyForScoring` → `compute_criterion_b_indicator_points(..., evidence_verified=True)` → `aggregate_criterion_b_from_results`.
3. Criterion A / SET–SEF paths in `rank_simulation_engine.py` and `teaching_effectiveness` **unchanged**.
4. Response shape for `criteriaScores[]` / `kra1.criteriaScores` **unchanged** (`criterionId`, `estimatedPoints`, `maxPoints`, `name`, `bonus`).

## Adapter API (implemented, not wired)

| Function | Role |
|----------|------|
| `score_primary_document_for_simulation(doc, settings=)` | One primary claim; ignores legacy point columns. |
| `aggregate_criterion_b_simulation_from_documents(docs, settings=)` | Profile-level B total for simulation. |
| `CRITERION_B_SIMULATION_ADAPTER_ENABLED` | Default `False`; flip in 5B after QA. |

## Phase 5B file touch list

| File | Change |
|------|--------|
| `documents/scoring/criterion_b_simulation_adapter.py` | Enable flag; optional env read. |
| `faculty/kra_document_aggregate.py` | **Done:** `aggregate_criterion_documents` → `aggregate_criterion_documents_from_list`; Criterion B adapter when flag on. |
| `faculty/rank_simulation_engine.py` | Unchanged; calls `aggregate_criterion_documents` as before. |
| `documents/scoring/document_evidence_points.py` | Unchanged when flag off; legacy B points still used until flag enabled. |
| `backend/docs/CRITERION_B_SCORING.md` | Cross-link this plan. |

**Do not modify:** `kra_configuration/*` published blob, Criterion A modules, migrations, Admin UI config.

## Aggregation policy (existing code — do not invent)

From `kra_configuration.criterion_b_scoring`:

1. Score each **eligible primary claim** → `CriterionBScoreResult`.
2. **`deduplication_key_for_bundle`** per primary claim (primary file hash or normalized title / program name + indicator).
3. **`aggregate_eligible_points_by_output`**: max points per `(annex_row_id, dedupe_key)`, then **sum** → **`cap_criterion_b_total`** (published `kra1-b` max, default **30**). See **`CRITERION_B_AGGREGATION_POLICY.md`**.
4. KRA I total: existing `_kra1_from_teaching` adds Criterion A estimate + B + C; **`cap_kra1_instruction_total`** enforces KRA I **100** when used.

### Policy open question (report, do not guess)

**Annex row vs indicator:** See **`CRITERION_B_AGGREGATION_POLICY.md`** — material-level dedupe prevents sole/co double credit; distinct outputs on the same row may stack until the **30** criterion cap.

## `readyForScoring` vs simulation estimation

| Concept | Meaning |
|---------|---------|
| `validationStatus` | Faculty/reviewer workflow: incomplete → reviewer_required → valid / invalid. |
| `readyForScoring` | **Strict gate for simulation points in 5B:** all mandatory checklist slots **reviewer-verified**, metadata satisfied (complete set, specialization, co-author %, program approvals). |
| Simulation label | Remains **estimated**; disclaimer unchanged in `rank_simulation_engine.SIMULATION_DISCLAIMER`. |

**Decision for 5B:** Simulation **must not** award Criterion B points when `readyForScoring` is false, even if `validationStatus` is `reviewer_required` with uploads present. **No provisional Criterion B partial points** unless product explicitly requests a separate `estimatedPointsProvisional` field (out of scope for 5A/5B as specified).

### Program optional slots (fixed Phase 5A.1)

Optional slots no longer block `valid` / `readyForScoring` when empty. Linked-but-unverified optional files may still surface `optional_*_reviewer_required` flags.

## Compatibility

- Flutter / Reviewer Web read `kraScores` and `criteriaScores`; numeric fields stay the same.
- When adapter enabled and no claims are ready, `estimatedPoints` for `kra1-b` should be **`null`** (not legacy OCR sum) — **will change simulation numbers** for faculty with unverified bundles; expected and required by Phase 4.5 audit. Ship behind flag + release note.

## Tests (Phase 5A)

`tests/documents/test_criterion_b_simulation_adapter.py` — happy path IM/program, cap, negatives, legacy bypass block.

Run:

```bash
cd backend && python -m pytest tests/documents/test_criterion_b_simulation_adapter.py -q
```

## GO / NO-GO for Phase 5B

| Gate | Status |
|------|--------|
| Adapter unit tests | Required — run in CI |
| Annex row double-count policy | **Product/legal** if strict one-row-one-score required |
| Staging manual QA (Phase 4.5 checklist) | Required before production flag |
| Feature flag default off | Required |

**Engineering GO for 5B implementation** once stakeholders accept (a) possible simulation drop when legacy points replaced by bundle gate, and (b) indicator-level aggregation as coded. **Production NO-GO** until staging QA + flag rollout.
