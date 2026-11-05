# KRA IV — Professional Development — Implementation Status

**Date:** 2026-11-05 (updated)  
**Source of truth:** `web/js/rules.js` (KRA IV block) + `backend/kra_configuration/data/kra4_indicators.json`

## Summary

KRA IV now has **end-to-end wiring** for catalog, backend evidence, Flask APIs, reviewer web (shared KRA II/III workspace), faculty mobile hub/wizard, indicator-family OCR hints, and rank simulation aggregation. **Live browser/mobile QA with real credentials and uploads is still required** to claim full completion.

## Component status

| Component | Status | Notes |
|-----------|--------|--------|
| 19 indicators + caps | **Complete** | `kra4_indicators.json`, annex/registry |
| Evidence backend | **Complete** | `backend/documents/kra4_evidence/*` |
| Flask API routes | **Complete** | `backend/documents/kra4_routes.py` (22 routes registered) |
| Reviewer web workspace | **Complete (integration)** | `kra4-evidence.js`, `kra2-a-review.js`, `documents.js`, `evidence-workspace.js` |
| Faculty Flutter module | **Complete (integration)** | `mobile/lib/screens/kra4/*`, `kra4_catalog.dart`, API client |
| OCR (advisory) | **Complete (family parsers)** | `kra4OcrExtraction`, no auto-approve |
| Admin scoring config | **Verify in UI** | KRA IV in `rules.js`; publish path should include `kra4-*` — confirm in Admin |
| Rank simulation | **Wired** | `kra4_simulation_adapter.py`, `kra_document_aggregate.py` |
| E2E QA | **Incomplete** | No `[KRA4-QA]` live matrix run in this pass |

## Official criteria (19 indicators)

| Criterion | Max | Highlights |
|-----------|-----|------------|
| A | 20 | `kra4-a-member` |
| B | 60 | Education, training, papers; sub-caps |
| C | 20 | Institutional / local / national awards |
| D (bonus) | 20 | Per-year experience indicators |

## Next steps for full sign-off

1. Run isolated `[KRA4-QA]` script (mirror `kra3_unified_review_matrix_verify.py`) with QA faculty only.
2. Browser: Assigned Faculty → KRA IV → each criterion → review → Save Assessment / Approve on pending; edit assessment on approved/rejected.
3. Mobile: Professional Development → add accomplishment → upload PDF → OCR → submit → confirm reviewer summary points.
4. Admin: publish scoring version and confirm KRA IV indicators appear in official config editor.

## Known gaps / clarifications

- International award points (Criterion C): not in catalog.
- Criterion D “newly hired” eligibility: confirm profile flags in validation when fields exist.
- Training duration rules (6h / 8h virtual): validate via `eventDurationHours` when captured on forms.
