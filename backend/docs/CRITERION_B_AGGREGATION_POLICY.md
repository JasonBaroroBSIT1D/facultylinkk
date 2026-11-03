# Criterion B — aggregation & evidence policy (Phase 5A.1)

Reference document: **`backend/docs/2026-DBM-CHED-JC-01-Enhanced-Implementing-Guidelines-of-JC3-series-of-2022 (1).pdf`** (DBM–CHED Joint Circular No. 01, s. 2026).

## PDF access limitation

The bundled PDF is **image-only** (no extractable text via PyMuPDF/pypdf in this environment). **Exact page numbers for §§11–14 could not be machine-verified** in Phase 5A.1. Structural mapping below follows:

- In-repo **`kra_configuration/criterion_b_annex.py`** `annex_reference` strings (Annex A §1.1–§1.4, §2.1–§2.2).
- **`CRITERION_B_EVIDENCE.md`** / **`CRITERION_B_PROGRAM_EVIDENCE.md`** (Phase 1–2c audits).
- Published Admin **`kraSettings`** (criterion B max 30, per-row base points on **sole/base** indicator IDs).

**Human verification:** Compare §§11–14 and Annex A table to this document before production certification.

---

## Task 1 — Annex row & duplicate claims (engineering policy)

| Question | Finding | Implementation |
|----------|---------|----------------|
| Multiple **distinct** instructional materials under the same Annex A row (e.g. two modules)? | JC structure treats categories (textbook, module, manual, multimedia) as separate line items; Criterion B **criterion max 30** applies to the **combined** B score. FacultyLink interprets **each distinct primary file / title** as a separate output when evidence is bundle-ready. | **Allowed** — each unique `deduplication_key` on the same `annex_row_id` may contribute; sum capped at 30. |
| Sole vs co-author on the **same material**? | Sole and co rows share one official **base** point allocation per Annex A line; co score is base × Annex C %. They are **not** independent full bases for one work. | **One credit per material** — keys `im:hash:{primary_file_hash}` (fallback: normalized title). Sole + co on **same hash** → **max** points, not sum. |
| Same material, duplicate claims / re-uploads? | Same as above. | Same dedupe key → max within `(annex_row_id, dedupe_key)`. |
| Was **best-per-indicator-id** correct? | **No** for simulation — it collapsed multiple distinct textbooks (same `kra1-b-textbook-sole` indicator) into one score. | Replaced for simulation by **`aggregate_eligible_points_by_output`** when `dedupe_keys` are supplied. Legacy best-per-indicator retained only when `dedupe_keys=None` (deprecated). |
| Same program lead + contributor? | Annex A §2.1 vs §2.2 are **separate rows** with separate published point entries; same program name may warrant reviewer warning, not automatic dedupe. | Keys `program:{normalized_name}:{indicatorId}`. |

**Uncertainty (do not invent):** Whether the circular caps **per Annex row per faculty** in addition to the **30** criterion cap (e.g. only one module line item ever) could not be confirmed from the image PDF. Current code applies **criterion-level 30 only** plus per-claim published base from Admin config.

---

## Task 2 — Academic program evidence

| Slot(s) | Classification |
|---------|----------------|
| `primary_contribution_document`, `dean_contribution_certification`, `academic_council_resolution`, `governing_board_resolution`, `implementation_evidence` | **Always mandatory** |
| `feasibility_study` **or** `benchmarking_report` | **Conditional** (new program — at least one) |
| `revised_curriculum_stakeholder_consultation` | **Conditional** (substantial revision) |
| `approved_program_outcomes`, `curriculum_obe_mapping` | **Optional** (“as applicable”, §14.3(a)iii–iv) |
| `rrpa_or_copc` | **Conditional** when reviewer marks applicability `applicable`; exemption via documented `not_applicable` decision (Annex A §2.5, p. 77) |

**Defect fixed:** Optional missing slots previously added `optional_*_pending` flags, forcing `reviewer_required` and blocking `readyForScoring`. Optional slots now appear in `checklistSummary` only; if linked but unverified, `optional_*_reviewer_required` may still apply.

---

## Module reference

| Module | Role |
|--------|------|
| `kra_configuration/criterion_b_aggregation.py` | `deduplication_key_for_bundle`, `aggregate_eligible_points_by_output` |
| `kra_configuration/criterion_b_scoring.py` | `aggregate_criterion_b_from_results(..., dedupe_keys=)` |
| `documents/criterion_b_evidence/program_validation.py` | Optional slot fix |
| `documents/scoring/criterion_b_simulation_adapter.py` | Supplies dedupe keys (adapter still **disabled**) |

---

## Phase 5B

Do not enable `CRITERION_B_SIMULATION_ADAPTER_ENABLED` until stakeholders sign off on PDF page verification and any per-row cap clarification.
