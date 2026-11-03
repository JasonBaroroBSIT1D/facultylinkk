"""REST routes for KRA-classified faculty documents."""

from __future__ import annotations

import mimetypes

from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import get_jwt_identity

from auth import assignment_queries as aq
from auth import permissions as perm
from auth.permissions import ROLE_ADMINISTRATOR, ROLE_FACULTY, ROLE_REVIEWER
from documents import directory as doc_dir
from documents import service as doc_svc
from documents.serializers import document_to_web, stats_from_documents
from models import DocumentTeachingEvaluation, FacultyProfile, User
from documents.metadata_correction import apply_metadata_correction
from documents.teaching_evaluation_review import apply_teaching_evaluation_review
from documents.teaching_evaluation_serializers import teaching_evaluation_to_web
from documents.storage import resolve_path
from documents.evaluation_eligibility import apply_eligibility_update, payload_for_api, reviewer_can_manage
from documents.teaching_effectiveness import indicator_folder_payload, teaching_effectiveness_payload
faculty_docs_bp = Blueprint("faculty_documents", __name__, url_prefix="/api/faculty/me/documents")
reviewer_docs_bp = Blueprint("reviewer_documents", __name__, url_prefix="/api/reviewer")
admin_docs_bp = Blueprint("admin_documents", __name__, url_prefix="/api/admin/documents")


def _file_api_base(role: str, public_id: str) -> str:
    if role == "faculty":
        return f"/api/faculty/me/documents/{public_id}"
    if role == "admin":
        return f"/api/admin/documents/{public_id}"
    return f"/api/reviewer/documents/{public_id}"


@faculty_docs_bp.get("")
@perm.roles_required(ROLE_FACULTY)
def faculty_list_documents():
    user = aq.current_faculty_user(get_jwt_identity())
    if not user or not user.faculty_profile:
        return jsonify({"message": "Faculty profile was not found."}), 404
    kra_id = (request.args.get("kraId") or request.args.get("kra_id") or "").strip() or None
    docs = doc_svc.list_faculty_documents(user.faculty_profile, kra_id=kra_id)
    rows = [
        document_to_web(d, api_base=_file_api_base("faculty", d.public_id))
        for d in docs
    ]
    stats = stats_from_documents(docs)
    return jsonify({"documents": rows, "stats": stats}), 200


@faculty_docs_bp.get("/criterion-c/summary")
@perm.roles_required(ROLE_FACULTY)
def faculty_criterion_c_summary():
    from documents.criterion_c_evidence.service import criterion_c_summary_for_faculty

    user = aq.current_faculty_user(get_jwt_identity())
    if not user or not user.faculty_profile:
        return jsonify({"message": "Faculty profile was not found."}), 404
    return jsonify(criterion_c_summary_for_faculty(user.faculty_profile.id)), 200


@faculty_docs_bp.get("/criterion-c/accomplishments")
@perm.roles_required(ROLE_FACULTY)
def faculty_criterion_c_accomplishments():
    from documents.criterion_c_evidence.service import list_faculty_accomplishments

    user = aq.current_faculty_user(get_jwt_identity())
    if not user or not user.faculty_profile:
        return jsonify({"message": "Faculty profile was not found."}), 404
    return jsonify({"accomplishments": list_faculty_accomplishments(user.faculty_profile.id)}), 200


@faculty_docs_bp.get("/kra2-a/summary")
@perm.roles_required(ROLE_FACULTY)
def faculty_kra2_a_summary():
    from documents.kra2_evidence.service import kra2_summary_for_faculty
    from kra_configuration.kra2_annex import CRITERION_A_ID

    user = aq.current_faculty_user(get_jwt_identity())
    if not user or not user.faculty_profile:
        return jsonify({"message": "Faculty profile was not found."}), 404
    return jsonify(kra2_summary_for_faculty(user.faculty_profile.id, criterion_id=CRITERION_A_ID)), 200


@faculty_docs_bp.get("/kra2/catalog")
@perm.roles_required(ROLE_FACULTY)
def faculty_kra2_catalog():
    from kra_configuration.kra2_indicator_registry import all_indicators, official_rules_verified

    return jsonify(
        {
            "officialRulesVerified": official_rules_verified(),
            "indicators": all_indicators(),
        }
    ), 200


def _faculty_kra2_criterion_summary(criterion_id: str):
    from documents.kra2_evidence.service import kra2_summary_for_faculty

    user = aq.current_faculty_user(get_jwt_identity())
    if not user or not user.faculty_profile:
        return jsonify({"message": "Faculty profile was not found."}), 404
    return jsonify(kra2_summary_for_faculty(user.faculty_profile.id, criterion_id=criterion_id)), 200


def _faculty_kra2_criterion_accomplishments(criterion_id: str):
    from documents.kra2_evidence.service import list_faculty_accomplishments

    user = aq.current_faculty_user(get_jwt_identity())
    if not user or not user.faculty_profile:
        return jsonify({"message": "Faculty profile was not found."}), 404
    return jsonify(
        {"accomplishments": list_faculty_accomplishments(user.faculty_profile.id, criterion_id=criterion_id)}
    ), 200


@faculty_docs_bp.get("/kra2-b/summary")
@perm.roles_required(ROLE_FACULTY)
def faculty_kra2_b_summary():
    from kra_configuration.kra2_annex import CRITERION_B_ID

    return _faculty_kra2_criterion_summary(CRITERION_B_ID)


@faculty_docs_bp.get("/kra2-b/accomplishments")
@perm.roles_required(ROLE_FACULTY)
def faculty_kra2_b_accomplishments():
    from kra_configuration.kra2_annex import CRITERION_B_ID

    return _faculty_kra2_criterion_accomplishments(CRITERION_B_ID)


@faculty_docs_bp.get("/kra2-c/summary")
@perm.roles_required(ROLE_FACULTY)
def faculty_kra2_c_summary():
    from kra_configuration.kra2_annex import CRITERION_C_ID

    return _faculty_kra2_criterion_summary(CRITERION_C_ID)


@faculty_docs_bp.get("/kra2-c/accomplishments")
@perm.roles_required(ROLE_FACULTY)
def faculty_kra2_c_accomplishments():
    from kra_configuration.kra2_annex import CRITERION_C_ID

    return _faculty_kra2_criterion_accomplishments(CRITERION_C_ID)


@faculty_docs_bp.get("/kra2-a/accomplishments")
@perm.roles_required(ROLE_FACULTY)
def faculty_kra2_a_accomplishments():
    from documents.kra2_evidence.service import list_faculty_accomplishments
    from kra_configuration.kra2_annex import CRITERION_A_ID

    user = aq.current_faculty_user(get_jwt_identity())
    if not user or not user.faculty_profile:
        return jsonify({"message": "Faculty profile was not found."}), 404
    return jsonify(
        {"accomplishments": list_faculty_accomplishments(user.faculty_profile.id, criterion_id=CRITERION_A_ID)}
    ), 200


@faculty_docs_bp.post("")
@perm.roles_required(ROLE_FACULTY)
def faculty_upload_document():
    user = aq.current_faculty_user(get_jwt_identity())
    if not user:
        return jsonify({"message": "Faculty account was not found."}), 404
    upload = request.files.get("file")
    if not upload:
        return jsonify({"message": "Choose a PDF or image file to upload."}), 400
    try:
        doc = doc_svc.create_upload(
            user,
            file=upload,
            title=(request.form.get("title") or "").strip(),
            kra_id=(request.form.get("kraId") or request.form.get("kra_id") or "").strip(),
            criterion_id=(request.form.get("criterionId") or request.form.get("criterion_id") or "").strip(),
            indicator_id=(request.form.get("indicatorId") or request.form.get("indicator_id") or "").strip(),
            replaces_public_id=(request.form.get("replacesDocumentId") or "").strip() or None,
            bundle_primary_public_id=(
                request.form.get("bundlePrimaryId")
                or request.form.get("bundle_primary_id")
                or ""
            ).strip()
            or None,
            evidence_slot=(request.form.get("evidenceSlot") or request.form.get("evidence_slot") or "").strip()
            or None,
        )
    except ValueError as error:
        code = str(error)
        messages = {
            "missing_file": "Choose a file to upload.",
            "empty_file": "The file is empty.",
            "file_too_large": "The file exceeds the 25 MB limit.",
            "unsupported_type": "Only PDF, Word (.docx), and image files are allowed.",
            "duplicate_upload": "This exact file is already uploaded for the selected criterion or indicator.",
            "invalid_pdf": "The file is not a valid PDF (missing PDF signature).",
            "invalid_file_content": "The file content does not match a supported PDF or image format.",
            "mime_content_mismatch": "The uploaded content type does not match the file contents.",
            "no_profile": "Faculty profile was not found.",
            "classification_required": "Select KRA and criterion before uploading.",
            "invalid_indicator": "Invalid indicator for this criterion.",
            "invalid_replace_target": "The document to replace was not found.",
            "not_replaceable": "This document cannot be replaced. Upload a new file only when revision is requested or OCR failed.",
            "primary_not_found": "The primary instructional material claim was not found.",
            "supporting_not_found": "The supporting document was not found.",
            "bundle_not_initialized": "Initialize the primary instructional material upload first.",
            "invalid_evidence_slot": "That evidence slot is not allowed for this Criterion B claim.",
            "duplicate_supporting_slot": "This file is already linked to that evidence slot.",
            "duplicate_primary_hash": "Supporting file cannot be identical to the primary material file.",
            "faculty_mismatch": "Supporting evidence must belong to the same faculty member.",
            "cannot_link_self": "A document cannot be linked to itself.",
            "accomplishment_not_ready_for_decision": (
                "Required evidence must be verified and policy flags resolved before approval."
            ),
            "review_rejection_remarks_required": "Provide reviewer remarks (at least 10 characters) when rejecting.",
            "review_approval_remarks_required": "Provide reviewer remarks (at least 10 characters) when approving.",
        }
        return jsonify({"message": messages.get(code, "Upload failed.")}), 400
    payload = document_to_web(
        doc,
        api_base=_file_api_base("faculty", doc.public_id),
        ocr_detail=False,
    )
    return jsonify({"document": payload}), 201


@faculty_docs_bp.get("/<public_id>")
@perm.roles_required(ROLE_FACULTY)
def faculty_get_document(public_id: str):
    user = aq.current_faculty_user(get_jwt_identity())
    doc = doc_svc.get_document(public_id)
    if not doc or not user or not doc_svc.faculty_owns(user, doc):
        return jsonify({"message": "Document was not found."}), 404
    return jsonify(
        document_to_web(
            doc,
            api_base=_file_api_base("faculty", doc.public_id),
            ocr_detail=True,
        )
    ), 200


@faculty_docs_bp.post("/<public_id>/ocr/retry")
@perm.roles_required(ROLE_FACULTY)
def faculty_retry_ocr(public_id: str):
    user = aq.current_faculty_user(get_jwt_identity())
    doc = doc_svc.get_document(public_id)
    if not doc or not user or not doc_svc.faculty_owns(user, doc):
        return jsonify({"message": "Document was not found."}), 404
    if doc.ocr_status == "processing":
        return jsonify({"message": "OCR is already in progress."}), 409
    job = doc_svc.retry_document_ocr(doc)
    if not job:
        return jsonify({"message": "OCR cannot run without a stored file."}), 400
    from documents.ocr.dispatch import maybe_dispatch_inline_worker
    from flask import current_app

    maybe_dispatch_inline_worker(current_app._get_current_object())
    return jsonify(
        {
            "document": document_to_web(
                doc,
                api_base=_file_api_base("faculty", doc.public_id),
                ocr_detail=True,
            ),
            "ocrJobId": job.id,
        }
    ), 202


@faculty_docs_bp.get("/<public_id>/file")
@perm.roles_required(ROLE_FACULTY)
def faculty_download_file(public_id: str):
    user = aq.current_faculty_user(get_jwt_identity())
    doc = doc_svc.get_document(public_id)
    if not doc or not user or not doc_svc.faculty_owns(user, doc):
        return jsonify({"message": "Document was not found."}), 404
    path = resolve_path(doc.file_path or "")
    if not path:
        return jsonify({"message": "File is not available."}), 404
    inline = request.args.get("disposition") == "inline"
    return send_file(
        path,
        mimetype=doc.mime_type or mimetypes.guess_type(doc.file_name or "")[0],
        as_attachment=not inline,
        download_name=doc.file_name or "document",
    )


@faculty_docs_bp.post("/<public_id>/submit")
@perm.roles_required(ROLE_FACULTY)
def faculty_submit_document(public_id: str):
    user = aq.current_faculty_user(get_jwt_identity())
    doc = doc_svc.get_document(public_id)
    if not doc or not user:
        return jsonify({"message": "Document was not found."}), 404
    try:
        doc_svc.submit_for_review(user, doc)
    except ValueError as error:
        if str(error) == "forbidden":
            return jsonify({"message": "You cannot submit this document."}), 403
        if str(error) == "not_submittable":
            return jsonify({"message": "Only draft or revision-requested documents can be submitted."}), 400
        return jsonify({"message": "Submit failed."}), 400
    return jsonify({
        "document": document_to_web(doc, api_base=_file_api_base("faculty", doc.public_id))
    }), 200


@faculty_docs_bp.delete("/<public_id>")
@perm.roles_required(ROLE_FACULTY)
def faculty_delete_document(public_id: str):
    user = aq.current_faculty_user(get_jwt_identity())
    if not user:
        return jsonify({"message": "Faculty account was not found."}), 404
    owned = doc_svc.get_owned_document(public_id, user)
    if owned and owned.deleted_at is not None:
        return jsonify({"ok": True, "message": "Document already removed."}), 200
    doc = doc_svc.get_document(public_id)
    if not doc or not doc_svc.faculty_owns(user, doc):
        return jsonify({"message": "Document was not found."}), 404
    try:
        doc_svc.soft_delete_faculty_document(user, doc)
    except ValueError as error:
        if str(error) == "not_deletable":
            return jsonify(
                {
                    "message": (
                        "This document cannot be deleted. Approved records require withdrawal; "
                        "other statuses may still be under review."
                    )
                }
            ), 400
        if str(error) == "forbidden":
            return jsonify({"message": "You cannot delete this document."}), 403
        return jsonify({"message": "Delete failed."}), 400
    return jsonify({"ok": True, "message": "Document removed from your active list."}), 200


@faculty_docs_bp.get("/<public_id>/criterion-b/evidence-bundle")
@perm.roles_required(ROLE_FACULTY)
def faculty_get_criterion_b_bundle(public_id: str):
    from documents.criterion_b_evidence.service import bundle_api_payload

    user = aq.current_faculty_user(get_jwt_identity())
    doc = doc_svc.get_owned_document(public_id, user) if user else None
    if not doc:
        return jsonify({"message": "Document was not found."}), 404
    return jsonify(bundle_api_payload(doc)), 200


@faculty_docs_bp.patch("/<public_id>/criterion-b/evidence-bundle")
@perm.roles_required(ROLE_FACULTY)
def faculty_patch_criterion_b_bundle(public_id: str):
    from documents.criterion_b_evidence.service import CriterionBEvidenceError, update_bundle_metadata

    user = aq.current_faculty_user(get_jwt_identity())
    if not user:
        return jsonify({"message": "Faculty account was not found."}), 404
    body = request.get_json(silent=True) or {}
    try:
        doc, validation = update_bundle_metadata(user, public_id, body)
    except CriterionBEvidenceError as error:
        codes = {
            "primary_not_found": (404, "Document was not found."),
            "bundle_not_initialized": (400, "Evidence bundle is not initialized for this claim."),
        }
        status, msg = codes.get(error.code, (400, "Update failed."))
        return jsonify({"message": msg}), status
    return jsonify(
        {
            "document": document_to_web(doc, api_base=_file_api_base("faculty", doc.public_id)),
            "validation": validation,
        }
    ), 200


@faculty_docs_bp.post("/<public_id>/criterion-b/link-supporting")
@perm.roles_required(ROLE_FACULTY)
def faculty_link_criterion_b_supporting(public_id: str):
    from documents.criterion_b_evidence.service import CriterionBEvidenceError, link_existing_supporting_document

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
    except CriterionBEvidenceError as error:
        messages = {
            "primary_not_found": "Primary claim was not found.",
            "supporting_not_found": "Supporting document was not found.",
            "duplicate_supporting_slot": "This file is already linked to that evidence slot.",
            "duplicate_primary_hash": "Supporting file cannot be identical to the primary material file.",
            "invalid_evidence_slot": "That evidence slot is not allowed for this Criterion B claim.",
            "cannot_link_self": "A document cannot be linked to itself.",
        }
        return jsonify({"message": messages.get(error.code, "Link failed.")}), 400
    return jsonify(
        {
            "document": document_to_web(primary, api_base=_file_api_base("faculty", primary.public_id)),
            "validation": validation,
        }
    ), 200


@faculty_docs_bp.get("/<public_id>/criterion-c/evidence-bundle")
@perm.roles_required(ROLE_FACULTY)
def faculty_get_criterion_c_bundle(public_id: str):
    from documents.criterion_c_evidence.service import bundle_api_payload

    user = aq.current_faculty_user(get_jwt_identity())
    doc = doc_svc.get_owned_document(public_id, user) if user else None
    if not doc:
        return jsonify({"message": "Document was not found."}), 404
    return jsonify(bundle_api_payload(doc)), 200


@faculty_docs_bp.patch("/<public_id>/criterion-c/evidence-bundle")
@perm.roles_required(ROLE_FACULTY)
def faculty_patch_criterion_c_bundle(public_id: str):
    from documents.criterion_c_evidence.service import CriterionCEvidenceError, update_bundle_metadata

    user = aq.current_faculty_user(get_jwt_identity())
    if not user:
        return jsonify({"message": "Faculty account was not found."}), 404
    body = request.get_json(silent=True) or {}
    try:
        doc, validation = update_bundle_metadata(user, public_id, body)
    except CriterionCEvidenceError as error:
        codes = {
            "primary_not_found": (404, "Document was not found."),
            "bundle_not_initialized": (400, "Evidence bundle is not initialized for this accomplishment."),
        }
        status, msg = codes.get(error.code, (400, "Update failed."))
        return jsonify({"message": msg}), status
    from documents.criterion_c_evidence.service import bundle_api_payload

    payload = bundle_api_payload(doc)
    return jsonify(
        {
            "document": document_to_web(doc, api_base=_file_api_base("faculty", doc.public_id)),
            "validation": validation,
            "bundle": payload.get("bundle"),
            "scoring": payload.get("scoring"),
            "ocrStatus": payload.get("ocrStatus"),
            "ocrExtraction": payload.get("ocrExtraction"),
        }
    ), 200


@faculty_docs_bp.post("/<public_id>/criterion-c/link-supporting")
@perm.roles_required(ROLE_FACULTY)
def faculty_link_criterion_c_supporting(public_id: str):
    from documents.criterion_c_evidence.service import CriterionCEvidenceError, link_existing_supporting_document

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
    except CriterionCEvidenceError as error:
        messages = {
            "primary_not_found": "Primary accomplishment was not found.",
            "supporting_not_found": "Supporting document was not found.",
            "invalid_evidence_slot": "That evidence slot is not allowed for this Criterion C accomplishment.",
            "duplicate_primary_hash": "Supporting file cannot be identical to the primary file.",
            "cannot_link_self": "A document cannot be linked to itself.",
        }
        return jsonify({"message": messages.get(error.code, "Link failed.")}), 400
    return jsonify(
        {
            "document": document_to_web(primary, api_base=_file_api_base("faculty", primary.public_id)),
            "validation": validation,
        }
    ), 200


def _kra2_evidence_error_response(error) -> tuple:
    from documents.kra2_evidence.service import Kra2EvidenceError

    if not isinstance(error, Kra2EvidenceError):
        raise error
    messages = {
        "primary_not_found": (404, "Document was not found."),
        "bundle_not_initialized": (400, "Evidence bundle is not initialized for this accomplishment."),
        "supporting_not_found": (404, "Supporting document was not found."),
        "invalid_evidence_slot": (400, "That evidence slot is not allowed for this KRA II accomplishment."),
        "duplicate_primary_hash": (400, "Supporting file cannot be identical to the primary file."),
        "cannot_link_self": (400, "A document cannot be linked to itself."),
        "forbidden": (403, "You do not have access to this document."),
        "cannot_verify_empty_slot": (400, "Cannot verify a slot with no linked document."),
        "invalid_slot_status": (400, "Unknown checklist status."),
        "accomplishment_not_ready_for_decision": (
            400,
            "Verify all required evidence and resolve blockers before approving.",
        ),
        "review_rejection_remarks_required": (
            400,
            "Provide reviewer remarks (at least 10 characters) when rejecting.",
        ),
        "review_approval_remarks_required": (
            400,
            "Provide reviewer remarks (at least 10 characters) when approving.",
        ),
        "assessed_points_invalid": (400, "Enter a valid assessed points value."),
        "assessed_points_exceeds_indicator_max": (
            400,
            "Assessed points exceed the published maximum for this indicator.",
        ),
        "assessed_points_exceeds_eligible": (
            400,
            "Assessed points exceed the system-calculated eligible amount for this accomplishment.",
        ),
        "assessed_points_not_adjustable": (
            400,
            "This indicator uses fixed official points. Confirm eligibility using the published score.",
        ),
        "score_adjustment_reason_required": (
            400,
            "Explain why the assessed score differs from the system-calculated eligible points.",
        ),
        "indicator_points_unknown": (400, "Published indicator points are not configured."),
        "accomplishment_already_finalized": (
            400,
            "This accomplishment is already approved. Reassessment requires an authorized workflow.",
        ),
    }
    status, msg = messages.get(error.code, (400, "Update failed."))
    return jsonify({"message": msg}), status


@faculty_docs_bp.get("/<public_id>/kra2/evidence-bundle")
@perm.roles_required(ROLE_FACULTY)
def faculty_get_kra2_bundle(public_id: str):
    from documents.kra2_evidence.service import bundle_api_payload

    user = aq.current_faculty_user(get_jwt_identity())
    doc = doc_svc.get_owned_document(public_id, user) if user else None
    if not doc:
        return jsonify({"message": "Document was not found."}), 404
    return jsonify(bundle_api_payload(doc)), 200


@faculty_docs_bp.patch("/<public_id>/kra2/evidence-bundle")
@perm.roles_required(ROLE_FACULTY)
def faculty_patch_kra2_bundle(public_id: str):
    from documents.kra2_evidence.service import Kra2EvidenceError, update_bundle_metadata, bundle_api_payload

    user = aq.current_faculty_user(get_jwt_identity())
    if not user:
        return jsonify({"message": "Faculty account was not found."}), 404
    body = request.get_json(silent=True) or {}
    try:
        doc, validation = update_bundle_metadata(user, public_id, body)
    except Kra2EvidenceError as error:
        return _kra2_evidence_error_response(error)
    payload = bundle_api_payload(doc)
    return jsonify(
        {
            "document": document_to_web(doc, api_base=_file_api_base("faculty", doc.public_id)),
            "validation": validation,
            "bundle": payload.get("bundle"),
            "scoring": payload.get("scoring"),
            "ocrStatus": payload.get("ocrStatus"),
            "ocrExtraction": payload.get("ocrExtraction"),
        }
    ), 200


@faculty_docs_bp.post("/<public_id>/kra2/link-supporting")
@perm.roles_required(ROLE_FACULTY)
def faculty_link_kra2_supporting(public_id: str):
    from documents.kra2_evidence.service import Kra2EvidenceError, link_existing_supporting_document

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
    except Kra2EvidenceError as error:
        return _kra2_evidence_error_response(error)
    return jsonify(
        {
            "document": document_to_web(primary, api_base=_file_api_base("faculty", primary.public_id)),
            "validation": validation,
        }
    ), 200


def _directory_params():
    args = request.args
    page = int(args.get("page") or 1)
    page_size = int(args.get("pageSize") or args.get("page_size") or 20)
    return {
        "page": page,
        "page_size": page_size,
        "query": (args.get("q") or args.get("query") or "").strip(),
        "department": (args.get("department") or "").strip(),
        "sort": (args.get("sort") or "name").strip(),
        "employee_no": (args.get("employeeNo") or args.get("employee_no") or "").strip(),
        "has_pending": (
            True
            if (args.get("hasPending") or "").lower() in ("1", "true", "yes")
            else False
            if (args.get("hasPending") or "").lower() in ("0", "false", "no")
            else None
        ),
    }


def _reviewer_filter_id(body_reviewer: str) -> int | None:
    if not body_reviewer:
        return None
    reviewer = User.query.filter_by(public_id=body_reviewer, role=ROLE_REVIEWER).first()
    return reviewer.id if reviewer else None


@reviewer_docs_bp.get("/me/documents/workspace")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_workspace_stats():
    user = aq.current_reviewer_user(get_jwt_identity())
    if not user:
        return jsonify({"message": "Reviewer account was not found."}), 404
    return jsonify({"stats": doc_dir.workspace_stats(reviewer_user_id=user.id)}), 200


@reviewer_docs_bp.get("/me/documents/faculty-directory")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_faculty_directory():
    user = aq.current_reviewer_user(get_jwt_identity())
    if not user:
        return jsonify({"message": "Reviewer account was not found."}), 404
    params = _directory_params()
    payload = doc_dir.paginated_faculty_directory(
        reviewer_user_id=user.id,
        **params,
    )
    return jsonify(payload), 200


@reviewer_docs_bp.get("/me/documents")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_list_documents():
    user = aq.current_reviewer_user(get_jwt_identity())
    if not user:
        return jsonify({"message": "Reviewer account was not found."}), 404
    faculty_id = (request.args.get("facultyId") or request.args.get("faculty_id") or "").strip()
    if faculty_id:
        docs = doc_svc.list_reviewer_documents_for_faculty(user, faculty_id)
    else:
        docs = doc_svc.list_reviewer_documents(user)
    from documents.set_sef_parent_review_sync import sync_set_sef_parent_reviews

    sync_set_sef_parent_reviews(docs, user, trigger="reviewer_documents_list")
    rows = [
        document_to_web(d, api_base=_file_api_base("reviewer", d.public_id))
        for d in docs
    ]
    return jsonify({"documents": rows, "stats": stats_from_documents(docs)}), 200


@reviewer_docs_bp.get("/me/review-queue")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_review_queue():
    user = aq.current_reviewer_user(get_jwt_identity())
    if not user:
        return jsonify({"message": "Reviewer account was not found."}), 404
    docs = doc_svc.queue_for_reviewer(user)
    rows = [
        document_to_web(d, api_base=_file_api_base("reviewer", d.public_id))
        for d in docs
    ]
    return jsonify({"documents": rows}), 200


@reviewer_docs_bp.get("/documents/<public_id>")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_get_document(public_id: str):
    user = aq.current_reviewer_user(get_jwt_identity())
    doc = doc_svc.get_document(public_id)
    if not doc or not user or not doc_svc.reviewer_can_access(user, doc):
        return jsonify({"message": "Document was not found."}), 404
    from documents.set_sef_parent_review_sync import try_sync_parent_document_review

    try_sync_parent_document_review(doc, user, trigger="reviewer_document_detail")
    return jsonify(
        document_to_web(
            doc,
            api_base=_file_api_base("reviewer", doc.public_id),
            ocr_detail=True,
        )
    ), 200


@reviewer_docs_bp.get("/documents/<public_id>/criterion-b/evidence-bundle")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_get_criterion_b_bundle(public_id: str):
    from documents.criterion_b_evidence.service import bundle_api_payload

    user = aq.current_reviewer_user(get_jwt_identity())
    doc = doc_svc.get_document(public_id)
    if not doc or not user or not doc_svc.reviewer_can_access(user, doc):
        return jsonify({"message": "Document was not found."}), 404
    return jsonify(bundle_api_payload(doc)), 200


@reviewer_docs_bp.patch("/documents/<public_id>/criterion-b/evidence-bundle")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_patch_criterion_b_checklist(public_id: str):
    from documents.criterion_b_evidence.service import CriterionBEvidenceError, reviewer_update_checklist_slot

    user = aq.current_reviewer_user(get_jwt_identity())
    body = request.get_json(silent=True) or {}
    slot_id = (body.get("evidenceSlot") or body.get("evidence_slot") or body.get("slotId") or "").strip()
    status = (body.get("status") or "").strip()
    rrpa_applicability = body.get("rrpaCopcApplicability")
    if rrpa_applicability is None:
        rrpa_applicability = body.get("rrpa_copc_applicability")
    disqualification = body.get("disqualificationConfirmed")
    if disqualification is None:
        disqualification = body.get("disqualification_confirmed")
    has_assessment = "reviewerAssessmentPoints" in body or "reviewerAssessmentJustification" in body
    has_remarks = bool(
        (body.get("remarks") or body.get("reviewerRemarks") or "").strip()
    )
    has_bundle_metadata = (
        "specializationAligned" in body
        or "completeSetDeclared" in body
        or disqualification is not None
    )
    confirm_contribution = body.get("confirmContributionPercentage") is True
    contribution_clarify = body.get("contributionNeedsClarification") is True
    if (
        not slot_id
        and rrpa_applicability is None
        and not has_assessment
        and not has_remarks
        and not has_bundle_metadata
        and not confirm_contribution
        and not contribution_clarify
    ):
        return jsonify(
            {
                "message": (
                    "evidenceSlot and status, rrpaCopcApplicability, reviewer remarks, "
                    "bundle metadata (specializationAligned), or reviewerAssessmentPoints "
                    "with justification is required."
                )
            }
        ), 400
    if has_assessment and "reviewerAssessmentPoints" not in body:
        return jsonify({"message": "reviewerAssessmentPoints is required with your justification."}), 400
    if slot_id and not status:
        return jsonify({"message": "status is required when evidenceSlot is provided."}), 400
    try:
        doc, validation = reviewer_update_checklist_slot(
            user,
            public_id,
            slot_id=slot_id or None,
            status=status or None,
            reviewer_note=(body.get("reviewerNote") or body.get("note") or ""),
            remarks=(body.get("remarks") or body.get("reviewerRemarks") or ""),
            disqualification_confirmed=disqualification if disqualification is not None else None,
            rrpa_copc_applicability=rrpa_applicability,
            rrpa_copc_applicability_note=(
                body.get("rrpaCopcApplicabilityNote")
                or body.get("rrpa_copc_applicability_note")
                or ""
            ),
            reviewer_assessment_points=body.get("reviewerAssessmentPoints"),
            reviewer_assessment_justification=(
                body.get("reviewerAssessmentJustification")
                or body.get("reviewer_assessment_justification")
                or ""
            ),
            specialization_aligned=body.get("specializationAligned")
            if "specializationAligned" in body
            else None,
            complete_set_declared=body.get("completeSetDeclared")
            if "completeSetDeclared" in body
            else None,
            confirm_contribution_percentage=confirm_contribution,
            confirmed_contribution_percent=body.get("confirmedContributionPercent"),
            contribution_needs_clarification=contribution_clarify,
            contribution_clarification_reason=(
                body.get("contributionClarificationReason")
                or body.get("contribution_clarification_reason")
                or ""
            ),
        )
    except CriterionBEvidenceError as error:
        codes = {
            "forbidden": (403, "You do not have access to this document."),
            "bundle_not_initialized": (400, "Evidence bundle is not initialized."),
            "cannot_verify_empty_slot": (400, "Cannot verify a slot with no linked document."),
            "invalid_slot_status": (400, "Unknown checklist status."),
            "invalid_rrpa_copc_applicability": (400, "Unknown RRPA/COPC applicability value."),
            "rrpa_copc_exemption_note_required": (
                400,
                "A reviewer note is required when RRPA/COPC is marked not applicable.",
            ),
            "rrpa_applicability_program_only": (
                400,
                "RRPA/COPC applicability applies to academic program claims only.",
            ),
            "reviewer_assessment_justification_required": (
                400,
                "Please explain why you chose this assessment score (at least 10 characters).",
            ),
            "reviewer_assessment_points_invalid": (400, "Enter a valid assessment score (0 or higher)."),
            "reviewer_assessment_points_exceeds_published_max": (
                400,
                "Assessment score exceeds the published maximum for this indicator.",
            ),
            "reviewer_assessment_points_required": (
                400,
                "reviewerAssessmentPoints is required when saving an assessment.",
            ),
            "reviewer_assessment_not_ready": (
                400,
                "Mandatory evidence is not complete or verified yet. Save document verifications first.",
            ),
            "contribution_confirmation_required": (
                400,
                "Confirm the contribution percentage against Annex C before finalizing the assessment.",
            ),
            "contribution_confirmation_required_for_assessment_change": (
                400,
                "Confirm the contribution percentage against Annex C before changing this assessment.",
            ),
            "contribution_percent_mismatch_unresolved": (
                400,
                "The recorded contribution percentage does not match the reviewed Annex C. Resolve the difference before finalizing the assessment.",
            ),
            "contribution_confirmation_incomplete": (
                400,
                "Contribution confirmation is incomplete.",
            ),
            "contribution_percent_required_on_claim": (
                400,
                "Recorded contribution percentage is required on this co-author claim.",
            ),
            "contribution_confirmation_percent_invalid": (
                400,
                "Enter a valid contribution percentage (0–100).",
            ),
            "annex_c_document_required": (
                400,
                "Link and verify the Annex C contribution document before confirming the percentage.",
            ),
            "contribution_mismatch_reason_required": (
                400,
                "Explain the mismatch between the recorded percentage and Annex C.",
            ),
            "contribution_clarification_reason_required": (
                400,
                "Provide a brief clarification (at least 10 characters).",
            ),
        }
        status_code, msg = codes.get(error.code, (400, "Update failed."))
        return jsonify({"message": msg}), status_code
    from documents.criterion_b_evidence.service import bundle_api_payload

    bundle_payload = bundle_api_payload(doc)
    return jsonify(
        {
            "document": document_to_web(doc, api_base=_file_api_base("reviewer", doc.public_id), ocr_detail=True),
            "validation": validation,
            "contributionVerification": bundle_payload.get("contributionVerification"),
            "scoring": bundle_payload.get("scoring"),
            "crossKraWarnings": bundle_payload.get("crossKraWarnings") or [],
        }
    ), 200


@reviewer_docs_bp.get("/documents/<public_id>/criterion-c/evidence-bundle")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_get_criterion_c_bundle(public_id: str):
    from documents.criterion_c_evidence.service import bundle_api_payload

    user = aq.current_reviewer_user(get_jwt_identity())
    doc = doc_svc.get_document(public_id)
    if not doc or not user or not doc_svc.reviewer_can_access(user, doc):
        return jsonify({"message": "Document was not found."}), 404
    return jsonify(bundle_api_payload(doc)), 200


@reviewer_docs_bp.patch("/documents/<public_id>/criterion-c/evidence-bundle")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_patch_criterion_c_bundle(public_id: str):
    from documents.criterion_c_evidence.service import CriterionCEvidenceError, reviewer_update_criterion_c

    user = aq.current_reviewer_user(get_jwt_identity())
    body = request.get_json(silent=True) or {}
    slot_id = (body.get("evidenceSlot") or body.get("evidence_slot") or body.get("slotId") or "").strip()
    status = (body.get("status") or "").strip()
    review_status = (body.get("reviewStatus") or body.get("review_status") or "").strip() or None
    has_remarks = bool((body.get("remarks") or body.get("reviewerRemarks") or "").strip())
    metadata_keys = (
        "projectTitle",
        "studentNames",
        "studentGroupLabel",
        "academicYear",
        "completionDate",
    )
    metadata_patch = {k: body[k] for k in metadata_keys if k in body}
    has_metadata = bool(metadata_patch)
    if not slot_id and not review_status and not has_remarks and not has_metadata:
        return jsonify(
            {
                "message": (
                    "evidenceSlot and status, reviewStatus (approved/rejected/pending), "
                    "research metadata fields, or reviewer remarks is required."
                )
            }
        ), 400
    if slot_id and not status:
        return jsonify({"message": "status is required when evidenceSlot is provided."}), 400
    try:
        doc, validation = reviewer_update_criterion_c(
            user,
            public_id,
            slot_id=slot_id or None,
            status=status or None,
            reviewer_note=(body.get("reviewerNote") or body.get("note") or ""),
            review_status=review_status,
            remarks=(body.get("remarks") or body.get("reviewerRemarks") or ""),
            assessed_points=body.get("assessedPoints") or body.get("assessed_points"),
            metadata=metadata_patch if has_metadata else None,
        )
    except CriterionCEvidenceError as error:
        codes = {
            "forbidden": (403, "You do not have access to this document."),
            "bundle_not_initialized": (400, "Evidence bundle is not initialized."),
            "cannot_verify_empty_slot": (400, "Cannot verify a slot with no linked document."),
            "invalid_slot_status": (400, "Unknown checklist status."),
            "accomplishment_not_ready_for_decision": (
                400,
                "Verify all required evidence and resolve policy flags before approving.",
            ),
            "review_rejection_remarks_required": (
                400,
                "Provide reviewer remarks (at least 10 characters) when rejecting.",
            ),
            "review_approval_remarks_required": (
                400,
                "Provide reviewer remarks (at least 10 characters) when approving.",
            ),
            "assessed_points_invalid": (400, "Enter a valid assessed points value."),
            "assessed_points_exceeds_annex_max": (
                400,
                "Assessed points exceed the published Annex A maximum for this indicator.",
            ),
        }
        status_code, msg = codes.get(error.code, (400, "Update failed."))
        return jsonify({"message": msg}), status_code
    from documents.criterion_c_evidence.service import bundle_api_payload

    return jsonify(
        {
            "document": document_to_web(doc, api_base=_file_api_base("reviewer", doc.public_id), ocr_detail=True),
            "validation": validation,
            "scoring": bundle_api_payload(doc).get("scoring"),
        }
    ), 200


def _reviewer_faculty_profile_or_404(user, faculty_public_id: str) -> FacultyProfile | None:
    profile = FacultyProfile.query.filter_by(public_id=faculty_public_id).first()
    if not profile or not user or profile.reviewer_user_id != user.id:
        return None
    return profile


@reviewer_docs_bp.get("/documents/<public_id>/kra2/evidence-bundle")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_get_kra2_bundle(public_id: str):
    from documents.kra2_evidence.service import bundle_api_payload

    user = aq.current_reviewer_user(get_jwt_identity())
    doc = doc_svc.get_document(public_id)
    if not doc or not user or not doc_svc.reviewer_can_access(user, doc):
        return jsonify({"message": "Document was not found."}), 404
    return jsonify(bundle_api_payload(doc)), 200


@reviewer_docs_bp.patch("/documents/<public_id>/kra2/evidence-bundle")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_patch_kra2_bundle(public_id: str):
    from documents.kra2_evidence.service import Kra2EvidenceError, reviewer_update_kra2, bundle_api_payload

    user = aq.current_reviewer_user(get_jwt_identity())
    body = request.get_json(silent=True) or {}
    slot_id = (body.get("evidenceSlot") or body.get("evidence_slot") or body.get("slotId") or "").strip()
    status = (body.get("status") or "").strip()
    review_status = (body.get("reviewStatus") or body.get("review_status") or "").strip() or None
    has_remarks = bool((body.get("remarks") or body.get("reviewerRemarks") or "").strip())
    metadata_keys = (
        "outputTitle",
        "outputVenue",
        "journalTitle",
        "authorsLine",
        "publicationDate",
        "publicationReference",
        "registrationNumber",
        "registrationDate",
        "citationContext",
        "indexingAttestation",
        "declaredContributionPercent",
    )
    metadata_patch = {k: body[k] for k in metadata_keys if k in body}
    if body.get("confirmReviewerMetadata") is True:
        metadata_patch["confirmReviewerMetadata"] = True
    has_metadata = bool(metadata_patch)
    if not slot_id and not review_status and not has_remarks and not has_metadata:
        return jsonify({"message": "evidenceSlot/status, reviewStatus, metadata, or remarks required."}), 400
    if slot_id and not status:
        return jsonify({"message": "status is required when evidenceSlot is provided."}), 400
    try:
        doc, validation = reviewer_update_kra2(
            user,
            public_id,
            slot_id=slot_id or None,
            status=status or None,
            reviewer_note=(body.get("reviewerNote") or body.get("note") or ""),
            review_status=review_status,
            remarks=(body.get("remarks") or body.get("reviewerRemarks") or ""),
            assessed_points=body.get("assessedPoints") or body.get("assessed_points"),
            score_adjustment_reason=(
                body.get("scoreAdjustmentReason") or body.get("score_adjustment_reason") or ""
            ),
            metadata=metadata_patch if has_metadata else None,
        )
    except Kra2EvidenceError as error:
        return _kra2_evidence_error_response(error)
    payload = bundle_api_payload(doc)
    return jsonify(
        {
            "document": document_to_web(doc, api_base=_file_api_base("reviewer", doc.public_id), ocr_detail=True),
            "validation": validation,
            "bundle": payload.get("bundle"),
            "scoring": payload.get("scoring"),
            "ocrExtraction": payload.get("ocrExtraction"),
        }
    ), 200


@reviewer_docs_bp.get("/me/faculty/<faculty_public_id>/kra2-a/summary")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_kra2_a_summary(faculty_public_id: str):
    from documents.kra2_evidence.service import kra2_summary_for_faculty
    from kra_configuration.kra2_annex import CRITERION_A_ID

    user = aq.current_reviewer_user(get_jwt_identity())
    if not user:
        return jsonify({"message": "Reviewer account was not found."}), 404
    profile = _reviewer_faculty_profile_or_404(user, faculty_public_id)
    if not profile:
        return jsonify({"message": "Faculty assignment was not found."}), 404
    return jsonify(kra2_summary_for_faculty(profile.id, criterion_id=CRITERION_A_ID)), 200


@reviewer_docs_bp.get("/me/faculty/<faculty_public_id>/kra2-a/accomplishments")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_kra2_a_accomplishments(faculty_public_id: str):
    from documents.kra2_evidence.service import list_faculty_accomplishments
    from kra_configuration.kra2_annex import CRITERION_A_ID

    user = aq.current_reviewer_user(get_jwt_identity())
    if not user:
        return jsonify({"message": "Reviewer account was not found."}), 404
    profile = _reviewer_faculty_profile_or_404(user, faculty_public_id)
    if not profile:
        return jsonify({"message": "Faculty assignment was not found."}), 404
    return jsonify(
        {"accomplishments": list_faculty_accomplishments(profile.id, criterion_id=CRITERION_A_ID)}
    ), 200


def _reviewer_kra2_criterion_summary(faculty_public_id: str, criterion_id: str):
    from documents.kra2_evidence.service import kra2_summary_for_faculty

    user = aq.current_reviewer_user(get_jwt_identity())
    if not user:
        return jsonify({"message": "Reviewer account was not found."}), 404
    profile = _reviewer_faculty_profile_or_404(user, faculty_public_id)
    if not profile:
        return jsonify({"message": "Faculty assignment was not found."}), 404
    return jsonify(kra2_summary_for_faculty(profile.id, criterion_id=criterion_id)), 200


def _reviewer_kra2_criterion_accomplishments(faculty_public_id: str, criterion_id: str):
    from documents.kra2_evidence.service import list_faculty_accomplishments

    user = aq.current_reviewer_user(get_jwt_identity())
    if not user:
        return jsonify({"message": "Reviewer account was not found."}), 404
    profile = _reviewer_faculty_profile_or_404(user, faculty_public_id)
    if not profile:
        return jsonify({"message": "Faculty assignment was not found."}), 404
    return jsonify(
        {"accomplishments": list_faculty_accomplishments(profile.id, criterion_id=criterion_id)}
    ), 200


@reviewer_docs_bp.get("/me/faculty/<faculty_public_id>/kra2-b/summary")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_kra2_b_summary(faculty_public_id: str):
    from kra_configuration.kra2_annex import CRITERION_B_ID

    return _reviewer_kra2_criterion_summary(faculty_public_id, CRITERION_B_ID)


@reviewer_docs_bp.get("/me/faculty/<faculty_public_id>/kra2-b/accomplishments")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_kra2_b_accomplishments(faculty_public_id: str):
    from kra_configuration.kra2_annex import CRITERION_B_ID

    return _reviewer_kra2_criterion_accomplishments(faculty_public_id, CRITERION_B_ID)


@reviewer_docs_bp.get("/me/faculty/<faculty_public_id>/kra2-c/summary")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_kra2_c_summary(faculty_public_id: str):
    from kra_configuration.kra2_annex import CRITERION_C_ID

    return _reviewer_kra2_criterion_summary(faculty_public_id, CRITERION_C_ID)


@reviewer_docs_bp.get("/me/faculty/<faculty_public_id>/kra2-c/accomplishments")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_kra2_c_accomplishments(faculty_public_id: str):
    from kra_configuration.kra2_annex import CRITERION_C_ID

    return _reviewer_kra2_criterion_accomplishments(faculty_public_id, CRITERION_C_ID)


@reviewer_docs_bp.get("/me/faculty/<faculty_public_id>/criterion-c/summary")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_criterion_c_summary(faculty_public_id: str):
    from documents.criterion_c_evidence.service import criterion_c_summary_for_faculty

    user = aq.current_reviewer_user(get_jwt_identity())
    if not user:
        return jsonify({"message": "Reviewer account was not found."}), 404
    profile = _reviewer_faculty_profile_or_404(user, faculty_public_id)
    if not profile:
        return jsonify({"message": "Faculty assignment was not found."}), 404
    return jsonify(criterion_c_summary_for_faculty(profile.id)), 200


@reviewer_docs_bp.get("/me/faculty/<faculty_public_id>/criterion-c/accomplishments")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_criterion_c_accomplishments(faculty_public_id: str):
    from documents.criterion_c_evidence.service import list_faculty_accomplishments

    user = aq.current_reviewer_user(get_jwt_identity())
    if not user:
        return jsonify({"message": "Reviewer account was not found."}), 404
    profile = _reviewer_faculty_profile_or_404(user, faculty_public_id)
    if not profile:
        return jsonify({"message": "Faculty assignment was not found."}), 404
    return jsonify({"accomplishments": list_faculty_accomplishments(profile.id)}), 200


@reviewer_docs_bp.post("/documents/<public_id>/ocr/retry")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_retry_ocr(public_id: str):
    user = aq.current_reviewer_user(get_jwt_identity())
    doc = doc_svc.get_document(public_id)
    if not doc or not user or not doc_svc.reviewer_can_access(user, doc):
        return jsonify({"message": "Document was not found."}), 404
    if doc.ocr_status == "processing":
        return jsonify({"message": "OCR is already in progress."}), 409
    job = doc_svc.retry_document_ocr(doc)
    if not job:
        return jsonify({"message": "OCR cannot run without a stored file."}), 400
    from documents.ocr.dispatch import maybe_dispatch_inline_worker
    from flask import current_app

    maybe_dispatch_inline_worker(current_app._get_current_object())
    return jsonify(
        {
            "document": document_to_web(
                doc,
                api_base=_file_api_base("reviewer", doc.public_id),
                ocr_detail=True,
            ),
            "ocrJobId": job.id,
        }
    ), 202


@reviewer_docs_bp.get("/documents/<public_id>/file")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_download_file(public_id: str):
    user = aq.current_reviewer_user(get_jwt_identity())
    doc = doc_svc.get_document(public_id)
    if not doc or not user or not doc_svc.reviewer_can_access(user, doc):
        return jsonify({"message": "Document was not found."}), 404
    path = resolve_path(doc.file_path or "")
    if not path:
        return jsonify({"message": "File is not available."}), 404
    inline = request.args.get("disposition") == "inline"
    return send_file(
        path,
        mimetype=doc.mime_type or mimetypes.guess_type(doc.file_name or "")[0],
        as_attachment=not inline,
        download_name=doc.file_name or "document",
    )


@reviewer_docs_bp.post("/documents/<public_id>/teaching-evaluations/<tev_public_id>/review")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_review_teaching_evaluation(public_id: str, tev_public_id: str):
    user = aq.current_reviewer_user(get_jwt_identity())
    doc = doc_svc.get_document(public_id)
    if not doc or not user or not doc_svc.reviewer_can_access(user, doc):
        return jsonify({"message": "Document was not found."}), 404
    tev = DocumentTeachingEvaluation.query.filter_by(
        public_id=tev_public_id, document_id=doc.id
    ).first()
    if not tev:
        return jsonify({"message": "Teaching evaluation record was not found."}), 404
    body = request.get_json(silent=True) or {}
    try:
        tev = apply_teaching_evaluation_review(user, doc, tev, body)
    except ValueError as error:
        code = str(error)
        messages = {
            "forbidden": "This document is not assigned to you.",
            "invalid_decision": "Unknown review decision.",
            "remarks_required": "Enter remarks explaining the revision or rejection (min. 8 characters).",
            "reason_required": "Enter a reason for corrections (min. 8 characters).",
            "no_changes": "Select a decision or change at least one field.",
            "invalid_rating_scale": "Rating scale must be a number.",
            "not_found": "Teaching evaluation record was not found.",
        }
        return jsonify({"message": messages.get(code, "Review could not be saved.")}), 400
    return jsonify(
        {
            "teachingEvaluation": teaching_evaluation_to_web(tev, doc, doc.faculty_profile),
            "document": document_to_web(
                doc,
                api_base=_file_api_base("reviewer", doc.public_id),
                ocr_detail=True,
            ),
        }
    ), 200


@reviewer_docs_bp.post("/documents/<public_id>/correct-metadata")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_correct_metadata(public_id: str):
    user = aq.current_reviewer_user(get_jwt_identity())
    doc = doc_svc.get_document(public_id)
    if not doc or not user or not doc_svc.reviewer_can_access(user, doc):
        return jsonify({"message": "Document was not found."}), 404
    body = request.get_json(silent=True) or {}
    try:
        doc = apply_metadata_correction(user, doc, body)
    except ValueError as error:
        code = str(error)
        messages = {
            "reason_required": "Enter a brief reason for the correction (at least 8 characters).",
            "no_changes": "Change at least one extracted field before saving.",
        }
        return jsonify({"message": messages.get(code, "Correction could not be saved.")}), 400
    payload = document_to_web(
        doc,
        api_base=_file_api_base("reviewer", doc.public_id),
        ocr_detail=True,
    )
    return jsonify({"document": payload}), 200


@reviewer_docs_bp.get("/me/teaching-effectiveness")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_teaching_effectiveness():
    user = aq.current_reviewer_user(get_jwt_identity())
    if not user:
        return jsonify({"message": "Reviewer account was not found."}), 404
    faculty_public = (request.args.get("facultyId") or request.args.get("faculty_id") or "").strip()
    if not faculty_public:
        return jsonify({"message": "facultyId is required."}), 400
    profile = FacultyProfile.query.filter_by(public_id=faculty_public).first()
    if not profile or profile.reviewer_user_id != user.id:
        return jsonify({"message": "Faculty assignment was not found."}), 404
    resp = jsonify(teaching_effectiveness_payload(profile))
    resp.headers["Cache-Control"] = "no-store"
    return resp, 200


@reviewer_docs_bp.get("/me/faculty/<faculty_public_id>/evaluation-eligibility")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_get_evaluation_eligibility(faculty_public_id: str):
    user = aq.current_reviewer_user(get_jwt_identity())
    if not user:
        return jsonify({"message": "Reviewer account was not found."}), 404
    profile = FacultyProfile.query.filter_by(public_id=faculty_public_id).first()
    if not profile or not reviewer_can_manage(user, profile):
        return jsonify({"message": "Faculty assignment was not found."}), 404
    return jsonify(payload_for_api(profile)), 200


@reviewer_docs_bp.put("/me/faculty/<faculty_public_id>/evaluation-eligibility")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_put_evaluation_eligibility(faculty_public_id: str):
    user = aq.current_reviewer_user(get_jwt_identity())
    if not user:
        return jsonify({"message": "Reviewer account was not found."}), 404
    profile = FacultyProfile.query.filter_by(public_id=faculty_public_id).first()
    if not profile or not reviewer_can_manage(user, profile):
        return jsonify({"message": "Faculty assignment was not found."}), 404
    body = request.get_json(silent=True) or {}
    try:
        profile = apply_eligibility_update(user, profile, body)
    except ValueError as error:
        code = str(error)
        messages = {
            "forbidden": "This faculty member is not assigned to you.",
            "justification_required": "Enter a justification (at least 16 characters).",
            "invalid_section10_code": "Select a valid Section 10 circumstance from the catalog.",
            "evidence_attestation_required": "Confirm supporting evidence is on file before verification.",
            "evidence_summary_required": "Summarize the supporting evidence on file (at least 16 characters).",
            "eligible_semester_count_required": "Enter the verified eligible semester count for this circumstance.",
            "eligible_semester_count_too_high": "Eligible semester count cannot exceed the standard six-semester period.",
        }
        return jsonify({"message": messages.get(code, "Eligibility was not saved.")}), 400
    return jsonify(payload_for_api(profile)), 200


@reviewer_docs_bp.get("/me/set-sef-indicator")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_set_sef_indicator():
    user = aq.current_reviewer_user(get_jwt_identity())
    if not user:
        return jsonify({"message": "Reviewer account was not found."}), 404
    faculty_public = (request.args.get("facultyId") or request.args.get("faculty_id") or "").strip()
    indicator_id = (request.args.get("indicatorId") or request.args.get("indicator_id") or "").strip()
    if not faculty_public or not indicator_id:
        return jsonify({"message": "facultyId and indicatorId are required."}), 400
    if indicator_id not in ("kra1-a-student", "kra1-a-supervisor"):
        return jsonify({"message": "Indicator is not a SET/SEF teaching effectiveness indicator."}), 400
    profile = FacultyProfile.query.filter_by(public_id=faculty_public).first()
    if not profile or profile.reviewer_user_id != user.id:
        return jsonify({"message": "Faculty assignment was not found."}), 404
    resp = jsonify(indicator_folder_payload(profile, indicator_id))
    resp.headers["Cache-Control"] = "no-store"
    return resp, 200


@reviewer_docs_bp.post("/documents/<public_id>/review")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_review_document(public_id: str):
    user = aq.current_reviewer_user(get_jwt_identity())
    doc = doc_svc.get_document(public_id)
    if not doc or not user:
        return jsonify({"message": "Document was not found."}), 404
    body = request.get_json(silent=True) or {}
    decision = body.get("decision") or body.get("action") or ""
    remarks = body.get("remarks") or body.get("feedback") or ""
    try:
        doc_svc.apply_review_decision(user, doc, decision=decision, remarks=remarks)
    except ValueError as error:
        code = str(error)
        if code == "forbidden":
            return jsonify({"message": "This document is not assigned to you."}), 403
        if code == "remarks_required":
            return jsonify({"message": "Enter remarks explaining the revision or rejection."}), 400
        if code == "invalid_decision":
            return jsonify({"message": "Unknown review decision."}), 400
        return jsonify({"message": "Review could not be saved."}), 400
    payload = document_to_web(doc, api_base=_file_api_base("reviewer", doc.public_id))
    return jsonify({"document": payload}), 200


@reviewer_docs_bp.put("/documents/<public_id>")
@perm.roles_required(ROLE_REVIEWER)
def reviewer_update_document(public_id: str):
    """Legacy web review panel may PUT full document payloads."""
    user = aq.current_reviewer_user(get_jwt_identity())
    doc = doc_svc.get_document(public_id)
    if not doc or not user or not doc_svc.reviewer_can_access(user, doc):
        return jsonify({"message": "Document was not found."}), 404
    body = request.get_json(silent=True) or {}
    doc = doc_svc.patch_from_web_payload(doc, body)
    return jsonify(
        document_to_web(doc, api_base=_file_api_base("reviewer", doc.public_id))
    ), 200


@admin_docs_bp.get("/workspace")
@perm.roles_required(ROLE_ADMINISTRATOR)
def admin_workspace_stats():
    return jsonify({"stats": doc_dir.workspace_stats()}), 200


@admin_docs_bp.get("/faculty-directory")
@perm.roles_required(ROLE_ADMINISTRATOR)
def admin_faculty_directory():
    params = _directory_params()
    reviewer_public = (request.args.get("reviewerId") or request.args.get("reviewer_id") or "").strip()
    payload = doc_dir.paginated_faculty_directory(
        reviewer_filter_user_id=_reviewer_filter_id(reviewer_public),
        **params,
    )
    return jsonify(payload), 200


@admin_docs_bp.get("/stats")
@perm.roles_required(ROLE_ADMINISTRATOR)
def admin_document_stats():
    return jsonify({"stats": doc_dir.workspace_stats()}), 200


@admin_docs_bp.get("")
@perm.roles_required(ROLE_ADMINISTRATOR)
def admin_list_documents():
    faculty_id = (request.args.get("facultyId") or request.args.get("faculty_id") or "").strip() or None
    docs = doc_svc.list_admin_documents(faculty_public_id=faculty_id)
    from documents.set_sef_parent_review_sync import sync_set_sef_parent_reviews

    sync_set_sef_parent_reviews(docs, None, trigger="admin_documents_list")
    rows = [
        document_to_web(d, api_base=_file_api_base("admin", d.public_id))
        for d in docs
    ]
    return jsonify({"documents": rows, "stats": stats_from_documents(docs)}), 200


@admin_docs_bp.get("/faculty/<faculty_public_id>/evaluation-eligibility")
@perm.roles_required(ROLE_ADMINISTRATOR)
def admin_get_evaluation_eligibility(faculty_public_id: str):
    profile = FacultyProfile.query.filter_by(public_id=faculty_public_id).first()
    if not profile:
        return jsonify({"message": "Faculty profile was not found."}), 404
    return jsonify(payload_for_api(profile)), 200


@admin_docs_bp.get("/faculty/<faculty_public_id>/teaching-effectiveness")
@perm.roles_required(ROLE_ADMINISTRATOR)
def admin_faculty_teaching_effectiveness(faculty_public_id: str):
    profile = FacultyProfile.query.filter_by(public_id=faculty_public_id).first()
    if not profile:
        return jsonify({"message": "Faculty profile was not found."}), 404
    resp = jsonify(teaching_effectiveness_payload(profile))
    resp.headers["Cache-Control"] = "no-store"
    return resp, 200


@admin_docs_bp.get("/faculty/<faculty_public_id>/set-sef-indicator")
@perm.roles_required(ROLE_ADMINISTRATOR)
def admin_set_sef_indicator(faculty_public_id: str):
    indicator_id = (request.args.get("indicatorId") or request.args.get("indicator_id") or "").strip()
    if indicator_id not in ("kra1-a-student", "kra1-a-supervisor"):
        return jsonify({"message": "Indicator is not a SET/SEF teaching effectiveness indicator."}), 400
    profile = FacultyProfile.query.filter_by(public_id=faculty_public_id).first()
    if not profile:
        return jsonify({"message": "Faculty profile was not found."}), 404
    resp = jsonify(indicator_folder_payload(profile, indicator_id))
    resp.headers["Cache-Control"] = "no-store"
    return resp, 200


@admin_docs_bp.get("/<public_id>")
@perm.roles_required(ROLE_ADMINISTRATOR)
def admin_get_document(public_id: str):
    doc = doc_svc.get_document(public_id)
    if not doc:
        return jsonify({"message": "Document was not found."}), 404
    return jsonify(
        document_to_web(
            doc,
            api_base=_file_api_base("admin", doc.public_id),
            ocr_detail=True,
        )
    ), 200


@admin_docs_bp.post("/<public_id>/ocr/retry")
@perm.roles_required(ROLE_ADMINISTRATOR)
def admin_retry_ocr(public_id: str):
    doc = doc_svc.get_document(public_id)
    if not doc:
        return jsonify({"message": "Document was not found."}), 404
    if doc.ocr_status == "processing":
        return jsonify({"message": "OCR is already in progress."}), 409
    job = doc_svc.retry_document_ocr(doc)
    if not job:
        return jsonify({"message": "OCR cannot run without a stored file."}), 400
    from documents.ocr.dispatch import maybe_dispatch_inline_worker
    from flask import current_app

    maybe_dispatch_inline_worker(current_app._get_current_object())
    return jsonify(
        {
            "document": document_to_web(
                doc,
                api_base=_file_api_base("admin", doc.public_id),
                ocr_detail=True,
            ),
            "ocrJobId": job.id,
        }
    ), 202


@admin_docs_bp.get("/<public_id>/file")
@perm.roles_required(ROLE_ADMINISTRATOR)
def admin_download_file(public_id: str):
    doc = doc_svc.get_document(public_id)
    if not doc:
        return jsonify({"message": "Document was not found."}), 404
    path = resolve_path(doc.file_path or "")
    if not path:
        return jsonify({"message": "File is not available."}), 404
    inline = request.args.get("disposition") == "inline"
    return send_file(
        path,
        mimetype=doc.mime_type or mimetypes.guess_type(doc.file_name or "")[0],
        as_attachment=not inline,
        download_name=doc.file_name or "document",
    )
