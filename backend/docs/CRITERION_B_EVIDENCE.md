# KRA I Criterion B — instructional materials evidence bundles (Phase 2b)

Academic program claims (Phase 2c): see **`CRITERION_B_PROGRAM_EVIDENCE.md`**.

Storage: **`documents.extracted_info`** JSON only (no migration applied in Phase 2b).

## Keys

| Key | Document | Purpose |
|-----|----------|---------|
| `criterionBEvidenceBundle` | Primary IM claim | Bundle metadata + checklist |
| `criterionBEvidenceLink` | Supporting upload | `{ role, primaryDocumentId, evidenceSlot }` |

Supporting documents **do not** receive separate simulation points (`document_evidence_points` returns `None`).

## Bundle fields (primary)

| Field | Description |
|-------|-------------|
| `materialTitle` | Title of the instructional material |
| `materialType` | `textbook` \| `module` \| `instructional_manual` \| `multimedia` |
| `authorship` | `sole` \| `co` (from indicator ID) |
| `contributionPercent` | Required for co-author indicators (0–100) |
| `completeSetDeclared` | Faculty attestation for module/manual complete set |
| `specializationAligned` | `null` until reviewer/faculty confirms alignment |
| `checklist` | Map of slot → `{ status, documentId, fileHash, reviewerNote, ocrHintOnly }` |
| `validationStatus` | `incomplete` \| `reviewer_required` \| `valid` \| `invalid` |
| `reviewerRemarks` | Reviewer notes |

## Evidence slots (Annex A + §§12–13)

| Slot ID | Applies to |
|---------|------------|
| `primary_material` | All (primary upload) |
| `imdc_evaluation_approval` | All |
| `approved_syllabus` | All |
| `library_certification` | All |
| `annex_c_contribution` | Co-author claims |
| `complete_set_attestation` | Module, manual |
| `originality_proof` | Multimedia |
| `pedagogical_validity_proof` | Multimedia |

OCR may set `present_unverified` only; **`verified`** requires reviewer PATCH.

## REST API (no UI in Phase 2b)

### Faculty

| Method | Path | Body / form |
|--------|------|-------------|
| POST | `/api/faculty/me/documents` | Optional `bundlePrimaryId` + `evidenceSlot` for supporting upload |
| GET | `/api/faculty/me/documents/:id/criterion-b/evidence-bundle` | — |
| PATCH | `/api/faculty/me/documents/:id/criterion-b/evidence-bundle` | `materialTitle`, `contributionPercent`, `completeSetDeclared`, `specializationAligned` |
| POST | `/api/faculty/me/documents/:id/criterion-b/link-supporting` | `{ supportingDocumentId, evidenceSlot }` |

### Reviewer

| Method | Path | Body |
|--------|------|------|
| GET | `/api/reviewer/documents/:id/criterion-b/evidence-bundle` | — |
| PATCH | `/api/reviewer/documents/:id/criterion-b/evidence-bundle` | `{ evidenceSlot, status, reviewerNote?, remarks? }` or `{ rrpaCopcApplicability, rrpaCopcApplicabilityNote?, remarks? }` for academic programs — `status`: `verified`, `present_unverified`, `reviewer_required`, `missing`, `not_applicable` (RRPA slot only). Optional `{ reviewerAssessmentPoints, reviewerAssessmentJustification, remarks? }` stores **reviewer-proposed** assessment in `bundle.reviewerProposedAssessment` (does not overwrite `estimated_points` or `verified_points`). |
| GET (faculty/reviewer) | same bundle routes | Response includes `scoring`: system estimate, guideline-compliant verified points, and `reviewerProposedAssessment`. |

Document list/detail payloads include **`criterionBEvidence`** when `criterionId === kra1-b`.

## Scoring integration

Phase 2a helpers (`compute_criterion_b_indicator_points`) are **not** wired to rank simulation. When integrated (later), use `validation.readyForScoring` and reviewer-verified checklist only.

## Future migration proposal (not applied)

Optional normalized tables for analytics:

- `criterion_b_claims (id, primary_document_id, faculty_profile_id, …)`
- `criterion_b_evidence_links (claim_id, document_id, slot_id, …)`

Stop and review SQL before any Alembic revision against production.
