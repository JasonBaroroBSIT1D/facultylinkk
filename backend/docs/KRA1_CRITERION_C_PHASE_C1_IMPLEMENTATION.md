# KRA I Criterion C — Phase C1 Backend Implementation

**Scope:** Backend scoring and evidence workflow only (no Faculty Mobile or Reviewer Web UI).  
**Authority:** DBM–CHED Joint Circular No. 01, s. 2026, §15 and Annex A; accumulation policy per `KRA1_CRITERION_C_ACCUMULATION_POLICY_VERIFICATION.md` (Option A: sum distinct eligible services, cap 10).

## Files created

| Path | Role |
|------|------|
| `kra_configuration/criterion_c_annex.py` | Criterion ID, Annex A default points, indicator metadata |
| `documents/criterion_c_evidence/checklist.py` | Research and mentorship evidence slots |
| `documents/criterion_c_evidence/bundle.py` | JSON bundle in `Document.extracted_info` |
| `documents/criterion_c_evidence/deduplication.py` | Duplicate service and adviser/panel overlap flags |
| `documents/criterion_c_evidence/validation.py` | Evidence readiness; OCR never certifies eligibility |
| `documents/criterion_c_evidence/reviewer_assessment.py` | Per-accomplishment approve/reject with audit history |
| `documents/criterion_c_evidence/scoring.py` | Per-service sum, cap 10; legacy fallback |
| `documents/criterion_c_evidence/service.py` | Init, link supporting, faculty/reviewer APIs |
| `documents/criterion_c_evidence/__init__.py` | Package marker |
| `documents/scoring/criterion_c_simulation_adapter.py` | Rank simulation wiring + env flag |
| `tests/documents/test_criterion_c_phase_c1.py` | Phase C1 unit tests |

## Files modified

| Path | Change |
|------|--------|
| `faculty/kra_document_aggregate.py` | `kra1-c` branch via Criterion C simulation adapter |
| `documents/service.py` | Initialize C bundles; route supporting uploads to C or B primary |
| `documents/routes.py` | Faculty/reviewer Criterion C evidence-bundle and summary routes |
| `documents/scoring/document_evidence_points.py` | Exclude Criterion C supporting documents |

**No Alembic migration** — accomplishments live in existing `documents` rows with `criterionCEvidenceBundle` JSON (same pattern as Criterion B).

## Architecture

- **Primary accomplishment:** one `Document` per service (`criterion_id=kra1-c`, indicator encodes role/type).
- **Bundle:** `extracted_info.criterionCEvidenceBundle` holds metadata, checklist, reviewer assessment, dedupe/policy flags.
- **Supporting files:** separate uploads with `criterionCEvidenceLink.role=supporting`; excluded from legacy point aggregation.
- **Scoring:** `aggregate_criterion_c_from_documents()` sums **reviewer-approved** services; `min(sum, 10)`. Documents **without** bundles keep **legacy best-per-indicator** (historical preservation).
- **Rank simulation:** `aggregate_criterion_documents(..., "kra1-c")` uses adapter when `CRITERION_C_SIMULATION_ADAPTER_ENABLED` is true (default **on**; set `0`/`false`/`off` to mirror Criterion B rollout gating).

## Official scoring mapping

| Indicator | Service | Points |
|-----------|---------|--------|
| `kra1-c-adviser-sp` | Capstone / SP adviser | 3 |
| `kra1-c-panel-sp` | Capstone / SP panel | 1 |
| `kra1-c-adviser-ut` | UG thesis adviser | 5 |
| `kra1-c-panel-ut` | UG thesis panel | 1 |
| `kra1-c-adviser-mt` | Master’s adviser | 8 |
| `kra1-c-panel-mt` | Master’s panel | 2 |
| `kra1-c-adviser-dd` | Doctoral adviser | 10 |
| `kra1-c-panel-dd` | Doctoral panel | 2 |
| `kra1-c-mentor` | Mentorship (for every eligible service) | 3 |

Admin-published `indicators` config overrides defaults when present.

## Evidence validation

**Research:** signed approval sheet; RRPA/COPC. Metadata requires title, student name(s), completion date.

**Mentorship:** designation, award/certificate, competition mechanics, awarding organization profile; competition name required.

Checklist slots must be **reviewer-verified** before accomplishment approval. Upload/OCR alone does not set `readyForScoring`.

## Duplicate prevention

- `duplicate_service_suspected` when dedup key matches another bundle (faculty, title, students/group, role, type, completion date, AY).
- `adviser_panel_same_thesis_review` when adviser + panel claims share the same thesis identity (title, students, completion date) — blocks approval until resolved.
- Shared RRPA/COPC may be linked per accomplishment without treating one research service as multiple accomplishments.

## API endpoints

**Faculty** (`/api/faculty/me/documents`):

- `GET /criterion-c/summary` — criterion totals and service breakdown
- `GET /criterion-c/accomplishments` — accomplishment list
- `GET|PATCH /<id>/criterion-c/evidence-bundle`
- `POST /<id>/criterion-c/link-supporting`

**Reviewer** (`/api/reviewer`):

- `GET|PATCH /documents/<id>/criterion-c/evidence-bundle` (slot verification, `reviewStatus`, `assessedPoints`, remarks)

Upload init: primary Criterion C upload auto-creates bundle; supporting upload uses `bundlePrimaryId` + `evidenceSlot` (same as B).

## Rank Simulation integration

`rank_simulation_engine.py` already calls `aggregate_criterion_documents(..., "kra1-c")`; Phase C1 replaces legacy-only math when the adapter is enabled. Criterion A/B paths unchanged.

## Test results

```text
pytest tests/documents/test_criterion_c_phase_c1.py --noconftest  → 20 passed
```

Coverage includes: all Annex point values, mentorship 3 pts, multi-service accumulation, cap 10, rejected exclusion, missing evidence, dedupe, adviser/panel flag, assessed vs eligible, legacy fallback, adapter wiring, Criterion B regression spot-check.

*(Full suite with Flask `conftest` requires project virtualenv/`factory` module on `PYTHONPATH`.)*

## Remaining policy uncertainties

1. **Adviser + panel on same thesis** — flagged for manual policy review; no automatic grant/deny of both (per accumulation verification doc).
2. **Consolation/local prizes (mentorship)** — bundle fields capture placement; reviewer must enforce §15.2 (no auto-reject rules beyond evidence gates).
3. **Hybrid legacy + new services** — legacy best-per-indicator may coexist with new per-service accomplishments until legacy rows are migrated or superseded (by design for non-destructive rollout).

## Steps before Phase C2 (Mobile / Reviewer Web)

1. Faculty wizard: metadata capture, evidence slot uploads, summary/scoring display from new APIs.
2. Reviewer workspace: Criterion C checklist UI, accomplishment approve/reject, policy flag handling.
3. Staging: confirm `CRITERION_C_SIMULATION_ADAPTER_ENABLED` policy with ops (default on in code).
4. Optional: migrate high-value legacy `kra1-c` documents to bundles without changing historical scores until reviewed.

**Phase C1 complete — stop here per scope.**
