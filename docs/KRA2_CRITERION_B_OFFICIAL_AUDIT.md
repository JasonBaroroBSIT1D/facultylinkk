# KRA II Criterion B (Inventions) — official rules audit

Source: DBM–CHED Joint Circular No. 01, s. 2026 — **Sections 22–24**, Annex A pp. **81–84** (PDF).

Text extraction from the scanned PDF is unavailable; point values and annex references cross-check 
`kra2_indicator_pdf_verification.py` (visual annex verification). Evidence slot IDs are implemented in 
`backend/documents/kra2_evidence/kra2_b_evidence_slots.py` and aligned to catalog `evidenceHints`.

## Policy rules (Sections 22–24)

| Rule | PDF reference | Implementation |
|---|---|---|
| Criterion B maximum 100 points | p. 17, 81 | `aggregate_kra2_criterion_from_documents` |
| Patent acceptance 10 / publication 20 / grant 80 | p. 81 | Published Admin indicator points |
| **Highest patent stage only** (same invention) | **Sec. 23.1.f, p. 18** | `patent_deduplication.apply_patent_highest_stage_only` |
| Patent + commercialization may both credit (same period) | p. 20 | Separate indicators; no cross-family dedup |
| Co-inventor / co-developer contribution (Annex F/G/H) | pp. 18–19 | `declaredContributionPercent` + contribution certificate slot |
| Commercialization sub-caps (local 20, international 30) | p. 82 | `groupMax` on `kra2-b-comm-local` / `kra2-b-comm-intl` |
| OCR advisory only; reviewer verifies | Sec. 23 (general) | Bundle validation + slot verification statuses |

## Scoring matrix (18 indicators)

| Indicator | Official base | Group / output cap | Configured | PDF status | Annex ref | Required evidence slots |
|---|---:|---:|---:|---|---|---|
| `kra2-b-patent-a-sole` | 10 | 10.0 | 10.0 / 10.0 | VERIFIED_POINTS | B.1.1 Patent A | `primary_output, invention_photo, president_special_order` |
| `kra2-b-patent-a-co` | 10 | 10.0 | 10.0 / 10.0 | PARTIAL | B.1.1 + Annex F | `primary_output, contribution_certificate` |
| `kra2-b-patent-p-sole` | 20 | 20.0 | 20.0 / 20.0 | VERIFIED_POINTS | B.1.1 Patent P | `primary_output, invention_photo, president_special_order` |
| `kra2-b-patent-p-co` | 20 | 20.0 | 20.0 / 20.0 | PARTIAL | B.1.1 + Annex F | `primary_output, contribution_certificate` |
| `kra2-b-patent-g-sole` | 80 | 80.0 | 80.0 / 80.0 | VERIFIED_POINTS | B.1.1 Patent G | `primary_output, invention_photo, president_special_order` |
| `kra2-b-patent-g-co` | 80 | 80.0 | 80.0 / 80.0 | PARTIAL | B.1.1 + Annex F | `primary_output, contribution_certificate` |
| `kra2-b-comm-local` | 5 | 20.0 | 5.0 / 20.0 | VERIFIED_POINTS | B.1.2.1 Local | `product_photo, patent_certificate, licensing_or_cpr_evidence, commercialization_proof, rd_itso_certification` |
| `kra2-b-comm-intl` | 10 | 30.0 | 10.0 / 30.0 | VERIFIED_POINTS | B.1.2.2 International | `product_photo, patent_certificate, licensing_or_cpr_evidence, commercialization_proof, rd_itso_certification` |
| `kra2-b-um-sole` | 10 | 10.0 | 10.0 / 10.0 | VERIFIED_POINTS | B.1.3.1 UM | `primary_output, invention_photo, president_special_order` |
| `kra2-b-um-co` | 10 | 10.0 | 10.0 / 10.0 | PARTIAL | B.1.3.1 + Annex F | `primary_output, contribution_certificate` |
| `kra2-b-id-sole` | 5 | 5.0 | 5.0 / 5.0 | VERIFIED_POINTS | B.1.3.2 ID | `primary_output, invention_photo, president_special_order` |
| `kra2-b-id-co` | 5 | 5.0 | 5.0 / 5.0 | PARTIAL | B.1.3.2 + Annex F | `primary_output, contribution_certificate` |
| `kra2-b-sw-new-sole` | 10 | 10.0 | 10.0 / 10.0 | VERIFIED_POINTS | B.2.1.1 New software | `president_special_order, project_summary, software_documentation, primary_output, utilization_certification` |
| `kra2-b-sw-new-co` | 10 | 10.0 | 10.0 / 10.0 | PARTIAL | B.2.1.1 + Annex G | `president_special_order, project_summary, software_documentation, primary_output, utilization_certification, contribution_certificate` |
| `kra2-b-sw-upd-sole` | 4 | 4.0 | 4.0 / 4.0 | VERIFIED_POINTS | B.2.1.2 Updated software | `president_special_order, project_summary, primary_output, utilization_certification, software_update_description` |
| `kra2-b-sw-upd-co` | 4 | 4.0 | 4.0 / 4.0 | PARTIAL | B.2.1.2 + Annex G | `president_special_order, project_summary, primary_output, utilization_certification, software_update_description, contribution_certificate` |
| `kra2-b-variety-sole` | 10 | 10.0 | 10.0 / 10.0 | VERIFIED_POINTS | B.2.2 Variety/breed/strain | `president_special_order, registration_deposit_evidence` |
| `kra2-b-variety-co` | 10 | 10.0 | 10.0 / 10.0 | PARTIAL | B.2.2 + Annex H | `registration_deposit_evidence, contribution_certificate` |

## Discrepancies vs pre-audit implementation

| Area | Before | After |
|---|---|---|
| Evidence checklist | `primary_output` (+ Annex D cert for co only) | Annex A multi-slot checklists per indicator family |
| Faculty mobile slot list | Generic primary + contribution | Matches backend `criterion_b_required_slots` |
| Reviewer web slot list | Generic primary + contribution | Uses API `requiredEvidenceSlots` + B catalog fallback |
| `kra2-b-variety-sole` catalog hints | Corrupted placeholder | Restored from Annex B.2.2 |

## Unverified / reviewer-gated (not machine-scored)

- Whether commercialization proof meets “reputable” or ITSO policy thresholds.
- Substantial functionality test for updated software (qualitative).
- International commercialization jurisdiction details.

## Configuration versioning

No published scoring version overwrite. Existing approved bundles retain locked configuration; 
new submissions expand checklist slots non-destructively via `ensure_checklist_slots`.

**Point values:** Catalog matches annex base points for all 18 Criterion B indicators.