# KRA I Criterion B — academic program evidence (Phase 2c)

Reference: **DBM–CHED JC 01, s. 2026** §14, Annex A §2. Storage: **`documents.extracted_info`** JSON only (no migration in Phase 2c).

## Indicators

| Indicator ID | Faculty role | Points from published Admin config |
|--------------|--------------|--------------------------------------|
| `kra1-b-program-lead` | Lead | `settings.indicators[kra1-b-program-lead]` |
| `kra1-b-program-contributor` | Contributor | `settings.indicators[kra1-b-program-contributor]` |

Same JSON keys as Phase 2b: `criterionBEvidenceBundle`, `criterionBEvidenceLink`.

## Bundle (`claimType`: `academic_program`)

| Field | Description |
|-------|-------------|
| `programName` | Academic program name |
| `programDevelopmentKind` | `new_program` \| `substantial_revision` |
| `facultyRole` | `lead` \| `contributor` (must match indicator) |
| `contributionDescription` | Narrative of actual faculty contribution |
| `committeeName` | Optional; improves cross-KRA committee overlap warnings |
| `checklist` | Evidence slots (same entry shape as IM bundles) |
| `crossKraWarnings` | Reviewer-visible §35 / Extension Criterion D hints |
| `reviewerDisqualificationConfirmed` | Reviewer-only hard disqualification |

## Evidence checklist

**Mandatory (always):**

- `primary_contribution_document` (primary upload)
- `dean_contribution_certification`
- `academic_council_resolution`
- `governing_board_resolution`
- `implementation_evidence`

**Conditional:**

- New program: at least one of `feasibility_study`, `benchmarking_report`
- Substantial revision: `revised_curriculum_stakeholder_consultation`

**Conditional — RRPA/COPC (`rrpa_or_copc`, Annex A §2 item 5, JC doc p. 77):**

- Reviewer must record **`rrpaCopcApplicability`**: `unknown` | `applicable` | `not_applicable` (stored in `rrpaCopcApplicabilityDecision` with note and timestamp).
- **`applicable`**: linked RRPA or COPC must be reviewer-**verified** before `readyForScoring`.
- **`not_applicable`**: requires reviewer decision + **non-empty exemption note** (missing document alone is not an exemption).
- **`unknown`**: flags `rrpa_copc_applicability_undetermined`; blocks `readyForScoring`.

Reviewer PATCH may send `{ rrpaCopcApplicability, rrpaCopcApplicabilityNote }` without a checklist slot update.

**Optional / as applicable (not required for `valid` or `readyForScoring`):**

- `approved_program_outcomes`
- `curriculum_obe_mapping`

If an optional slot is **linked** but not reviewer-verified, validation may flag `optional_<slot>_reviewer_required` without blocking scoring readiness when optional slots are empty.

**Implementation evidence (`implementation_evidence`) — conservative retention (Phase 6A.1):**

- JC §14 point 1 requires programs to be “formally approved **and implemented**” (doc p. 10).
- Annex A §2 (p. 77) lists five evidence items and does **not** name a separate “implementation” upload.
- FacultyLink keeps **`implementation_evidence` mandatory** pending human policy sign-off; do not weaken without verified JC text.

OCR may hint `present_unverified` only; **`verified`** requires reviewer PATCH.

## Validation status

| Status | Meaning |
|--------|---------|
| `incomplete` | Missing metadata or required documents |
| `reviewer_required` | Documents present; reviewer must verify eligibility |
| `valid` | Reviewer verified mandatory slots |
| `invalid` | Confirmed disqualifier (e.g. role/indicator mismatch, reviewer disqualification) |

Missing evidence is **not** automatically `invalid`.

## Cross-KRA warnings (§35 Item 1)

`crossKraWarnings` on bundle GET and `criterionBEvidence` payloads when peers suggest:

- Extension **Criterion D** committee designation overlap (`kra3-d-inst-chair`, `kra3-d-inst-member`, `kra3-d-dept-chair`, `kra3-d-dept-member`)
- Same file hash claimed under another KRA/criterion
- Same program name under both lead and contributor indicators

Warnings use `confidence`: `uncertain` or `confirmed`. **Never auto-reject** a claim.

## REST API

Same routes as Phase 2b (`/criterion-b/evidence-bundle`, `/link-supporting`).

**Faculty PATCH** additionally accepts: `programName`, `programDevelopmentKind`, `contributionDescription`, `committeeName`.

**Reviewer PATCH** additionally accepts: `disqualificationConfirmed` (boolean).

Response includes `crossKraWarnings` at the payload root (in addition to `validation`).

## Scoring

Phase 2a `compute_criterion_b_indicator_points` remains available; rank simulation is **not** wired. Supporting linked documents return no independent points.

## Future migration (not applied)

See `CRITERION_B_EVIDENCE.md` — optional normalized claim tables. Stop for approval before Alembic.
