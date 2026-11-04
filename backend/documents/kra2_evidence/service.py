"""KRA II evidence bundles — shared service layer (Criteria A/B/C)."""

from __future__ import annotations

from typing import Any

from extensions import db
from models import AuditLog, Document

from kra_configuration.kra2_annex import (
    CRITERION_A_ID,
    criterion_id_for_indicator,
    is_kra2_criterion,
    is_kra2_indicator,
)
from documents.kra2_evidence.bundle import (
    apply_slot_link,
    build_initial_bundle,
    bundle_from_document,
    is_supporting_evidence_document,
    link_from_document,
    persist_bundle,
    persist_link,
)
from documents.kra2_evidence.slots import required_slots, slot_label
from documents.kra2_evidence.submission_state import accomplishment_submitted
from documents.kra2_evidence.reviewer_assessment import apply_reviewer_accomplishment_decision
from documents.kra2_evidence.scoring import estimated_points_for_bundle
from documents.kra2_evidence.validation import validate_kra2_bundle
from documents.service import get_document, get_owned_document


class Kra2EvidenceError(ValueError):
    def __init__(self, code: str, message: str = ""):
        super().__init__(message or code)
        self.code = code


def _indicator_for_doc(doc: Document) -> str:
    bundle = bundle_from_document(doc)
    if isinstance(bundle, dict):
        bid = (bundle.get("indicatorId") or "").strip()
        if bid and is_kra2_indicator(bid):
            return bid
    return (doc.indicator_id or "").strip()


def _peer_bundles(
    faculty_profile_id: int,
    *,
    exclude_public_id: str | None = None,
) -> list[tuple[str, dict[str, Any]]]:
    q = Document.query.filter_by(faculty_profile_id=faculty_profile_id).filter(Document.deleted_at.is_(None))
    rows: list[tuple[str, dict[str, Any]]] = []
    for doc in q.limit(500).all():
        if not is_kra2_indicator(doc.indicator_id):
            continue
        if is_supporting_evidence_document(doc):
            continue
        bundle = bundle_from_document(doc)
        if bundle and doc.public_id != exclude_public_id:
            rows.append((doc.public_id, bundle))
    return rows


def _apply_validation_to_bundle(
    bundle: dict[str, Any],
    *,
    indicator_id: str,
    faculty_profile_id: int | None = None,
    public_id: str | None = None,
) -> dict[str, Any]:
    if faculty_profile_id is not None:
        from documents.kra2_evidence.deduplication import assess_peer_duplicates
        from documents.kra2_evidence.patent_deduplication import assess_patent_stage_overlaps

        peers = _peer_bundles(faculty_profile_id, exclude_public_id=public_id)
        dup_flags = assess_peer_duplicates(
            bundle,
            peer_bundles=[(pid, b) for pid, b in peers],
            self_public_id=public_id or "",
        )
        peer_triples = [
            (pid, b, (b.get("indicatorId") or "").strip())
            for pid, b in peers
        ]
        patent_flags = assess_patent_stage_overlaps(
            bundle,
            indicator_id=indicator_id,
            peer_bundles=peer_triples,
            self_public_id=public_id or "",
        )
        bundle["duplicateFlags"] = list(dict.fromkeys([*dup_flags, *patent_flags]))
    validation = validate_kra2_bundle(bundle, indicator_id=indicator_id)
    bundle["validationStatus"] = validation["validationStatus"]
    bundle["flags"] = validation["flags"]
    return validation


def maybe_initialize_kra2_bundle(doc: Document) -> None:
    if not is_kra2_criterion(doc.criterion_id):
        return
    if not is_kra2_indicator(doc.indicator_id):
        return
    if is_supporting_evidence_document(doc):
        return
    if bundle_from_document(doc):
        return
    initial_title = (doc.title or "").strip()
    bundle = build_initial_bundle(
        primary_document_id=doc.public_id,
        primary_file_hash=doc.file_hash,
        indicator_id=doc.indicator_id or "",
        output_title=initial_title,
    )
    from documents.kra2_evidence.ocr_publication import ensure_publication_ocr_extraction, merge_ocr_into_bundle

    extraction = ensure_publication_ocr_extraction(doc)
    bundle = merge_ocr_into_bundle(bundle, extraction)
    bundle["metadataWorkflow"] = "ocr_first"
    _apply_validation_to_bundle(
        bundle,
        indicator_id=_indicator_for_doc(doc),
        faculty_profile_id=doc.faculty_profile_id,
        public_id=doc.public_id,
    )
    persist_bundle(doc, bundle)
    doc.status = "draft"


def attach_supporting_upload_link(
    supporting: Document,
    *,
    primary_public_id: str,
    evidence_slot: str,
) -> Document:
    primary = get_document(primary_public_id)
    if not primary:
        raise Kra2EvidenceError("primary_not_found")
    db.session.refresh(primary)
    if primary.faculty_profile_id != supporting.faculty_profile_id:
        raise Kra2EvidenceError("faculty_mismatch")
    bundle = bundle_from_document(primary)
    if not bundle:
        raise Kra2EvidenceError("bundle_not_initialized")
    allowed = frozenset(required_slots(indicator_id=_indicator_for_doc(primary)))
    if evidence_slot not in allowed:
        raise Kra2EvidenceError("invalid_evidence_slot")

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
        raise Kra2EvidenceError("duplicate_primary_hash")

    bundle = apply_slot_link(
        bundle,
        slot_id=evidence_slot,
        supporting_document_id=supporting.public_id,
        supporting_file_hash=supporting.file_hash,
    )
    _apply_validation_to_bundle(
        bundle,
        indicator_id=_indicator_for_doc(primary),
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
        raise Kra2EvidenceError("primary_not_found")
    supporting = get_owned_document(supporting_public_id, faculty_user)
    if not supporting:
        raise Kra2EvidenceError("supporting_not_found")
    if supporting.public_id == primary.public_id:
        raise Kra2EvidenceError("cannot_link_self")
    attach_supporting_upload_link(
        supporting,
        primary_public_id=primary.public_id,
        evidence_slot=evidence_slot,
    )
    db.session.commit()
    bundle = bundle_from_document(primary) or {}
    return primary, validate_kra2_bundle(bundle, indicator_id=_indicator_for_doc(primary))


_METADATA_FIELD_MAP = {
    "outputTitle": "outputTitle",
    "outputVenue": "outputVenue",
    "journalTitle": "journalTitle",
    "authorsLine": "authorsLine",
    "publicationDate": "publicationDate",
    "publicationReference": "publicationReference",
    "registrationNumber": "registrationNumber",
    "registrationDate": "registrationDate",
    "citationContext": "citationContext",
    "indexingAttestation": "indexingAttestation",
}


def _field_value_for_confirm(bundle: dict[str, Any], field_id: str) -> bool:
    if field_id == "outputVenue" or field_id == "journalTitle":
        return bool((bundle.get("outputVenue") or bundle.get("journalTitle") or "").strip())
    raw = bundle.get(field_id)
    if raw is None:
        return False
    return bool(str(raw).strip())


def _apply_bundle_metadata_fields(
    bundle: dict[str, Any],
    payload: dict[str, Any],
    *,
    actor: str = "faculty",
) -> bool:
    confirmed = bundle.setdefault("metadataConfirmed", {})
    if not isinstance(confirmed, dict):
        confirmed = {}
        bundle["metadataConfirmed"] = confirmed
    per_field_confirmed = payload.get("metadataConfirmed")
    bulk_confirm = payload.get("confirmMetadata") is True
    reviewer_confirm = payload.get("confirmReviewerMetadata") is True
    changed = False
    for api_key, bundle_key in _METADATA_FIELD_MAP.items():
        if api_key not in payload:
            continue
        value = str(payload.get(api_key) or "").strip()
        if (bundle.get(bundle_key) or "").strip() != value:
            changed = True
        bundle[bundle_key] = value
        if bundle_key == "outputVenue":
            bundle["journalTitle"] = value
        elif bundle_key == "journalTitle" and value:
            bundle["outputVenue"] = value
        if actor == "reviewer":
            confirmed[bundle_key] = bool(value)
        elif bulk_confirm:
            confirmed[bundle_key] = bool(value)
        elif isinstance(per_field_confirmed, dict) and per_field_confirmed.get(bundle_key) is True:
            confirmed[bundle_key] = bool(value)
        elif api_key in payload:
            confirmed[bundle_key] = bool(value)

    if "declaredContributionPercent" in payload:
        raw = payload.get("declaredContributionPercent")
        try:
            pct = round(float(raw), 2) if raw is not None and str(raw).strip() else None
        except (TypeError, ValueError):
            pct = None
        if bundle.get("declaredContributionPercent") != pct:
            changed = True
        bundle["declaredContributionPercent"] = pct
        if bulk_confirm and pct is not None:
            confirmed["declaredContributionPercent"] = True

    if bulk_confirm and actor == "faculty":
        from documents.kra2_evidence.bundle import _utcnow_iso

        bundle["metadataFacultyConfirmedAt"] = _utcnow_iso()

    if payload.get("submitAccomplishment") is True:
        from documents.kra2_evidence.bundle import _utcnow_iso

        if not bundle.get("submittedForReviewAt"):
            changed = True
        bundle["submittedForReviewAt"] = _utcnow_iso()

    if actor == "reviewer" and reviewer_confirm:
        from kra_configuration.kra2_indicator_registry import metadata_field_ids

        ind = (bundle.get("indicatorId") or "").strip()
        for field_id in metadata_field_ids(ind):
            if field_id == "declaredContributionPercent":
                if (bundle.get("contribution") or "").strip().lower() != "declared":
                    continue
            if _field_value_for_confirm(bundle, field_id):
                confirmed[field_id] = True
        if _field_value_for_confirm(bundle, "outputVenue"):
            confirmed["journalTitle"] = True
        from documents.kra2_evidence.bundle import _utcnow_iso

        bundle["metadataReviewerConfirmedAt"] = _utcnow_iso()
        changed = True

    if actor == "reviewer" and changed and not reviewer_confirm:
        from documents.kra2_evidence.bundle import _utcnow_iso

        bundle["metadataReviewerConfirmedAt"] = _utcnow_iso()
    return changed


def update_bundle_metadata(
    faculty_user,
    primary_public_id: str,
    payload: dict[str, Any],
) -> tuple[Document, dict[str, Any]]:
    primary = get_owned_document(primary_public_id, faculty_user)
    if not primary:
        raise Kra2EvidenceError("primary_not_found")
    bundle = bundle_from_document(primary)
    if not bundle:
        raise Kra2EvidenceError("bundle_not_initialized")

    from documents.kra2_evidence.ocr_extraction import (
        ensure_publication_ocr_extraction,
        merge_ocr_into_bundle,
    )

    extraction = ensure_publication_ocr_extraction(primary)
    if isinstance(extraction, dict):
        merge_ocr_into_bundle(bundle, extraction)

    _apply_bundle_metadata_fields(bundle, payload, actor="faculty")
    validation = _apply_validation_to_bundle(
        bundle,
        indicator_id=_indicator_for_doc(primary),
        faculty_profile_id=primary.faculty_profile_id,
        public_id=primary.public_id,
    )
    submitting = payload.get("submitAccomplishment") is True
    persist_bundle(primary, bundle)
    if submitting:
        if validation.get("submissionBlockers") or not validation.get("readyForSubmission"):
            db.session.commit()
            raise Kra2EvidenceError("accomplishment_not_ready_for_decision")
        from documents.service import utcnow

        primary.status = "pending_review"
        primary.submitted_at = utcnow()
        if profile := primary.faculty_profile:
            primary.reviewer_user_id = profile.reviewer_user_id
    db.session.commit()
    return primary, validation


def reviewer_update_kra2(
    reviewer_user,
    primary_public_id: str,
    *,
    slot_id: str | None,
    status: str | None,
    reviewer_note: str = "",
    review_status: str | None = None,
    remarks: str = "",
    assessed_points: float | int | str | None = None,
    score_adjustment_reason: str = "",
    metadata: dict[str, Any] | None = None,
) -> tuple[Document, dict[str, Any]]:
    from documents.service import reviewer_can_access

    primary = get_document(primary_public_id)
    if not primary or not reviewer_can_access(reviewer_user, primary):
        raise Kra2EvidenceError("forbidden")
    bundle = bundle_from_document(primary)
    if not bundle:
        raise Kra2EvidenceError("bundle_not_initialized")
    indicator_id = _indicator_for_doc(primary)
    if (slot_id or review_status) and not accomplishment_submitted(bundle):
        raise Kra2EvidenceError("accomplishment_not_submitted")
    prior_review = (bundle.get("reviewStatus") or "").strip().lower()
    if prior_review == "approved" and review_status:
        raise Kra2EvidenceError("accomplishment_already_finalized")

    from documents.kra2_evidence.ocr_extraction import (
        ensure_publication_ocr_extraction,
        merge_ocr_into_bundle,
    )

    extraction = ensure_publication_ocr_extraction(primary)
    if isinstance(extraction, dict):
        merge_ocr_into_bundle(bundle, extraction)

    if metadata:
        if _apply_bundle_metadata_fields(bundle, metadata, actor="reviewer"):
            import json

            db.session.add(
                AuditLog(
                    actor_user_id=int(reviewer_user.id),
                    action="KRA II reviewer metadata update",
                    target_id=primary.public_id,
                    detail=json.dumps(
                        {"documentId": primary.public_id, "fields": sorted(metadata.keys())},
                        ensure_ascii=False,
                    )[:2000],
                )
            )

    if slot_id and status:
        checklist = bundle.setdefault("checklist", {})
        entry = checklist.get(slot_id) if isinstance(checklist.get(slot_id), dict) else {}
        if status == "verified":
            if not entry.get("documentId"):
                raise Kra2EvidenceError("cannot_verify_empty_slot")
            entry["status"] = "verified"
            entry["ocrHintOnly"] = False
        elif status in ("present_unverified", "reviewer_required", "missing"):
            entry["status"] = status
        else:
            raise Kra2EvidenceError("invalid_slot_status")
        if reviewer_note:
            entry["reviewerNote"] = reviewer_note.strip()
        checklist[slot_id] = entry

    if review_status:
        validation_pre = _apply_validation_to_bundle(
            bundle,
            indicator_id=indicator_id,
            faculty_profile_id=primary.faculty_profile_id,
            public_id=primary.public_id,
        )
        if review_status.strip().lower() == "approved":
            if validation_pre.get("approvalBlockers"):
                raise Kra2EvidenceError("accomplishment_not_ready_for_decision")
            from documents.kra2_evidence.bundle import SLOT_STATUS_VERIFIED

            for _slot, st in (validation_pre.get("checklistSummary") or {}).items():
                if st != SLOT_STATUS_VERIFIED:
                    raise Kra2EvidenceError("accomplishment_not_ready_for_decision")
        from kra_configuration.version_lock import (
            maybe_lock_document_scoring_configuration,
            record_configuration_in_kra2_bundle,
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
                score_adjustment_reason=score_adjustment_reason,
                indicator_id=indicator_id,
                settings=score_settings,
            )
            record_configuration_in_kra2_bundle(bundle, resolution=score_resolution)
            sc = bundle.get("scoringConfiguration")
            ra = bundle.get("reviewerAssessment")
            if isinstance(sc, dict) and isinstance(ra, dict):
                ra["scoringConfigurationId"] = sc.get("configurationId")
                ra["scoringConfigurationVersion"] = sc.get("version")
        except ValueError as error:
            code = str(error)
            if code in (
                "invalid_review_status",
                "review_rejection_remarks_required",
                "review_approval_remarks_required",
                "assessed_points_invalid",
                "assessed_points_exceeds_indicator_max",
                "assessed_points_exceeds_eligible",
                "assessed_points_not_adjustable",
                "score_adjustment_reason_required",
                "indicator_points_unknown",
            ):
                raise Kra2EvidenceError(code) from error
            raise

        import json

        db.session.add(
            AuditLog(
                actor_user_id=int(reviewer_user.id),
                action="KRA II reviewer accomplishment decision",
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
        indicator_id=indicator_id,
        faculty_profile_id=primary.faculty_profile_id,
        public_id=primary.public_id,
    )
    persist_bundle(primary, bundle)
    if review_status and review_status.strip().lower() == "approved":
        from kra_configuration.version_lock import maybe_lock_document_scoring_configuration

        maybe_lock_document_scoring_configuration(primary)
    if review_status:
        from documents.kra2_evidence.workflow_sync import sync_kra2_document_workflow_status

        sync_kra2_document_workflow_status(primary, bundle, review_status=review_status)
    db.session.commit()
    return primary, validation


def bundle_api_payload(doc: Document) -> dict[str, Any]:
    from documents.kra2_evidence.ocr_extraction import (
        OCR_EXTRACTION_KEY,
        ensure_publication_ocr_extraction,
        merge_ocr_into_bundle,
        ocr_review_flags_for_document,
    )
    from documents.kra2_evidence.workflow_sync import heal_kra2_workflow_status_mismatch

    extraction = ensure_publication_ocr_extraction(doc)
    bundle = bundle_from_document(doc)
    if isinstance(bundle, dict) and extraction:
        merge_ocr_into_bundle(bundle, extraction)
        persist_bundle(doc, bundle)
    if heal_kra2_workflow_status_mismatch(doc):
        db.session.commit()
    elif db.session.is_modified(doc):
        db.session.commit()

    bundle = bundle_from_document(doc)
    indicator_id = _indicator_for_doc(doc)
    if isinstance(bundle, dict) and (bundle.get("indicatorId") or "").strip() != indicator_id:
        bundle["indicatorId"] = indicator_id
    validation = validate_kra2_bundle(bundle, indicator_id=indicator_id)
    if isinstance(bundle, dict):
        validation = _apply_validation_to_bundle(
            bundle,
            indicator_id=indicator_id,
            faculty_profile_id=doc.faculty_profile_id,
            public_id=doc.public_id,
        )
        persist_bundle(doc, bundle)
    from kra_configuration.version_lock import resolve_settings_for_faculty_simulation
    from documents.kra2_evidence.reviewer_assessment import (
        reviewer_scoring_controls,
        system_calculated_assessed_points,
    )
    from kra_configuration.kra2_annex import (
        published_kra2_criterion_max_points,
        published_kra2_indicator_base_points,
        published_kra2_indicator_points,
    )
    from kra_configuration.kra2_indicator_registry import official_indicator_max_points, scoring_group_max

    score_settings, score_resolution = resolve_settings_for_faculty_simulation()
    applicable = score_resolution.has_applicable_row
    bundle_dict = bundle if isinstance(bundle, dict) else None
    est = estimated_points_for_bundle(
        bundle_dict,
        indicator_id=indicator_id,
        settings=score_settings,
        applicable_config_present=applicable,
    )
    eligible_max = published_kra2_indicator_points(
        indicator_id,
        score_settings,
        allow_annex_fallback=not applicable,
    )
    system_calc = None
    if bundle_dict:
        try:
            system_calc = system_calculated_assessed_points(
                bundle_dict,
                indicator_id=indicator_id,
                settings=score_settings,
            )
        except ValueError:
            system_calc = est
    assessed = None
    score_adjustment_reason = None
    if isinstance(bundle, dict):
        ra = bundle.get("reviewerAssessment")
        if isinstance(ra, dict):
            assessed = ra.get("assessedPoints")
            score_adjustment_reason = ra.get("scoreAdjustmentReason")
    info = dict(getattr(doc, "extracted_info", None) or {})
    ocr_extraction = info.get(OCR_EXTRACTION_KEY)
    review_flags = ocr_review_flags_for_document(doc, bundle if isinstance(bundle, dict) else None)
    controls = reviewer_scoring_controls(indicator_id, settings=score_settings)
    official_max = official_indicator_max_points(indicator_id, score_settings)
    official_base = published_kra2_indicator_base_points(
        indicator_id,
        score_settings,
        allow_annex_fallback=not applicable,
    )
    group_max = scoring_group_max(indicator_id)
    crit_id = (getattr(doc, "criterion_id", None) or "").strip()
    criterion_cap = None
    if crit_id:
        cap = published_kra2_criterion_max_points(
            crit_id,
            score_settings,
            allow_annex_fallback=not applicable,
        )
        criterion_cap = float(cap) if cap is not None else None
    verified_pct = None
    if isinstance(bundle, dict) and (bundle.get("contribution") or "").strip().lower() == "declared":
        try:
            verified_pct = float(bundle.get("declaredContributionPercent"))
        except (TypeError, ValueError):
            verified_pct = None
    sc = (bundle or {}).get("scoringConfiguration") if isinstance(bundle, dict) else None
    scoring_version = sc.get("version") if isinstance(sc, dict) else None
    ra = (bundle or {}).get("reviewerAssessment") if isinstance(bundle, dict) else None
    approved_pts = ra.get("approvedPoints") if isinstance(ra, dict) else None
    if approved_pts is None and isinstance(ra, dict):
        approved_pts = ra.get("assessedPoints")
    req_slots = list(required_slots(indicator_id=indicator_id))
    slot_labels = {slot: slot_label(slot, indicator_id=indicator_id) for slot in req_slots}
    return {
        "bundle": bundle,
        "validation": validation,
        "requiredEvidenceSlots": req_slots,
        "slotLabels": slot_labels,
        "effectiveIndicatorId": indicator_id,
        "scoring": {
            "estimatedPoints": est,
            "officialBasePoints": float(official_base) if official_base is not None else None,
            "verifiedContributionPercent": verified_pct,
            "systemCalculatedPoints": system_calc if system_calc is not None else est,
            "eligiblePoints": float(eligible_max) if eligible_max is not None else None,
            "groupMaxPoints": float(group_max) if group_max is not None else None,
            "criterionMaxPoints": criterion_cap,
            "criterionId": crit_id or None,
            "reviewerAssessedPoints": assessed,
            "approvedPoints": approved_pts,
            "scoreAdjustmentReason": score_adjustment_reason,
            "scoringMethod": controls["scoringMethod"],
            "scoringMethodLabel": controls["scoringMethodLabel"],
            "allowsPointAdjustment": controls["allowsPointAdjustment"],
            "allowsContributionEdit": controls["allowsContributionEdit"],
            "adjustmentGoverningRule": controls["adjustmentGoverningRule"],
            "maxAssessedPoints": system_calc if system_calc is not None else est,
            "indicatorMaxPoints": float(official_max) if official_max is not None else None,
            "indicatorId": indicator_id,
            "scoringConfigurationVersion": scoring_version,
        },
        "isSupportingDocument": is_supporting_evidence_document(doc),
        "link": link_from_document(doc),
        "ocrStatus": (getattr(doc, "ocr_status", None) or "pending").strip().lower(),
        "ocrExtraction": ocr_extraction,
        "ocrReviewFlags": review_flags,
    }


def list_faculty_accomplishments(
    faculty_profile_id: int,
    *,
    criterion_id: str | None = None,
    submitted_only: bool = False,
) -> list[dict[str, Any]]:
    q = Document.query.filter_by(faculty_profile_id=faculty_profile_id).filter(
        Document.deleted_at.is_(None)
    )
    if criterion_id:
        q = q.filter_by(criterion_id=criterion_id)
    else:
        q = q.filter(Document.criterion_id.like("kra2-%"))
    rows: list[dict[str, Any]] = []
    for doc in q.order_by(Document.submitted_at.desc()).limit(200).all():
        if not is_kra2_indicator(doc.indicator_id):
            continue
        if is_supporting_evidence_document(doc):
            continue
        bundle = bundle_from_document(doc)
        if submitted_only and not accomplishment_submitted(bundle):
            continue
        indicator_id = _indicator_for_doc(doc)
        validation = validate_kra2_bundle(bundle, indicator_id=indicator_id) if bundle else None
        assessment = (bundle or {}).get("reviewerAssessment")
        assessed_pts = assessment.get("assessedPoints") if isinstance(assessment, dict) else None
        submitted = doc.submitted_at.isoformat() if getattr(doc, "submitted_at", None) else None
        rows.append(
            {
                "documentId": doc.public_id,
                "title": doc.title,
                "indicatorId": doc.indicator_id,
                "criterionId": doc.criterion_id,
                "status": doc.status,
                "accomplishmentId": (bundle or {}).get("accomplishmentId"),
                "reviewStatus": (bundle or {}).get("reviewStatus") or "pending",
                "validationStatus": (validation or {}).get("validationStatus"),
                "outputTitle": (bundle or {}).get("outputTitle"),
                "journalTitle": (bundle or {}).get("journalTitle"),
                "authorsLine": (bundle or {}).get("authorsLine"),
                "publicationDate": (bundle or {}).get("publicationDate"),
                "declaredContributionPercent": (bundle or {}).get("declaredContributionPercent"),
                "metadataConfirmed": (bundle or {}).get("metadataConfirmed"),
                "submittedForReviewAt": (bundle or {}).get("submittedForReviewAt"),
                "submittedAt": submitted,
                "estimatedPoints": estimated_points_for_bundle(
                    bundle,
                    indicator_id=indicator_id,
                ),
                "reviewerAssessedPoints": assessed_pts,
            }
        )
    return rows


def kra2_summary_for_faculty(
    faculty_profile_id: int,
    *,
    criterion_id: str,
    settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from documents.kra2_evidence.scoring import aggregate_kra2_criterion_from_documents
    from kra_configuration.version_lock import resolve_settings_for_faculty_simulation

    applicable = False
    if settings is None:
        settings, resolution = resolve_settings_for_faculty_simulation()
        applicable = resolution.has_applicable_row

    docs = (
        Document.query.filter_by(
            faculty_profile_id=faculty_profile_id,
            criterion_id=criterion_id,
        )
        .filter(Document.deleted_at.is_(None))
        .all()
    )
    from documents.kra2_evidence.workflow_sync import heal_kra2_workflow_for_documents

    if heal_kra2_workflow_for_documents(docs):
        db.session.commit()
    accomplishments = list_faculty_accomplishments(faculty_profile_id, criterion_id=criterion_id)
    block = aggregate_kra2_criterion_from_documents(
        docs,
        criterion_id=criterion_id,
        settings=settings,
        applicable_config_present=applicable or bool(settings and settings.get("criteria")),
    )
    block["accomplishmentCount"] = len(accomplishments)
    pending = approved = rejected = draft_count = 0
    for row in accomplishments:
        if not (row.get("submittedForReviewAt") or "").strip():
            draft_count += 1
            continue
        rs = (row.get("reviewStatus") or "pending").strip().lower()
        if rs == "approved":
            approved += 1
        elif rs == "rejected":
            rejected += 1
        else:
            pending += 1
    block["draftCount"] = draft_count
    block["reviewCounts"] = {"pending": pending, "approved": approved, "rejected": rejected}
    draft_est = sum(float(r.get("estimatedPoints") or 0) for r in accomplishments)
    cap = float(block.get("maxPoints") or 100.0)
    block["draftEstimatedSum"] = round(min(draft_est, cap), 2)
    return block
