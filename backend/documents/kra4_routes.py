"""Flask routes for KRA IV evidence bundles and criterion summaries."""

from __future__ import annotations

from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity

from auth import assignment_queries as aq
from auth import permissions as perm
from auth.permissions import ROLE_ADMINISTRATOR, ROLE_FACULTY, ROLE_REVIEWER
from documents import service as doc_svc
from documents.serializers import document_to_web


def _kra4_evidence_error_response(error) -> tuple:
    from documents.kra4_evidence.service import Kra4EvidenceError
    from documents.kra2_evidence.service import Kra2EvidenceError

    if not isinstance(error, Kra4EvidenceError):
        raise error
    wrapped = Kra2EvidenceError(error.code, str(error))
    from documents.routes import _kra2_evidence_error_response

    return _kra2_evidence_error_response(wrapped)


_KRA4_REVIEWER_METADATA_KEYS = (
    "activityTitle",
    "organizationName",
    "facultyRole",
    "activityDate",
    "serviceStartDate",
    "serviceEndDate",
    "institutionName",
    "degreeTitle",
    "eventTitle",
    "eventDurationHours",
    "eventScope",
    "paperTitle",
    "awardTitle",
    "awardLevel",
    "employerName",
    "positionTitle",
    "experienceYears",
    "approvalReference",
    "outputTitle",
)


def register() -> None:
    from documents.routes import (
        _file_api_base,
        _reviewer_faculty_profile_or_404,
        admin_docs_bp,
        faculty_docs_bp,
        reviewer_docs_bp,
    )

    @faculty_docs_bp.get("/<public_id>/kra4/evidence-bundle")
    @perm.roles_required(ROLE_FACULTY)
    def faculty_get_kra4_bundle(public_id: str):
        from documents.kra4_evidence.service import bundle_api_payload

        user = aq.current_faculty_user(get_jwt_identity())
        doc = doc_svc.get_owned_document(public_id, user) if user else None
        if not doc:
            return jsonify({"message": "Document was not found."}), 404
        return jsonify(bundle_api_payload(doc)), 200

    @faculty_docs_bp.patch("/<public_id>/kra4/evidence-bundle")
    @perm.roles_required(ROLE_FACULTY)
    def faculty_patch_kra4_bundle(public_id: str):
        from documents.kra4_evidence.service import Kra4EvidenceError, update_bundle_metadata, bundle_api_payload

        user = aq.current_faculty_user(get_jwt_identity())
        if not user:
            return jsonify({"message": "Faculty account was not found."}), 404
        body = request.get_json(silent=True) or {}
        try:
            doc, validation = update_bundle_metadata(user, public_id, body)
        except Kra4EvidenceError as error:
            return _kra4_evidence_error_response(error)
        payload = bundle_api_payload(doc)
        return jsonify(
            {
                "document": document_to_web(doc, api_base=_file_api_base("faculty", doc.public_id)),
                "validation": validation,
                "bundle": payload.get("bundle"),
                "scoring": payload.get("scoring"),
                "ocrStatus": payload.get("ocrStatus"),
                "ocrExtraction": payload.get("ocrExtraction"),
                "requiredEvidenceSlots": payload.get("requiredEvidenceSlots"),
                "slotLabels": payload.get("slotLabels"),
                "submissionStatus": validation.get("validationStatus"),
                "scoringVersion": payload.get("scoring", {}).get("scoringConfigurationVersion"),
            }
        ), 200

    @faculty_docs_bp.post("/<public_id>/kra4/link-supporting")
    @perm.roles_required(ROLE_FACULTY)
    def faculty_link_kra4_supporting(public_id: str):
        from documents.kra4_evidence.service import Kra4EvidenceError, link_existing_supporting_document

        user = aq.current_faculty_user(get_jwt_identity())
        if not user:
            return jsonify({"message": "Faculty account was not found."}), 404
        body = request.get_json(silent=True) or {}
        supporting_id = (body.get("supportingDocumentId") or body.get("supporting_document_id") or "").strip()
        slot = (body.get("evidenceSlot") or body.get("evidence_slot") or "").strip()
        if not supporting_id or not slot:
            return jsonify({"message": "supportingDocumentId and evidenceSlot are required."}), 400
        try:
            primary, validation = link_existing_supporting_document(
                user,
                primary_public_id=public_id,
                supporting_public_id=supporting_id,
                evidence_slot=slot,
            )
        except Kra4EvidenceError as error:
            return _kra4_evidence_error_response(error)
        return jsonify(
            {
                "document": document_to_web(primary, api_base=_file_api_base("faculty", primary.public_id)),
                "validation": validation,
            }
        ), 200

    @reviewer_docs_bp.get("/documents/<public_id>/kra4/evidence-bundle")
    @perm.roles_required(ROLE_REVIEWER)
    def reviewer_get_kra4_bundle(public_id: str):
        from documents.kra4_evidence.service import bundle_api_payload

        user = aq.current_reviewer_user(get_jwt_identity())
        doc = doc_svc.get_document(public_id)
        if not doc or not user or not doc_svc.reviewer_can_access(user, doc):
            return jsonify({"message": "Document was not found."}), 404
        return jsonify(bundle_api_payload(doc, viewer_user=user)), 200

    @reviewer_docs_bp.patch("/documents/<public_id>/kra4/evidence-bundle")
    @perm.roles_required(ROLE_REVIEWER)
    def reviewer_patch_kra4_bundle(public_id: str):
        from documents.kra4_evidence.service import Kra4EvidenceError, reviewer_update_kra4, bundle_api_payload

        user = aq.current_reviewer_user(get_jwt_identity())
        body = request.get_json(silent=True) or {}
        slot_id = (body.get("evidenceSlot") or body.get("evidence_slot") or body.get("slotId") or "").strip()
        status = (body.get("status") or "").strip()
        review_status = (body.get("reviewStatus") or body.get("review_status") or "").strip() or None
        has_remarks = bool((body.get("remarks") or body.get("reviewerRemarks") or "").strip())
        has_assessment_fields = (
            "assessedPoints" in body
            or "assessed_points" in body
            or bool((body.get("scoreAdjustmentReason") or body.get("score_adjustment_reason") or "").strip())
        )
        metadata_patch = {k: body[k] for k in _KRA4_REVIEWER_METADATA_KEYS if k in body}
        if body.get("confirmReviewerMetadata") is True:
            metadata_patch["confirmReviewerMetadata"] = True
        has_metadata = bool(metadata_patch)
        reassessment_action = (body.get("reassessmentAction") or body.get("reassessment_action") or "").strip() or None
        if (
            not slot_id
            and not review_status
            and not has_remarks
            and not has_metadata
            and not has_assessment_fields
            and not reassessment_action
        ):
            return jsonify({"message": "evidenceSlot/status, reviewStatus, metadata, remarks, or assessedPoints required."}), 400
        if slot_id and not status:
            return jsonify({"message": "status is required when evidenceSlot is provided."}), 400
        try:
            doc, validation = reviewer_update_kra4(
                user,
                public_id,
                slot_id=slot_id or None,
                status=status or None,
                reviewer_note=(body.get("reviewerNote") or body.get("note") or ""),
                review_status=review_status,
                remarks=(body.get("remarks") or body.get("reviewerRemarks") or ""),
                assessed_points=body.get("assessedPoints") if "assessedPoints" in body else body.get("assessed_points"),
                score_adjustment_reason=(
                    body.get("scoreAdjustmentReason") or body.get("score_adjustment_reason") or ""
                ),
                metadata=metadata_patch if has_metadata else None,
                reassessment_action=reassessment_action,
                reassessment_reason=(body.get("reassessmentReason") or body.get("reassessment_reason") or ""),
                confirm_reassessment=body.get("confirmReassessment") is True
                or body.get("confirm_reassessment") is True,
            )
        except Kra4EvidenceError as error:
            return _kra4_evidence_error_response(error)
        payload = bundle_api_payload(doc, viewer_user=user)
        return jsonify(
            {
                "document": document_to_web(doc, api_base=_file_api_base("reviewer", doc.public_id), ocr_detail=True),
                "validation": validation,
                "bundle": payload.get("bundle"),
                "scoring": payload.get("scoring"),
                "ocrExtraction": payload.get("ocrExtraction"),
                "requiredEvidenceSlots": payload.get("requiredEvidenceSlots"),
                "slotLabels": payload.get("slotLabels"),
                "reassessmentCapabilities": payload.get("reassessmentCapabilities"),
                "reassessmentSession": payload.get("reassessmentSession"),
                "reassessmentHistory": payload.get("reassessmentHistory"),
            }
        ), 200

    def _faculty_kra4_criterion_summary(criterion_id: str):
        from documents.kra4_evidence.service import kra4_summary_for_faculty

        user = aq.current_faculty_user(get_jwt_identity())
        if not user or not user.faculty_profile:
            return jsonify({"message": "Faculty profile was not found."}), 404
        return jsonify(kra4_summary_for_faculty(user.faculty_profile.id, criterion_id=criterion_id)), 200

    def _faculty_kra4_criterion_accomplishments(criterion_id: str):
        from documents.kra4_evidence.service import list_faculty_accomplishments

        user = aq.current_faculty_user(get_jwt_identity())
        if not user or not user.faculty_profile:
            return jsonify({"message": "Faculty profile was not found."}), 404
        return jsonify(
            {"accomplishments": list_faculty_accomplishments(user.faculty_profile.id, criterion_id=criterion_id)}
        ), 200

    def _reviewer_kra4_criterion_summary(faculty_public_id: str, criterion_id: str):
        from documents.kra4_evidence.service import kra4_summary_for_faculty

        user = aq.current_reviewer_user(get_jwt_identity())
        if not user:
            return jsonify({"message": "Reviewer account was not found."}), 404
        profile = _reviewer_faculty_profile_or_404(user, faculty_public_id)
        if not profile:
            return jsonify({"message": "Faculty assignment was not found."}), 404
        return jsonify(kra4_summary_for_faculty(profile.id, criterion_id=criterion_id)), 200

    def _reviewer_kra4_criterion_accomplishments(faculty_public_id: str, criterion_id: str):
        from documents.kra4_evidence.service import list_faculty_accomplishments

        user = aq.current_reviewer_user(get_jwt_identity())
        if not user:
            return jsonify({"message": "Reviewer account was not found."}), 404
        profile = _reviewer_faculty_profile_or_404(user, faculty_public_id)
        if not profile:
            return jsonify({"message": "Faculty assignment was not found."}), 404
        return jsonify(
            {
                "accomplishments": list_faculty_accomplishments(
                    profile.id, criterion_id=criterion_id, submitted_only=False
                )
            }
        ), 200

    @faculty_docs_bp.get("/kra4-a/summary")
    @perm.roles_required(ROLE_FACULTY)
    def faculty_kra4_a_summary():
        from kra_configuration.kra4_annex import CRITERION_A_ID

        return _faculty_kra4_criterion_summary(CRITERION_A_ID)

    @faculty_docs_bp.get("/kra4-a/accomplishments")
    @perm.roles_required(ROLE_FACULTY)
    def faculty_kra4_a_accomplishments():
        from kra_configuration.kra4_annex import CRITERION_A_ID

        return _faculty_kra4_criterion_accomplishments(CRITERION_A_ID)

    @faculty_docs_bp.get("/kra4-b/summary")
    @perm.roles_required(ROLE_FACULTY)
    def faculty_kra4_b_summary():
        from kra_configuration.kra4_annex import CRITERION_B_ID

        return _faculty_kra4_criterion_summary(CRITERION_B_ID)

    @faculty_docs_bp.get("/kra4-b/accomplishments")
    @perm.roles_required(ROLE_FACULTY)
    def faculty_kra4_b_accomplishments():
        from kra_configuration.kra4_annex import CRITERION_B_ID

        return _faculty_kra4_criterion_accomplishments(CRITERION_B_ID)

    @faculty_docs_bp.get("/kra4-c/summary")
    @perm.roles_required(ROLE_FACULTY)
    def faculty_kra4_c_summary():
        from kra_configuration.kra4_annex import CRITERION_C_ID

        return _faculty_kra4_criterion_summary(CRITERION_C_ID)

    @faculty_docs_bp.get("/kra4-c/accomplishments")
    @perm.roles_required(ROLE_FACULTY)
    def faculty_kra4_c_accomplishments():
        from kra_configuration.kra4_annex import CRITERION_C_ID

        return _faculty_kra4_criterion_accomplishments(CRITERION_C_ID)

    @faculty_docs_bp.get("/kra4-d/summary")
    @perm.roles_required(ROLE_FACULTY)
    def faculty_kra4_d_summary():
        from kra_configuration.kra4_annex import CRITERION_D_ID

        return _faculty_kra4_criterion_summary(CRITERION_D_ID)

    @faculty_docs_bp.get("/kra4-d/accomplishments")
    @perm.roles_required(ROLE_FACULTY)
    def faculty_kra4_d_accomplishments():
        from kra_configuration.kra4_annex import CRITERION_D_ID

        return _faculty_kra4_criterion_accomplishments(CRITERION_D_ID)

    @reviewer_docs_bp.get("/me/faculty/<faculty_public_id>/kra4-a/summary")
    @perm.roles_required(ROLE_REVIEWER)
    def reviewer_kra4_a_summary(faculty_public_id: str):
        from kra_configuration.kra4_annex import CRITERION_A_ID

        return _reviewer_kra4_criterion_summary(faculty_public_id, CRITERION_A_ID)

    @reviewer_docs_bp.get("/me/faculty/<faculty_public_id>/kra4-a/accomplishments")
    @perm.roles_required(ROLE_REVIEWER)
    def reviewer_kra4_a_accomplishments(faculty_public_id: str):
        from kra_configuration.kra4_annex import CRITERION_A_ID

        return _reviewer_kra4_criterion_accomplishments(faculty_public_id, CRITERION_A_ID)

    @reviewer_docs_bp.get("/me/faculty/<faculty_public_id>/kra4-b/summary")
    @perm.roles_required(ROLE_REVIEWER)
    def reviewer_kra4_b_summary(faculty_public_id: str):
        from kra_configuration.kra4_annex import CRITERION_B_ID

        return _reviewer_kra4_criterion_summary(faculty_public_id, CRITERION_B_ID)

    @reviewer_docs_bp.get("/me/faculty/<faculty_public_id>/kra4-b/accomplishments")
    @perm.roles_required(ROLE_REVIEWER)
    def reviewer_kra4_b_accomplishments(faculty_public_id: str):
        from kra_configuration.kra4_annex import CRITERION_B_ID

        return _reviewer_kra4_criterion_accomplishments(faculty_public_id, CRITERION_B_ID)

    @reviewer_docs_bp.get("/me/faculty/<faculty_public_id>/kra4-c/summary")
    @perm.roles_required(ROLE_REVIEWER)
    def reviewer_kra4_c_summary(faculty_public_id: str):
        from kra_configuration.kra4_annex import CRITERION_C_ID

        return _reviewer_kra4_criterion_summary(faculty_public_id, CRITERION_C_ID)

    @reviewer_docs_bp.get("/me/faculty/<faculty_public_id>/kra4-c/accomplishments")
    @perm.roles_required(ROLE_REVIEWER)
    def reviewer_kra4_c_accomplishments(faculty_public_id: str):
        from kra_configuration.kra4_annex import CRITERION_C_ID

        return _reviewer_kra4_criterion_accomplishments(faculty_public_id, CRITERION_C_ID)

    @reviewer_docs_bp.get("/me/faculty/<faculty_public_id>/kra4-d/summary")
    @perm.roles_required(ROLE_REVIEWER)
    def reviewer_kra4_d_summary(faculty_public_id: str):
        from kra_configuration.kra4_annex import CRITERION_D_ID

        return _reviewer_kra4_criterion_summary(faculty_public_id, CRITERION_D_ID)

    @reviewer_docs_bp.get("/me/faculty/<faculty_public_id>/kra4-d/accomplishments")
    @perm.roles_required(ROLE_REVIEWER)
    def reviewer_kra4_d_accomplishments(faculty_public_id: str):
        from kra_configuration.kra4_annex import CRITERION_D_ID

        return _reviewer_kra4_criterion_accomplishments(faculty_public_id, CRITERION_D_ID)

    def _admin_reassessment_patch_kra4(public_id: str):
        from documents.kra4_evidence.service import Kra4EvidenceError, reviewer_update_kra4, bundle_api_payload
        from models import User

        admin = User.query.filter_by(public_id=get_jwt_identity(), role=ROLE_ADMINISTRATOR, is_active=True).first()
        if not admin:
            return jsonify({"message": "Administrator account was not found."}), 403
        body = request.get_json(silent=True) or {}
        reassessment_action = (body.get("reassessmentAction") or body.get("reassessment_action") or "").strip()
        if not reassessment_action:
            return jsonify({"message": "reassessmentAction is required for administrator reassessment."}), 400
        try:
            doc, validation = reviewer_update_kra4(
                admin,
                public_id,
                slot_id=None,
                status=None,
                review_status=None,
                remarks=(body.get("remarks") or body.get("reviewerRemarks") or ""),
                assessed_points=body.get("assessedPoints") if "assessedPoints" in body else body.get("assessed_points"),
                score_adjustment_reason=(
                    body.get("scoreAdjustmentReason") or body.get("score_adjustment_reason") or ""
                ),
                reassessment_action=reassessment_action,
                reassessment_reason=(body.get("reassessmentReason") or body.get("reassessment_reason") or ""),
                confirm_reassessment=body.get("confirmReassessment") is True
                or body.get("confirm_reassessment") is True,
                actor_is_administrator=True,
            )
        except Kra4EvidenceError as error:
            return _kra4_evidence_error_response(error)
        payload = bundle_api_payload(doc)
        return jsonify({"validation": validation, "bundle": payload.get("bundle"), "scoring": payload.get("scoring")}), 200

    @admin_docs_bp.patch("/<public_id>/kra4/evidence-bundle")
    @perm.roles_required(ROLE_ADMINISTRATOR)
    def admin_patch_kra4_evidence_bundle(public_id: str):
        return _admin_reassessment_patch_kra4(public_id)
