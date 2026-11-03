"""Persistence helpers for Criterion B evidence bundles (instructional materials + programs)."""

from __future__ import annotations

from typing import Any

from extensions import db
from models import Document

from kra_configuration.criterion_b_annex import (
    is_academic_program_indicator,
    is_instructional_material_indicator,
)
from documents.criterion_b_evidence.bundle import (
    apply_slot_link,
    build_initial_bundle,
    bundle_from_document,
    is_supporting_evidence_document,
    link_from_document,
    persist_bundle,
    persist_link,
)
from documents.criterion_b_evidence.checklist import required_slots
from documents.criterion_b_evidence.cross_kra import assess_cross_kra_warnings
from documents.criterion_b_evidence.program_bundle import (
    build_initial_program_bundle,
    is_academic_program_bundle,
)
from documents.criterion_b_evidence.program_applicability import (
    RRPA_APPLICABILITY_NOT_APPLICABLE,
    apply_rrpa_copc_applicability_decision,
)
from documents.criterion_b_evidence.program_checklist import (
    SLOT_RRPA_COPC,
    allowed_supporting_slots,
)
from documents.criterion_b_evidence.program_validation import validate_academic_program_bundle
from documents.criterion_b_evidence.validation import (
    detect_duplicate_supporting_hash,
    validate_instructional_material_bundle,
)
from documents.service import get_document, get_owned_document


class CriterionBEvidenceError(ValueError):
    def __init__(self, code: str, message: str = ""):
        super().__init__(message or code)
        self.code = code


def _validate_bundle(bundle: dict[str, Any] | None) -> dict[str, Any]:
    if is_academic_program_bundle(bundle):
        return validate_academic_program_bundle(bundle)
    return validate_instructional_material_bundle(bundle)


def _allowed_supporting_slots(bundle: dict[str, Any]) -> frozenset[str] | set[str]:
    if is_academic_program_bundle(bundle):
        return allowed_supporting_slots()
    return frozenset(
        required_slots(
            bundle.get("materialType") or "",
            authorship=bundle.get("authorship") or "sole",
        )
    )


def _existing_primary_with_bundle_for_indicator(
    faculty_profile_id: int,
    indicator_id: str,
    *,
    exclude_public_id: str | None = None,
) -> bool:
    """True when faculty already has a non-supporting Criterion B claim with an evidence bundle."""
    ind = (indicator_id or "").strip()
    if not ind:
        return False
    q = Document.query.filter_by(
        faculty_profile_id=faculty_profile_id,
        indicator_id=ind,
        criterion_id="kra1-b",
    )
    if exclude_public_id:
        q = q.filter(Document.public_id != exclude_public_id)
    for row in q:
        if getattr(row, "deleted_at", None) is not None:
            continue
        if is_supporting_evidence_document(row):
            continue
        if bundle_from_document(row):
            return True
    return False


def _apply_validation_to_bundle(
    bundle: dict[str, Any],
    *,
    peer_documents: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    validation = _validate_bundle(bundle)
    bundle["validationStatus"] = validation["validationStatus"]
    bundle["flags"] = validation["flags"]
    if is_academic_program_bundle(bundle):
        bundle["crossKraWarnings"] = assess_cross_kra_warnings(bundle, peer_documents)
    return validation


def peer_document_summaries(
    faculty_profile_id: int,
    *,
    exclude_public_id: str | None = None,
) -> list[dict[str, Any]]:
    """Read-only peer rows for cross-KRA warnings (does not modify data)."""
    query = Document.query.filter(
        Document.faculty_profile_id == faculty_profile_id,
        Document.deleted_at.is_(None),
    )
    if exclude_public_id:
        query = query.filter(Document.public_id != exclude_public_id)
    summaries: list[dict[str, Any]] = []
    for row in query.limit(500).all():
        info = row.extracted_info if isinstance(row.extracted_info, dict) else {}
        bundle = info.get("criterionBEvidenceBundle")
        program_name = None
        committee = None
        if isinstance(bundle, dict) and bundle.get("claimType") == "academic_program":
            program_name = bundle.get("programName")
            committee = bundle.get("committeeName")
        summaries.append(
            {
                "publicId": row.public_id,
                "indicatorId": row.indicator_id,
                "criterionId": row.criterion_id,
                "title": row.title,
                "fileHash": row.file_hash,
                "programName": program_name,
                "committeeName": committee,
            }
        )
    return summaries


def maybe_initialize_instructional_material_bundle(doc: Document) -> None:
    """After primary IM upload, attach an empty evidence bundle (JSON only)."""
    if not is_instructional_material_indicator(doc.indicator_id):
        return
    if is_supporting_evidence_document(doc):
        return
    if bundle_from_document(doc):
        return
    if _existing_primary_with_bundle_for_indicator(
        doc.faculty_profile_id,
        doc.indicator_id or "",
        exclude_public_id=doc.public_id,
    ):
        return
    bundle = build_initial_bundle(
        primary_document_id=doc.public_id,
        primary_file_hash=doc.file_hash,
        indicator_id=doc.indicator_id or "",
        material_title=doc.title or "",
    )
    persist_bundle(doc, bundle)


def maybe_initialize_academic_program_bundle(doc: Document) -> None:
    """After primary program claim upload, attach program evidence bundle (JSON only)."""
    if not is_academic_program_indicator(doc.indicator_id):
        return
    if is_supporting_evidence_document(doc):
        return
    if bundle_from_document(doc):
        return
    if _existing_primary_with_bundle_for_indicator(
        doc.faculty_profile_id,
        doc.indicator_id or "",
        exclude_public_id=doc.public_id,
    ):
        return
    bundle = build_initial_program_bundle(
        primary_document_id=doc.public_id,
        primary_file_hash=doc.file_hash,
        indicator_id=doc.indicator_id or "",
        program_name=doc.title or "",
    )
    persist_bundle(doc, bundle)


def maybe_initialize_criterion_b_bundle(doc: Document) -> None:
    maybe_initialize_instructional_material_bundle(doc)
    maybe_initialize_academic_program_bundle(doc)


def attach_supporting_upload_link(
    supporting: Document,
    *,
    primary_public_id: str,
    evidence_slot: str,
) -> Document:
    """Mark a newly uploaded file as supporting evidence for a primary claim."""
    primary = get_document(primary_public_id)
    if not primary:
        raise CriterionBEvidenceError("primary_not_found")
    db.session.refresh(primary)
    if primary.faculty_profile_id != supporting.faculty_profile_id:
        raise CriterionBEvidenceError("faculty_mismatch")
    bundle = bundle_from_document(primary)
    if not bundle:
        raise CriterionBEvidenceError("bundle_not_initialized")
    allowed = _allowed_supporting_slots(bundle)
    if evidence_slot not in allowed:
        raise CriterionBEvidenceError("invalid_evidence_slot")
    checklist = bundle.get("checklist") if isinstance(bundle.get("checklist"), dict) else {}
    slot_entry = checklist.get(evidence_slot) if isinstance(checklist, dict) else None
    if isinstance(slot_entry, dict) and slot_entry.get("documentId") == supporting.public_id:
        persist_link(
            supporting,
            {
                "role": "supporting",
                "primaryDocumentId": primary.public_id,
                "evidenceSlot": evidence_slot,
            },
        )
        supporting.criterion_id = primary.criterion_id
        supporting.kra_id = primary.kra_id
        supporting.indicator_id = primary.indicator_id
        return primary
    if detect_duplicate_supporting_hash(bundle, slot_id=evidence_slot, file_hash=supporting.file_hash):
        raise CriterionBEvidenceError("duplicate_supporting_slot")
    primary_slot = "primary_material" if not is_academic_program_bundle(bundle) else "primary_contribution_document"
    if evidence_slot != primary_slot and supporting.file_hash == primary.file_hash:
        raise CriterionBEvidenceError("duplicate_primary_hash")

    bundle = apply_slot_link(
        bundle,
        slot_id=evidence_slot,
        supporting_document_id=supporting.public_id,
        supporting_file_hash=supporting.file_hash,
    )
    peers = peer_document_summaries(
        primary.faculty_profile_id,
        exclude_public_id=primary.public_id,
    )
    _apply_validation_to_bundle(bundle, peer_documents=peers)
    persist_bundle(primary, bundle)

    persist_link(
        supporting,
        {
            "role": "supporting",
            "primaryDocumentId": primary.public_id,
            "evidenceSlot": evidence_slot,
        },
    )
    supporting.criterion_id = primary.criterion_id
    supporting.kra_id = primary.kra_id
    supporting.indicator_id = primary.indicator_id
    return primary


def link_existing_supporting_document(
    faculty_user,
    *,
    primary_public_id: str,
    supporting_public_id: str,
    evidence_slot: str,
) -> tuple[Document, dict[str, Any]]:
    primary = get_owned_document(primary_public_id, faculty_user)
    if not primary:
        raise CriterionBEvidenceError("primary_not_found")
    supporting = get_owned_document(supporting_public_id, faculty_user)
    if not supporting:
        raise CriterionBEvidenceError("supporting_not_found")
    if supporting.public_id == primary.public_id:
        raise CriterionBEvidenceError("cannot_link_self")
    attach_supporting_upload_link(supporting, primary_public_id=primary.public_id, evidence_slot=evidence_slot)
    db.session.commit()
    bundle = bundle_from_document(primary) or {}
    return primary, _validate_bundle(bundle)


def update_bundle_metadata(
    faculty_user,
    primary_public_id: str,
    payload: dict[str, Any],
) -> tuple[Document, dict[str, Any]]:
    primary = get_owned_document(primary_public_id, faculty_user)
    if not primary:
        raise CriterionBEvidenceError("primary_not_found")
    bundle = bundle_from_document(primary)
    if not bundle:
        raise CriterionBEvidenceError("bundle_not_initialized")

    if is_academic_program_bundle(bundle):
        if "programName" in payload:
            bundle["programName"] = str(payload.get("programName") or "").strip()
        if "programDevelopmentKind" in payload:
            bundle["programDevelopmentKind"] = payload.get("programDevelopmentKind")
        if "contributionDescription" in payload:
            bundle["contributionDescription"] = str(payload.get("contributionDescription") or "").strip()
        if "committeeName" in payload:
            bundle["committeeName"] = str(payload.get("committeeName") or "").strip()
    else:
        if "materialTitle" in payload:
            bundle["materialTitle"] = str(payload.get("materialTitle") or "").strip()
        if "contributionPercent" in payload:
            bundle["contributionPercent"] = payload.get("contributionPercent")
        if "completeSetDeclared" in payload:
            bundle["completeSetDeclared"] = bool(payload.get("completeSetDeclared"))
        if "specializationAligned" in payload:
            val = payload.get("specializationAligned")
            if val is None:
                bundle["specializationAligned"] = None
            else:
                bundle["specializationAligned"] = bool(val)

    peers = peer_document_summaries(
        primary.faculty_profile_id,
        exclude_public_id=primary.public_id,
    )
    validation = _apply_validation_to_bundle(bundle, peer_documents=peers)
    persist_bundle(primary, bundle)
    db.session.commit()
    return primary, validation


def reviewer_update_checklist_slot(
    reviewer_user,
    primary_public_id: str,
    *,
    slot_id: str | None,
    status: str | None,
    reviewer_note: str = "",
    remarks: str = "",
    disqualification_confirmed: bool | None = None,
    rrpa_copc_applicability: str | None = None,
    rrpa_copc_applicability_note: str = "",
    reviewer_assessment_points: float | int | str | None = None,
    reviewer_assessment_justification: str | None = None,
    specialization_aligned: bool | None = None,
    complete_set_declared: bool | None = None,
    confirm_contribution_percentage: bool | None = None,
    confirmed_contribution_percent: float | int | str | None = None,
    contribution_needs_clarification: bool | None = None,
    contribution_clarification_reason: str = "",
) -> tuple[Document, dict[str, Any]]:
    from documents.service import reviewer_can_access

    primary = get_document(primary_public_id)
    if not primary or not reviewer_can_access(reviewer_user, primary):
        raise CriterionBEvidenceError("forbidden")
    bundle = bundle_from_document(primary)
    if not bundle:
        raise CriterionBEvidenceError("bundle_not_initialized")

    if rrpa_copc_applicability is not None:
        if not is_academic_program_bundle(bundle):
            raise CriterionBEvidenceError("rrpa_applicability_program_only")
        try:
            apply_rrpa_copc_applicability_decision(
                bundle,
                status=str(rrpa_copc_applicability),
                note=rrpa_copc_applicability_note,
                decided_by_role="reviewer",
            )
        except ValueError as error:
            code = str(error)
            if code == "rrpa_copc_exemption_note_required":
                raise CriterionBEvidenceError("rrpa_copc_exemption_note_required") from error
            raise CriterionBEvidenceError("invalid_rrpa_copc_applicability") from error
        checklist = bundle.setdefault("checklist", {})
        rrpa_entry = checklist.get(SLOT_RRPA_COPC)
        if not isinstance(rrpa_entry, dict):
            from documents.criterion_b_evidence.bundle import empty_checklist_entry

            rrpa_entry = empty_checklist_entry()
        from documents.criterion_b_evidence.program_applicability import (
            rrpa_copc_applicability_from_bundle,
        )

        if rrpa_copc_applicability_from_bundle(bundle) == RRPA_APPLICABILITY_NOT_APPLICABLE:
            rrpa_entry["status"] = "not_applicable"
            rrpa_entry["ocrHintOnly"] = False
        checklist[SLOT_RRPA_COPC] = rrpa_entry

    if slot_id and status:
        checklist = bundle.setdefault("checklist", {})
        entry = checklist.get(slot_id) if isinstance(checklist.get(slot_id), dict) else {}
        if status == "verified":
            if not entry.get("documentId"):
                raise CriterionBEvidenceError("cannot_verify_empty_slot")
            entry["status"] = "verified"
            entry["ocrHintOnly"] = False
        elif status == "not_applicable":
            if slot_id != SLOT_RRPA_COPC:
                raise CriterionBEvidenceError("invalid_slot_status")
            entry["status"] = "not_applicable"
            entry["ocrHintOnly"] = False
        elif status in ("present_unverified", "reviewer_required", "missing"):
            entry["status"] = status
        else:
            raise CriterionBEvidenceError("invalid_slot_status")
        if reviewer_note:
            entry["reviewerNote"] = reviewer_note.strip()
        checklist[slot_id] = entry

    if remarks:
        bundle["reviewerRemarks"] = remarks.strip()
    if disqualification_confirmed is not None and is_academic_program_bundle(bundle):
        bundle["reviewerDisqualificationConfirmed"] = bool(disqualification_confirmed)
    if not is_academic_program_bundle(bundle):
        if specialization_aligned is not None:
            bundle["specializationAligned"] = bool(specialization_aligned)
        if complete_set_declared is not None:
            bundle["completeSetDeclared"] = bool(complete_set_declared)

    if confirm_contribution_percentage or contribution_needs_clarification:
        from documents.criterion_b_evidence.contribution_confirmation import (
            apply_contribution_confirmation,
            mark_needs_clarification,
        )

        if contribution_needs_clarification:
            try:
                mark_needs_clarification(
                    bundle,
                    reviewer_user_id=int(reviewer_user.id),
                    reviewer_display_name=getattr(reviewer_user, "full_name", "") or "",
                    clarification_reason=contribution_clarification_reason,
                )
            except ValueError as error:
                code = str(error)
                if code.startswith("contribution_"):
                    raise CriterionBEvidenceError(code) from error
                raise
        elif confirm_contribution_percentage:
            pct = confirmed_contribution_percent
            if pct is None:
                pct = bundle.get("contributionPercent")
            try:
                apply_contribution_confirmation(
                    bundle,
                    reviewer_user_id=int(reviewer_user.id),
                    reviewer_display_name=getattr(reviewer_user, "full_name", "") or "",
                    confirmed_percent=pct,
                    clarification_reason=contribution_clarification_reason,
                )
            except ValueError as error:
                code = str(error)
                if code.startswith("contribution_") or code.startswith("annex_"):
                    raise CriterionBEvidenceError(code) from error
                raise

    if reviewer_assessment_points is not None or (
        reviewer_assessment_justification is not None
        and str(reviewer_assessment_justification).strip()
    ):
        peers_pre = peer_document_summaries(
            primary.faculty_profile_id,
            exclude_public_id=primary.public_id,
        )
        validation_pre = _apply_validation_to_bundle(bundle, peer_documents=peers_pre)
        if not validation_pre.get("readyForScoring"):
            raise CriterionBEvidenceError("reviewer_assessment_not_ready")
        if reviewer_assessment_points is None:
            raise CriterionBEvidenceError("reviewer_assessment_points_required")
        from documents.criterion_b_evidence.reviewer_assessment import (
            apply_reviewer_proposed_assessment,
            assessment_from_bundle,
        )
        import json

        from models import AuditLog

        prior = assessment_from_bundle(bundle) or {}
        prior_points = prior.get("points")
        prior_just = prior.get("justification")
        try:
            record = apply_reviewer_proposed_assessment(
                bundle,
                points=reviewer_assessment_points,
                justification=reviewer_assessment_justification or "",
                reviewer_user_id=int(reviewer_user.id),
                reviewer_display_name=getattr(reviewer_user, "full_name", "") or "",
                indicator_id=(primary.indicator_id or "").strip(),
            )
        except ValueError as error:
            code = str(error)
            if code.startswith("reviewer_assessment_"):
                raise CriterionBEvidenceError(code) from error
            raise CriterionBEvidenceError("reviewer_assessment_points_invalid") from error
        if record.get("points") != prior_points or record.get("justification") != prior_just:
            db.session.add(
                AuditLog(
                    actor_user_id=int(reviewer_user.id),
                    action="Criterion B reviewer proposed assessment",
                    target_id=primary.public_id,
                    detail=json.dumps(
                        {
                            "documentId": primary.public_id,
                            "indicatorId": primary.indicator_id,
                            "priorPoints": prior_points,
                            "newPoints": record.get("points"),
                            "estimatedPoints": float(primary.estimated_points or 0),
                            "verifiedPoints": float(primary.verified_points)
                            if primary.verified_points is not None
                            else None,
                        },
                        ensure_ascii=False,
                    )[:4000],
                )
            )

    peers = peer_document_summaries(
        primary.faculty_profile_id,
        exclude_public_id=primary.public_id,
    )
    validation = _apply_validation_to_bundle(bundle, peer_documents=peers)
    persist_bundle(primary, bundle)
    db.session.commit()
    return primary, validation


def bundle_api_payload(doc: Document) -> dict[str, Any]:
    bundle = bundle_from_document(doc)
    peers = peer_document_summaries(
        doc.faculty_profile_id,
        exclude_public_id=doc.public_id,
    )
    validation = _validate_bundle(bundle)
    indicator_id = (doc.indicator_id or "").strip()
    from documents.criterion_b_evidence.contribution_confirmation import (
        augment_validation_with_contribution_blockers,
        build_contribution_verification_view,
    )
    from documents.criterion_b_evidence.checklist import SLOT_ANNEX_C_CONTRIBUTION

    validation = augment_validation_with_contribution_blockers(
        validation,
        bundle if isinstance(bundle, dict) else None,
        indicator_id=indicator_id,
    )
    annex_info = None
    faculty_name = None
    if isinstance(bundle, dict) and doc.faculty_profile and doc.faculty_profile.user:
        faculty_name = doc.faculty_profile.user.full_name
        checklist = bundle.get("checklist") if isinstance(bundle.get("checklist"), dict) else {}
        annex_entry = checklist.get(SLOT_ANNEX_C_CONTRIBUTION)
        if isinstance(annex_entry, dict) and annex_entry.get("documentId"):
            annex_doc = get_document(str(annex_entry["documentId"]))
            if annex_doc and isinstance(annex_doc.extracted_info, dict):
                annex_info = annex_doc.extracted_info
    contribution_verification = build_contribution_verification_view(
        bundle if isinstance(bundle, dict) else None,
        indicator_id=indicator_id,
        annex_extracted_info=annex_info,
        faculty_name=faculty_name,
    )
    if isinstance(bundle, dict) and is_academic_program_bundle(bundle):
        cross = assess_cross_kra_warnings(bundle, peers)
    else:
        cross = []
    from documents.criterion_b_evidence.scoring_context import build_criterion_b_scoring_context

    return {
        "bundle": bundle,
        "validation": validation,
        "contributionVerification": contribution_verification,
        "crossKraWarnings": cross,
        "scoring": build_criterion_b_scoring_context(doc, bundle, validation),
        "isSupportingDocument": is_supporting_evidence_document(doc),
        "link": link_from_document(doc),
    }
