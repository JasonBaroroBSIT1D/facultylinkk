# Proposed migration — Criterion B reviewer assessment (optional)

**Status:** Not required for the implemented feature. **Do not run** unless product owners want a first-class column instead of JSON.

## Current approach (shipped)

- Reviewer-proposed scores live in `Document.extracted_info.criterionBEvidenceBundle.reviewerProposedAssessment`.
- Audit trail uses existing `audit_logs` rows (`action`: `Criterion B reviewer proposed assessment`).
- `Document.estimated_points`, `Document.verified_points`, and `Document.reviewer_score` are **not** updated by reviewer-proposed assessment.

## Optional future migration (additive only)

If a dedicated column is desired for reporting:

```sql
-- Example only — NOT APPLIED
ALTER TABLE documents
  ADD COLUMN IF NOT EXISTS criterion_b_reviewer_proposed_points NUMERIC(10,2),
  ADD COLUMN IF NOT EXISTS criterion_b_reviewer_proposed_justification TEXT,
  ADD COLUMN IF NOT EXISTS criterion_b_reviewer_proposed_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS criterion_b_reviewer_proposed_by_user_id INTEGER REFERENCES users(id);
```

Backfill would copy from `extracted_info` JSON; dual-write could run during a transition period.

**Approval required** before executing any SQL migration in shared environments.
