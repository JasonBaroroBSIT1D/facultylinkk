"""Preserve Criterion B JSON on ``Document.extracted_info`` across OCR and other merges."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

BUNDLE_EXTRACTED_KEY = "criterionBEvidenceBundle"
LINK_EXTRACTED_KEY = "criterionBEvidenceLink"

CRITERION_B_PRESERVED_TOP_LEVEL_KEYS: tuple[str, ...] = (
    BUNDLE_EXTRACTED_KEY,
    LINK_EXTRACTED_KEY,
)

_BUNDLE_SCALAR_FIELDS: tuple[str, ...] = (
    "version",
    "claimType",
    "claimRole",
    "materialTitle",
    "materialType",
    "annexRowId",
    "indicatorId",
    "authorship",
    "contributionPercent",
    "specializationAligned",
    "completeSetDeclared",
    "programName",
    "programDevelopmentKind",
    "facultyRole",
    "contributionDescription",
    "committeeName",
    "validationStatus",
    "reviewerRemarks",
    "reviewerDisqualificationConfirmed",
    "rrpaCopcApplicability",
    "rrpaCopcApplicabilityNote",
)


def _merge_checklist_entries(
    preserved: dict[str, Any],
    incoming: dict[str, Any],
) -> dict[str, Any]:
    merged = deepcopy(incoming)
    for slot_id, old_entry in preserved.items():
        if not isinstance(old_entry, dict):
            continue
        new_entry = merged.get(slot_id)
        if not isinstance(new_entry, dict):
            merged[slot_id] = deepcopy(old_entry)
            continue
        if old_entry.get("documentId") and not new_entry.get("documentId"):
            merged[slot_id] = deepcopy(old_entry)
            continue
        if old_entry.get("status") == "verified" and new_entry.get("status") != "verified":
            merged[slot_id] = deepcopy(old_entry)
    return merged


def merge_criterion_b_evidence_bundles(
    preserved: dict[str, Any] | None,
    incoming: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Prefer linked checklist + reviewer state from ``preserved`` when ``incoming`` dropped them."""
    if not isinstance(preserved, dict):
        return deepcopy(incoming) if isinstance(incoming, dict) else None
    if not isinstance(incoming, dict):
        return deepcopy(preserved)
    merged = deepcopy(incoming)
    for field in _BUNDLE_SCALAR_FIELDS:
        if preserved.get(field) is not None and merged.get(field) in (None, ""):
            merged[field] = preserved[field]
    old_cl = preserved.get("checklist")
    new_cl = merged.get("checklist")
    if isinstance(old_cl, dict):
        if isinstance(new_cl, dict):
            merged["checklist"] = _merge_checklist_entries(old_cl, new_cl)
        else:
            merged["checklist"] = deepcopy(old_cl)
    old_ids = preserved.get("supportingDocumentIds")
    new_ids = merged.get("supportingDocumentIds")
    if isinstance(old_ids, list):
        combined = list(new_ids) if isinstance(new_ids, list) else []
        for doc_id in old_ids:
            if doc_id and doc_id not in combined:
                combined.append(doc_id)
        merged["supportingDocumentIds"] = combined
    decision_old = preserved.get("rrpaCopcApplicabilityDecision")
    decision_new = merged.get("rrpaCopcApplicabilityDecision")
    if isinstance(decision_old, dict) and not isinstance(decision_new, dict):
        merged["rrpaCopcApplicabilityDecision"] = deepcopy(decision_old)
    assess_old = preserved.get("reviewerProposedAssessment")
    assess_new = merged.get("reviewerProposedAssessment")
    if isinstance(assess_old, dict) and not isinstance(assess_new, dict):
        merged["reviewerProposedAssessment"] = deepcopy(assess_old)
    return merged


def preserve_criterion_b_extracted_info(
    *,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Merge ``after`` onto ``before`` without dropping Criterion B bundle/link payloads.

    Used defensively when OCR or other pipelines rewrite ``extracted_info``.
    """
    base = dict(before or {})
    updated = dict(after or {})
    merged = {**base, **updated}
    for key in CRITERION_B_PRESERVED_TOP_LEVEL_KEYS:
        if key == BUNDLE_EXTRACTED_KEY:
            merged[key] = merge_criterion_b_evidence_bundles(base.get(key), updated.get(key))
        elif key in base and base.get(key) is not None:
            if key not in updated or updated.get(key) is None:
                merged[key] = deepcopy(base[key])
            elif isinstance(base[key], dict) and isinstance(updated.get(key), dict):
                merged[key] = {**deepcopy(base[key]), **updated[key]}
    return merged


def snapshot_criterion_b_extracted_fields(info: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(info, dict):
        return {}
    out: dict[str, Any] = {}
    for key in CRITERION_B_PRESERVED_TOP_LEVEL_KEYS:
        if key in info and info[key] is not None:
            out[key] = deepcopy(info[key])
    return out
