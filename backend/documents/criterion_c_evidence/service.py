"""Criterion C evidence bundles — research advising and mentorship accomplishments."""

from __future__ import annotations

from typing import Any

from extensions import db
from models import AuditLog, Document

from kra_configuration.criterion_c_annex import CRITERION_C_ID, indicator_metadata, is_criterion_c_indicator
from documents.criterion_c_evidence.bundle import (
    apply_slot_link,
    build_initial_bundle,
    bundle_from_document,
    is_supporting_evidence_document,
    link_from_document,
    persist_bundle,
    persist_link,
)
from documents.criterion_c_evidence.checklist import required_slots
from documents.criterion_c_evidence.deduplication import assess_peer_duplicates
from documents.criterion_c_evidence.reviewer_assessment import apply_reviewer_accomplishment_decision
from documents.criterion_c_evidence.scoring import estimated_points_for_bundle
from documents.criterion_c_evidence.validation import validate_criterion_c_bundle
from documents.service import get_document, get_owned_document


class CriterionCEvidenceError(ValueError):
    def __init__(self, code: str, message: str = ""):
        super().__init__(message or code)
        self.code = code


def _peer_bundles(
    faculty_profile_id: int,
    *,
    exclude_public_id: str | None = None,
) -> list[tuple[str, dict[str, Any]]]:
    q = Document.query.filter_by(
        faculty_profile_id=faculty_profile_id,
        criterion_id=CRITERION_C_ID,
    ).filter(Document.deleted_at.is_(None))
    if exclude_public_id:
        q = q.filter(Document.public_id != exclude_public_id)
    rows: list[tuple[str, dict[str, Any]]] = []
    for doc in q.limit(500).all():
        if is_supporting_evidence_document(doc):
            continue
        bundle = bundle_from_document(doc)
        if bundle:
            rows.append((doc.public_id, bundle))
    return rows


def _apply_validation_to_bundle(
    bundle: dict[str, Any],
    *,
    faculty_profile_id: int,
    public_id: str,
) -> dict[str, Any]:
    peers = _peer_bundles(faculty_profile_id, exclude_public_id=public_id)
    dup_flags, policy_flags = assess_peer_duplicates(
        bundle,
        faculty_profile_id=faculty_profile_id,
        peer_bundles=peers,
        self_public_id=public_id,
    )
    bundle["duplicateFlags"] = dup_flags
    bundle["policyFlags"] = policy_flags
    validation = validate_criterion_c_bundle(bundle)
    bundle["validationStatus"] = validation["validationStatus"]
    bundle["flags"] = validation["flags"]
    return validation


def maybe_initialize_criterion_c_bundle(doc: Document) -> None:
    if (doc.criterion_id or "").strip() != CRITERION_C_ID:
        return
    if not is_criterion_c_indicator(doc.indicator_id):
        return
    if is_supporting_evidence_document(doc):
        return
    if bundle_from_document(doc):
        return
    meta_pre = indicator_metadata(doc.indicator_id or "") if is_criterion_c_indicator(doc.indicator_id) else {}
    service_category = (meta_pre.get("serviceCategory") or "research").strip().lower()
    initial_title = ""
    if service_category != "research":
        initial_title = (doc.title or "").strip()
    bundle = build_initial_bundle(
        primary_document_id=doc.public_id,
        primary_file_hash=doc.file_hash,
        indicator_id=doc.indicator_id or "",
        project_title=initial_title,
    )
    if service_category == "research":
        from documents.criterion_c_evidence.ocr_research import link_primary_document_as_approval_sheet

        bundle = link_primary_document_as_approval_sheet(doc, bundle)
        bundle["researchMetadataWorkflow"] = "ocr_first"
    _apply_validation_to_bundle(
        bundle,
        faculty_profile_id=doc.faculty_profile_id,
        public_id=doc.public_id,
    )
    persist_bundle(doc, bundle)


def attach_supporting_upload_link(
    supporting: Document,
    *,
    primary_public_id: str,
    evidence_slot: str,
) -> Document:
    primary = get_document(primary_public_id)
    if not primary:
        raise CriterionCEvidenceError("primary_not_found")
    db.session.refresh(primary)
    if primary.faculty_profile_id != supporting.faculty_profile_id:
        raise CriterionCEvidenceError("faculty_mismatch")
    bundle = bundle_from_document(primary)
    if not bundle:
        raise CriterionCEvidenceError("bundle_not_initialized")
    service_category = (bundle.get("serviceCategory") or "research").strip().lower()
    allowed = frozenset(required_slots(service_category=service_category))
    if evidence_slot not in allowed:
        raise CriterionCEvidenceError("invalid_evidence_slot")

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

    if supporting.file_hash and supporting.file_hash == primary.file_hash:
        raise CriterionCEvidenceError("duplicate_primary_hash")

    bundle = apply_slot_link(
        bundle,
        slot_id=evidence_slot,
        supporting_document_id=supporting.public_id,
        supporting_file_hash=supporting.file_hash,
    )
    _apply_validation_to_bundle(
        bundle,
        faculty_profile_id=primary.faculty_profile_id,
        public_id=primary.public_id,
    )
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
        raise CriterionCEvidenceError("primary_not_found")
    supporting = get_owned_document(supporting_public_id, faculty_user)
    if not supporting:
        raise CriterionCEvidenceError("supporting_not_found")
    if supporting.public_id == primary.public_id:
        raise CriterionCEvidenceError("cannot_link_self")
    attach_supporting_upload_link(
        supporting,
        primary_public_id=primary.public_id,
        evidence_slot=evidence_slot,
    )
    db.session.commit()
    bundle = bundle_from_document(primary) or {}
    return primary, validate_criterion_c_bundle(bundle)


_METADATA_FIELD_MAP = {
    "projectTitle": "projectTitle",
    "studentNames": "studentNames",
    "studentGroupLabel": "studentGroupLabel",
    "academicYear": "academicYear",
    "completionDate": "completionDate",
}


def _apply_bundle_metadata_fields(
    bundle: dict[str, Any],
    payload: dict[str, Any],
    *,
    actor: str = "faculty",
) -> bool:
    """Apply metadata keys present in payload. Returns True if any field changed."""
    from documents.criterion_c_evidence.research_metadata import is_unreliable_research_title

    confirmed = bundle.setdefault("metadataConfirmed", {})
    if not isinstance(confirmed, dict):
        confirmed = {}
        bundle["metadataConfirmed"] = confirmed
    per_field_confirmed = payload.get("metadataConfirmed")
    bulk_confirm = payload.get("confirmMetadata") is True
    changed = False
    for api_key, bundle_key in _METADATA_FIELD_MAP.items():
        if api_key not in payload:
            continue
        value = str(payload.get(api_key) or "").strip()
        if api_key == "projectTitle" and is_unreliable_research_title(value):
            value = ""
        if (bundle.get(bundle_key) or "").strip() != value:
            changed = True
        bundle[bundle_key] = value
        if actor == "reviewer":
            confirmed[bundle_key] = bool(value)
        elif bulk_confirm:
            confirmed[bundle_key] = True
        elif isinstance(per_field_confirmed, dict) and per_field_confirmed.get(bundle_key) is True:
            confirmed[bundle_key] = True
        elif api_key in payload:
            confirmed[bundle_key] = True
    if bulk_confirm and actor == "faculty":
        from documents.criterion_c_evidence.bundle import _utcnow_iso

        bundle["metadataFacultyConfirmedAt"] = _utcnow_iso()
    if actor == "reviewer" and changed:
        from documents.criterion_c_evidence.bundle import _utcnow_iso

        bundle["metadataReviewerConfirmedAt"] = _utcnow_iso()
    if "mentorship" in payload and isinstance(payload.get("mentorship"), dict):
        ment = bundle.setdefault("mentorship", {})
        for key in ("competitionName", "prizeLevel", "prizePlacement"):
            if key in payload["mentorship"]:
                new_val = str(payload["mentorship"].get(key) or "").strip()
                if (ment.get(key) or "").strip() != new_val:
                    changed = True
                ment[key] = new_val
    return changed


def update_bundle_metadata(
    faculty_user,
    primary_public_id: str,
    payload: dict[str, Any],
) -> tuple[Document, dict[str, Any]]:
    primary = get_owned_document(primary_public_id, faculty_user)
    if not primary:
        raise CriterionCEvidenceError("primary_not_found")
    bundle = bundle_from_document(primary)
    if not bundle:
        raise CriterionCEvidenceError("bundle_not_initialized")

    _apply_bundle_metadata_fields(bundle, payload, actor="faculty")

    validation = _apply_validation_to_bundle(
        bundle,
        faculty_profile_id=primary.faculty_profile_id,
        public_id=primary.public_id,
    )
    persist_bundle(primary, bundle)
    db.session.commit()
    return primary, validation


def reviewer_update_criterion_c(
    reviewer_user,
    primary_public_id: str,
    *,
    slot_id: str | None,
    status: str | None,
    reviewer_note: str = "",
    review_status: str | None = None,
    remarks: str = "",
    assessed_points: float | int | str | None = None,
    metadata: dict[str, Any] | None = None,
) -> tuple[Document, dict[str, Any]]:
    from documents.service import reviewer_can_access

    primary = get_document(primary_public_id)
    if not primary or not reviewer_can_access(reviewer_user, primary):
        raise CriterionCEvidenceError("forbidden")
    bundle = bundle_from_document(primary)
    if not bundle:
        raise CriterionCEvidenceError("bundle_not_initialized")

    if metadata:
        if _apply_bundle_metadata_fields(bundle, metadata, actor="reviewer"):
            import json

            db.session.add(
                AuditLog(
                    actor_user_id=int(reviewer_user.id),
                    action="Criterion C reviewer metadata update",
                    target_id=primary.public_id,
                    detail=json.dumps(
                        {
                            "documentId": primary.public_id,
                            "fields": sorted(metadata.keys()),
                        },
                        ensure_ascii=False,
                    )[:2000],
                )
            )

    if slot_id and status:
        checklist = bundle.setdefault("checklist", {})
        entry = checklist.get(slot_id) if isinstance(checklist.get(slot_id), dict) else {}
        if status == "verified":
            if not entry.get("documentId"):
                raise CriterionCEvidenceError("cannot_verify_empty_slot")
            entry["status"] = "verified"
            entry["ocrHintOnly"] = False
        elif status in ("present_unverified", "reviewer_required", "missing"):
            entry["status"] = status
        else:
            raise CriterionCEvidenceError("invalid_slot_status")
        if reviewer_note:
            entry["reviewerNote"] = reviewer_note.strip()
        checklist[slot_id] = entry

    if review_status:
        validation_pre = _apply_validation_to_bundle(
            bundle,
            faculty_profile_id=primary.faculty_profile_id,
            public_id=primary.public_id,
        )
        if review_status.strip().lower() == "approved":
            if validation_pre.get("blockers"):
                raise CriterionCEvidenceError("accomplishment_not_ready_for_decision")
            from documents.criterion_c_evidence.bundle import SLOT_STATUS_VERIFIED

            for _slot, st in (validation_pre.get("checklistSummary") or {}).items():
                if st != SLOT_STATUS_VERIFIED:
                    raise CriterionCEvidenceError("accomplishment_not_ready_for_decision")
        from kra_configuration.version_lock import (
            maybe_lock_document_scoring_configuration,
            record_configuration_in_criterion_c_bundle,
            resolve_settings_for_faculty_simulation,
        )

        score_settings, score_resolution = resolve_settings_for_faculty_simulation()
        try:
            apply_reviewer_accomplishment_decision(
                bundle,
                review_status=review_status,
                reviewer_user_id=int(reviewer_user.id),
                reviewer_display_name=getattr(reviewer_user, "full_name", "") or "",
                remarks=remarks,
                assessed_points=assessed_points,
                indicator_id=(primary.indicator_id or "").strip(),
                settings=score_settings,
            )
            record_configuration_in_criterion_c_bundle(bundle, resolution=score_resolution)
        except ValueError as error:
            code = str(error)
            if code in (
                "invalid_review_status",
                "review_rejection_remarks_required",
                "review_approval_remarks_required",
                "assessed_points_invalid",
                "assessed_points_exceeds_annex_max",
                "indicator_points_unknown",
            ):
                raise CriterionCEvidenceError(code) from error
            raise

        import json

        db.session.add(
            AuditLog(
                actor_user_id=int(reviewer_user.id),
                action="Criterion C reviewer accomplishment decision",
                target_id=primary.public_id,
                detail=json.dumps(
                    {
                        "documentId": primary.public_id,
                        "indicatorId": primary.indicator_id,
                        "reviewStatus": review_status,
                        "assessedPoints": bundle.get("reviewerAssessment", {}).get("assessedPoints"),
                    },
                    ensure_ascii=False,
                )[:4000],
            )
        )
    elif remarks:
        bundle["reviewerRemarks"] = remarks.strip()

    validation = _apply_validation_to_bundle(
        bundle,
        faculty_profile_id=primary.faculty_profile_id,
        public_id=primary.public_id,
    )
    persist_bundle(primary, bundle)
    if review_status and review_status.strip().lower() == "approved":
        from kra_configuration.version_lock import maybe_lock_document_scoring_configuration

        maybe_lock_document_scoring_configuration(primary)
    if review_status:
        from documents.criterion_c_evidence.workflow_sync import sync_criterion_c_document_workflow_status

        sync_criterion_c_document_workflow_status(primary, bundle, review_status=review_status)
    db.session.commit()
    return primary, validation


def bundle_api_payload(doc: Document) -> dict[str, Any]:
    from documents.criterion_c_evidence.ocr_research import (
        OCR_EXTRACTION_KEY,
        ensure_research_ocr_extraction,
    )

    ensure_research_ocr_extraction(doc)
    from documents.criterion_c_evidence.workflow_sync import heal_criterion_c_workflow_status_mismatch

    if heal_criterion_c_workflow_status_mismatch(doc):
        db.session.commit()
    elif db.session.is_modified(doc):
        db.session.commit()
    bundle = bundle_from_document(doc)
    validation = validate_criterion_c_bundle(bundle)
    if isinstance(bundle, dict):
        validation = _apply_validation_to_bundle(
            bundle,
            faculty_profile_id=doc.faculty_profile_id,
            public_id=doc.public_id,
        )
    est = estimated_points_for_bundle(
        bundle if isinstance(bundle, dict) else None,
        indicator_id=(doc.indicator_id or "").strip(),
    )
    assessed = None
    if isinstance(bundle, dict):
        ra = bundle.get("reviewerAssessment")
        if isinstance(ra, dict):
            assessed = ra.get("assessedPoints")
    info = dict(getattr(doc, "extracted_info", None) or {})
    ocr_extraction = info.get(OCR_EXTRACTION_KEY)
    ocr_flags: list[str] = []
    if isinstance(ocr_extraction, dict):
        fields = ocr_extraction.get("fields") if isinstance(ocr_extraction.get("fields"), dict) else {}
        sn = fields.get("studentNames") if isinstance(fields.get("studentNames"), dict) else {}
        st_status = (sn.get("status") or "").strip().lower()
        if st_status in ("missing", "needs_review"):
            ocr_flags.append("student_names_ocr_needs_review")
        if not (sn.get("value") or "").strip():
            ocr_flags.append("student_names_ocr_missing")

    return {
        "bundle": bundle,
        "validation": validation,
        "scoring": {
            "estimatedPoints": est,
            "reviewerAssessedPoints": assessed,
            "indicatorId": doc.indicator_id,
        },
        "isSupportingDocument": is_supporting_evidence_document(doc),
        "link": link_from_document(doc),
        "ocrStatus": (getattr(doc, "ocr_status", None) or "pending").strip().lower(),
        "ocrExtraction": ocr_extraction,
        "ocrReviewFlags": ocr_flags,
    }


def list_faculty_accomplishments(faculty_profile_id: int) -> list[dict[str, Any]]:
    q = Document.query.filter_by(
        faculty_profile_id=faculty_profile_id,
        criterion_id=CRITERION_C_ID,
    ).filter(Document.deleted_at.is_(None))
    rows: list[dict[str, Any]] = []
    for doc in q.order_by(Document.submitted_at.desc()).limit(200).all():
        if is_supporting_evidence_document(doc):
            continue
        bundle = bundle_from_document(doc)
        validation = validate_criterion_c_bundle(bundle) if bundle else None
        assessment = (bundle or {}).get("reviewerAssessment")
        assessed_pts = assessment.get("assessedPoints") if isinstance(assessment, dict) else None
        submitted = doc.submitted_at.isoformat() if getattr(doc, "submitted_at", None) else None
        rows.append(
            {
                "documentId": doc.public_id,
                "title": doc.title,
                "indicatorId": doc.indicator_id,
                "status": doc.status,
                "accomplishmentId": (bundle or {}).get("accomplishmentId"),
                "reviewStatus": (bundle or {}).get("reviewStatus") or "pending",
                "validationStatus": (validation or {}).get("validationStatus"),
                "projectTitle": (bundle or {}).get("projectTitle"),
                "studentNames": (bundle or {}).get("studentNames"),
                "studentGroupLabel": (bundle or {}).get("studentGroupLabel"),
                "serviceCategory": (bundle or {}).get("serviceCategory"),
                "researchType": (bundle or {}).get("researchType"),
                "role": (bundle or {}).get("role"),
                "academicYear": (bundle or {}).get("academicYear"),
                "completionDate": (bundle or {}).get("completionDate"),
                "metadataConfirmed": (bundle or {}).get("metadataConfirmed"),
                "metadataFacultyConfirmedAt": (bundle or {}).get("metadataFacultyConfirmedAt"),
                "submittedAt": submitted,
                "estimatedPoints": estimated_points_for_bundle(
                    bundle,
                    indicator_id=(doc.indicator_id or "").strip(),
                ),
                "reviewerAssessedPoints": assessed_pts,
            }
        )
    return rows


def criterion_c_summary_for_faculty(faculty_profile_id: int, *, settings: dict[str, Any] | None = None) -> dict[str, Any]:
    from documents.criterion_c_evidence.scoring import aggregate_criterion_c_from_documents
    from kra_configuration.version_lock import resolve_settings_for_faculty_simulation

    applicable = False
    if settings is None:
        settings, resolution = resolve_settings_for_faculty_simulation()
        applicable = resolution.has_applicable_row

    docs = (
        Document.query.filter_by(
            faculty_profile_id=faculty_profile_id,
            criterion_id=CRITERION_C_ID,
        )
        .filter(Document.deleted_at.is_(None))
        .all()
    )
    from documents.criterion_c_evidence.workflow_sync import heal_criterion_c_workflow_for_documents

    if heal_criterion_c_workflow_for_documents(docs):
        db.session.commit()
    accomplishments = list_faculty_accomplishments(faculty_profile_id)
    block = aggregate_criterion_c_from_documents(
        docs,
        settings=settings,
        applicable_config_present=applicable or bool(settings and settings.get("criteria")),
    )
    block["accomplishmentCount"] = len(accomplishments)
    pending = approved = rejected = 0
    for row in accomplishments:
        rs = (row.get("reviewStatus") or "pending").strip().lower()
        if rs == "approved":
            approved += 1
        elif rs == "rejected":
            rejected += 1
        else:
            pending += 1
    block["reviewCounts"] = {
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
    }
    draft_est = sum(float(r.get("estimatedPoints") or 0) for r in accomplishments)
    cap = float(block.get("maxPoints") or 10.0)
    block["draftEstimatedSum"] = round(min(draft_est, cap), 2)
    return block
