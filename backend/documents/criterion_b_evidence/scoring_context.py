"""API-facing Criterion B scoring labels (system vs guideline vs reviewer-proposed)."""

from __future__ import annotations

from typing import Any

from kra_configuration.criterion_b_scoring import (
    compute_criterion_b_indicator_points,
    published_base_points_for_annex_row,
    published_criterion_b_max,
)
from documents.scoring.criterion_b_simulation_adapter import (
    CRITERION_B_SIMULATION_ADAPTER_ENABLED,
)
from documents.scoring.document_evidence_points import effective_document_points
from documents.criterion_b_evidence.current_score import (
    guideline_verified_points_if_ready,
    published_base_for_display,
    resolve_criterion_b_current_score,
)
from documents.criterion_b_evidence.reviewer_assessment import assessment_from_bundle

from models import Document


def build_criterion_b_scoring_context(
    doc: Document,
    bundle: dict[str, Any] | None,
    validation: dict[str, Any] | None,
) -> dict[str, Any]:
    indicator_id = (doc.indicator_id or "").strip()
    bundle = bundle if isinstance(bundle, dict) else {}
    validation = validation if isinstance(validation, dict) else {}

    current = resolve_criterion_b_current_score(doc, bundle, validation)
    base = published_base_for_display(indicator_id)
    contrib = bundle.get("contributionPercent")
    ready = validation.get("readyForScoring") is True

    guideline_result = compute_criterion_b_indicator_points(
        indicator_id,
        contribution_percent=contrib,
        evidence_verified=ready,
    )
    guide_pts = guideline_verified_points_if_ready(
        indicator_id,
        bundle,
        validation,
    )

    proposed = assessment_from_bundle(bundle) or {}

    return {
        "systemEstimatePoints": current.system_estimate_points,
        "preservedAutomatedEstimatePoints": current.system_estimate_points,
        "systemEstimateNote": (
            "Automated estimate from uploads and OCR. This is not official verification."
        ),
        "guidelineCompliantVerifiedPoints": guide_pts
        if guide_pts is not None
        else (guideline_result.points if guideline_result.eligible else None),
        "guidelineCompliantNote": (
            "Points from published DBM–CHED rules when required evidence is reviewer-verified. "
            "Not overridden by reviewer professional assessment."
        ),
        "guidelineEligible": guideline_result.eligible,
        "guidelineReasons": list(guideline_result.reasons),
        "publishedBasePoints": base,
        "allowedReviewerAssessmentMaxPoints": current.allowed_reviewer_max_points,
        "criterionBMaxPoints": published_criterion_b_max(),
        "simulationAdapterEnabled": CRITERION_B_SIMULATION_ADAPTER_ENABLED,
        "reviewerProposedAssessment": {
            "points": proposed.get("points"),
            "justification": proposed.get("justification"),
            "updatedAt": proposed.get("updatedAt"),
            "reviewerDisplayName": proposed.get("reviewerDisplayName"),
        },
        "displayScore": {
            "label": current.label,
            "points": current.points,
            "source": current.source,
        },
        "currentScore": {
            "label": current.label,
            "points": current.points,
            "source": current.source,
        },
    }
