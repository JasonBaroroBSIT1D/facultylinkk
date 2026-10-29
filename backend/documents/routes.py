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
from models import FacultyProfile, User
from documents.metadata_correction import apply_metadata_correction
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
        )
    except ValueError as error:
        code = str(error)
        messages = {
            "missing_file": "Choose a file to upload.",
            "empty_file": "The file is empty.",
            "file_too_large": "The file exceeds the 25 MB limit.",
            "unsupported_type": "Only PDF, Word (.docx), and image files are allowed.",
            "duplicate_upload": "This exact file is already uploaded for the selected indicator.",
            "invalid_pdf": "The file is not a valid PDF (missing PDF signature).",
            "invalid_file_content": "The file content does not match a supported PDF or image format.",
            "mime_content_mismatch": "The uploaded content type does not match the file contents.",
            "no_profile": "Faculty profile was not found.",
            "classification_required": "Select KRA, criterion, and indicator before uploading.",
            "invalid_replace_target": "The document to replace was not found.",
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
    doc = doc_svc.get_document(public_id)
    if not doc or not user:
        return jsonify({"message": "Document was not found."}), 404
    try:
        doc_svc.soft_delete_faculty_document(user, doc)
    except ValueError as error:
        if str(error) == "not_deletable":
            return jsonify({"message": "Only draft uploads can be deleted."}), 400
        return jsonify({"message": "Delete failed."}), 403
    return jsonify({"ok": True}), 200


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
    return jsonify(
        document_to_web(
            doc,
            api_base=_file_api_base("reviewer", doc.public_id),
            ocr_detail=True,
        )
    ), 200


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
