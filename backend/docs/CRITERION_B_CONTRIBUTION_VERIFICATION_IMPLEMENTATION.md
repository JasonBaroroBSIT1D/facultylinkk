# Criterion B — Annex C contribution verification (implementation report)

**Date:** 2026-11-03  
**Guideline basis:** 2026 DBM–CHED Joint Circular No. 01 (Criterion B §11–13; collaborative IM §12(4); Annex C)  
**Scoring formula:** unchanged — `published_base × (contributionPercent / 100)`; reviewer assessment capped by published max for that share.

---

## 1. Files inspected and modified

### Backend (new / core)

| File | Role |
|------|------|
| `documents/criterion_b_evidence/contribution_confirmation.py` | **New.** Confirmation state on bundle JSON (`contributionConfirmation`), OCR advisory hint, reviewer confirm/clarify, assessment gate, validation blockers, API view builder. |
| `documents/criterion_b_evidence/reviewer_assessment.py` | Calls `assert_can_save_reviewer_assessment()` before saving co-author assessments. |
| `documents/criterion_b_evidence/service.py` | PATCH: `confirmContributionPercentage`, `confirmedContributionPercent`, clarification flags; `bundle_api_payload()` exposes `contributionVerification`; validation augmented with contribution blockers. |
| `documents/routes.py` | Stable HTTP error codes for contribution failures; PATCH response includes `contributionVerification` + `scoring`. |

### Backend (unchanged scoring / aggregation)

| File | Note |
|------|------|
| `kra_configuration/criterion_b_scoring.py` | No formula changes. |
| `documents/criterion_b_evidence/current_score.py` | Uses existing reviewer assessment + contribution percent. |
| `documents/scoring/criterion_b_simulation_adapter.py` | **Still activated** when env flag set; no silent removal of legacy points. |
| `faculty/kra_document_aggregate.py` | No change to cap logic (Criterion B 30, KRA I 100). |

### Reviewer Web

| File | Role |
|------|------|
| `web/js/criterion-b-simple-review.js` | **Contribution Verification** panel on Annex C step; confirm action via PATCH. |
| `web/js/criterion-b-workspace-ui.js` | Readiness row for co-author Annex C confirmation. |
| `web/tests/contribution-verification-readiness.test.js` | Node test for readiness rows. |

### Faculty Mobile

| File | Role |
|------|------|
| `mobile/lib/data/criterion_b_evidence.dart` | `CriterionBContributionVerification`, faculty-facing labels. |
| `mobile/lib/widgets/criterion_b_evidence_panel.dart` | Status + plain-language detail for co-author claims. |
| `mobile/test/contribution_verification_display_test.dart` | Label mapping tests. |

### Tests (backend)

| File | Role |
|------|------|
| `tests/documents/test_contribution_confirmation.py` | Unit tests for confirmation, OCR advisory, legacy, cap rejection. |
| `tests/documents/test_criterion_b_current_score_integration.py` | Co-author flows now confirm contribution before new assessment. |
| `tests/staging/test_criterion_b_activation_scenarios.py` | Jason-like scenario uses pre-existing reviewer assessment (legacy path). |
| `tests/kra_configuration/test_criterion_b_aggregation_policy.py` | Adapter reason code tolerance (`evidence_not_verified` \| `evidence_not_ready_for_scoring`). |

---

## 2. Backend validation changes

- **Storage:** `criterionBEvidenceBundle.contributionConfirmation` (JSON on document row — **no Alembic migration**).
- **Statuses:** `not_confirmed`, `confirmed`, `mismatch`, `needs_clarification`, `legacy_grandfathered`.
- **OCR:** `suggest_contribution_percent_from_ocr()` — regex on OCR excerpt only; never writes bundle or auto-confirms.
- **Confirm API:** Reviewer must PATCH with `confirmContributionPercentage: true` and `confirmedContributionPercent` after Annex C slot has a linked document. Mismatch vs recorded `contributionPercent` sets `mismatch` and requires `contributionClarificationReason` (correction workflow); assessment save blocked while unresolved.
- **Assessment save:** Co-author indicators require either:
  - `confirmed` with recorded % = confirmed %, or
  - `legacy_grandfathered` with **unchanged** points + justification (historical Jason-like records).
- **Validation payload:** `augment_validation_with_contribution_blockers()` adds `contribution_confirmation_pending` / legacy flag messages without changing `readyForScoring` semantics for grandfathered rows (advisory blocker text for legacy).

### Stable error codes (representative)

- `contribution_confirmation_required`
- `contribution_confirmation_required_for_assessment_change`
- `contribution_percent_mismatch_unresolved`
- `contribution_confirmation_incomplete`
- `annex_c_document_required`
- (existing) `reviewer_assessment_points_exceeds_published_max`

---

## 3. Reviewer Web changes

Within **Open Faculty Work → Check Files → Save Review**, on the Annex C step:

- **Contribution Verification:** recorded %, OCR suggestion (if any), advisory note, match status label, document preview context.
- **Action:** “Confirm Contribution Percentage” → PATCH with confirmed value.
- **Readiness:** co-author rows show Annex C contribution row as not OK until `confirmationStatus === 'confirmed'` (legacy shows OK with “Contribution Confirmation Required” messaging).

Mismatch copy: *“The recorded contribution percentage does not match the reviewed Annex C. Resolve the difference before finalizing the assessment.”* — no checkbox override.

---

## 4. Faculty Mobile changes

Co-author accomplishment details show:

| Backend status | Faculty label |
|----------------|---------------|
| `not_confirmed` / pending | Awaiting Contribution Verification |
| `confirmed` | Contribution Verified |
| `mismatch`, `needs_clarification` | Needs Correction |
| `legacy_grandfathered` | Contribution Confirmation Required (wording aligned with reviewer legacy state) |

No automatic change to faculty-recorded `contributionPercent`; correction uses existing document/resubmission flows.

---

## 5. Database migration requirements

**None required** for this feature. All confirmation fields live in existing `criterionBEvidenceBundle` JSON.

**Do not apply** any new migration without backup and explicit approval (none drafted for this task).

---

## 6. Legacy-record behavior (Jason `doc_64d33454ab0f` and similar)

**Preserved without automatic mutation:**

- Stored 50% contribution, 14-point reviewer assessment, synthetic Annex C, prior verification history.

**Detection:** If a co-author bundle has a completed `reviewerProposedAssessment` (points + justification ≥ min length) and **no** `contributionConfirmation` record → `legacy_grandfathered`.

**UI/API label:** “Contribution Confirmation Required” — **not** presented as newly Annex C–verified.

### KRA / aggregation policy (explicit — no silent behavior change)

| Option | Behavior | Impact |
|--------|----------|--------|
| **A (implemented)** | Legacy assessments **continue to count** in simulation/KRA when other gates pass (verified evidence, adapter on, current score resolver). New/changed assessments require confirmation. | Jason’s 14 points remain in totals until a reviewer **changes** assessment or faculty corrects contribution via authorized workflow. Lowest risk to historical data. |
| B (not implemented) | Block KRA credit until confirmation on all co-author rows. | Would drop Jason from active totals until manual confirm — **rejected** per Task 6. |
| C (not implemented) | Auto-insert `confirmed` from OCR or recorded %. | **Rejected** — violates reviewer-control and OCR advisory-only rules. |

**Recommendation:** On next reviewer session for Jason’s row, use **Confirm Contribution Percentage** after reading Annex C; until then, treat as historical assessment with advisory legacy flag.

---

## 7. Automated test results

```text
backend: pytest tests/documents tests/kra_configuration tests/faculty/test_rank_simulation_criterion_b_wiring.py tests/staging/test_criterion_b_activation_scenarios.py -k "criterion_b or contribution"  → 118 passed
web:     node web/tests/contribution-verification-readiness.test.js  → passed
mobile:  flutter test test/contribution_verification_display_test.dart  → passed
```

**Coverage mapping (Task 8):**

| # | Scenario | Test location |
|---|----------|----------------|
| 1 | Matching recorded/confirmed | `test_matching_recorded_and_confirmed_allows_assessment` |
| 2 | Missing Annex C | `apply_contribution_confirmation` raises `annex_c_document_required` (module) |
| 3 | Missing recorded % | `contribution_percent_required_on_claim` |
| 4 | Missing reviewer confirmation | `test_missing_confirmation_blocks_new_assessment` |
| 5–6 | OCR mismatch / ambiguous | `test_ocr_*`, view flags |
| 7 | Verified doc, no confirm | `test_verified_annex_without_confirmation_flagged_in_view` |
| 8 | Assessment > cap | `test_assessment_exceeding_cap_rejected` (19 vs 18 max @ 60%) |
| 9 | Justification | existing `test_criterion_b_reviewer_assessment.py` |
| 10 | Historical compatibility | `test_legacy_grandfather_*`, staging Jason-like |
| 11–13 | Supporting docs, B max 30, KRA 100 | existing criterion B / adapter / aggregation tests |
| 14 | Rank simulation | `test_rank_simulation_criterion_b_wiring.py`, integration tests |
| 15–16 | Web readiness / mobile labels | web + Flutter tests above |

---

## 8. Remaining risks

1. **Live Jason row:** Legacy flag appears until reviewer confirms; UI must not imply Annex C was formally reconciled pre-change.
2. **OCR quality:** False suggestions possible; reviewers must rely on document preview, not OCR alone.
3. **Mismatch without faculty correction:** Assessment changes remain blocked until recorded % or Annex C evidence is aligned via existing correction workflow.
4. **Partial UI verification:** Full browser reviewer JWT flow not automated in CI; manual checklist below.
5. **Env flag:** Criterion B simulation adapter remains env-controlled; contribution gate is independent of adapter but both affect displayed KRA totals.

---

## 9. Manual testing checklist

- [ ] Reviewer: open co-author textbook accomplishment → Annex C step shows Contribution Verification panel.
- [ ] Confirm 60% on sample with recorded 60% → status **Confirmed**; save assessment 17/18 with justification succeeds; 19 fails.
- [ ] Confirm 40% with recorded 50% → **Mismatch**; assessment save blocked; message shown on Web.
- [ ] Legacy row (existing assessment, no confirmation): re-save same 14 pts → succeeds; change to 15 → blocked until confirm.
- [ ] Faculty mobile: co-author detail shows correct status labels for each backend status.
- [ ] Jason `doc_64d33454ab0f`: 50%, 14 pts, KRA total unchanged; status shows legacy/confirmation required, not “Contribution Verified”.
- [ ] Sole-author indicator: no contribution panel; assessment unchanged behavior.
- [ ] Rank simulation screen: Criterion B subtotal consistent with canonical current score after confirm + assess.

---

## Approval gates (not done in this delivery)

- **No** PostgreSQL reset, **no** migration applied, **no** live edits to Jason’s bundle.
- **No** change to `CRITERION_B_SIMULATION_ADAPTER_ENABLED` without explicit ops instruction.

If product later chooses **Option B** (withhold KRA credit until all co-author rows confirmed), that requires a separate approved change to `current_score` / adapter eligibility — out of scope for this enhancement.
