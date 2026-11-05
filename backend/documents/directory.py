"""Paginated faculty directories for the Evidence Workspace."""

from __future__ import annotations

from sqlalchemy import case, desc, func, or_

from extensions import db
from models import Document, FacultyProfile, User

from documents.serializers import stats_from_documents
from documents.set_sef_parent_context import workspace_teaching_evaluation_stats
from documents.status_map import is_awaiting_review

_PENDING = ("pending_review", "reviewer_required", "needs_revision")
_APPROVED = ("approved", "valid")
_REVISION = ("needs_revision",)
_REJECTED = ("rejected",)


def profile_evidence_metrics(docs: list[Document]) -> dict[str, int]:
    """Source PDF workflow counts vs child SET/SEF semester validation (never double-count)."""
    tev = workspace_teaching_evaluation_stats(docs)
    pdf_pending = sum(1 for d in docs if is_awaiting_review(d))
    pdf_total = len(docs)
    return {
        "sourcePdfTotal": pdf_total,
        "sourcePdfPendingWorkflow": pdf_pending,
        "documentTotal": pdf_total,
        "documentPending": pdf_pending,
        "evaluationRecordsTotal": tev["evaluationRecordsTotal"],
        "evaluationRecordsPending": tev["evaluationRecordsPending"],
        "evaluationRecordsValidated": tev["evaluationRecordsValidated"],
        "evaluationRecordsNeedsRevision": tev["evaluationRecordsNeedsRevision"],
        "evaluationRecordsRejected": tev["evaluationRecordsRejected"],
        "evaluationRecordsIncomplete": tev["evaluationRecordsIncomplete"],
        "semesterEvaluationsPending": tev["evaluationRecordsPending"]
        + tev["evaluationRecordsIncomplete"]
        + tev["evaluationRecordsNeedsRevision"],
    }


def _doc_stats_subquery():
    return (
        db.session.query(
            Document.faculty_profile_id.label("profile_id"),
            func.count(Document.id).label("doc_total"),
            func.sum(case((Document.status.in_(_PENDING), 1), else_=0)).label("doc_pending"),
            func.sum(case((Document.status.in_(_APPROVED), 1), else_=0)).label("doc_approved"),
            func.sum(case((Document.status.in_(_REVISION), 1), else_=0)).label("doc_revision"),
            func.sum(case((Document.status.in_(_REJECTED), 1), else_=0)).label("doc_rejected"),
            func.max(Document.submitted_at).label("last_activity"),
            func.max(Document.created_at).label("last_upload"),
        )
        .filter(Document.deleted_at.is_(None))
        .group_by(Document.faculty_profile_id)
        .subquery()
    )


def workspace_stats(*, reviewer_user_id: int | None = None) -> dict:
    doc_q = Document.query.filter(Document.deleted_at.is_(None))
    faculty_q = (
        FacultyProfile.query.join(User, FacultyProfile.user_id == User.id)
        .filter(User.role == "faculty", User.is_active.is_(True))
    )
    if reviewer_user_id is not None:
        faculty_q = faculty_q.filter(FacultyProfile.reviewer_user_id == reviewer_user_id)
        assigned_ids = [row.id for row in faculty_q.with_entities(FacultyProfile.id).all()]
        if not assigned_ids:
            base = {
                "facultyWithDocuments": 0,
                "totalDocuments": 0,
                "pendingReview": 0,
                "approvedEvidence": 0,
                "needsRevision": 0,
                "rejected": 0,
                "documentStatusBreakdown": stats_from_documents([]),
            }
            base.update(workspace_teaching_evaluation_stats([]))
            if reviewer_user_id is not None:
                base["assignedFaculty"] = 0
            else:
                base["totalFaculty"] = faculty_q.count()
            return base
        doc_q = doc_q.filter(Document.faculty_profile_id.in_(assigned_ids))

    docs = doc_q.all()
    if docs:
        from documents.set_sef_parent_review_sync import sync_set_sef_parent_reviews

        sync_set_sef_parent_reviews(docs, None, trigger="workspace_stats")
    faculty_with_docs = len({d.faculty_profile_id for d in docs})
    pending = sum(1 for d in docs if is_awaiting_review(d))
    approved = sum(1 for d in docs if d.status in _APPROVED)
    revision = sum(1 for d in docs if d.status in _REVISION)
    rejected = sum(1 for d in docs if d.status in _REJECTED)

    tev_stats = workspace_teaching_evaluation_stats(docs)

    status_breakdown = stats_from_documents(docs)
    base = {
        "facultyWithDocuments": faculty_with_docs,
        "totalDocuments": len(docs),
        "pendingReview": pending,
        "approvedEvidence": approved,
        "needsRevision": revision,
        "rejected": rejected,
        "documentStatusBreakdown": status_breakdown,
        **tev_stats,
    }
    if reviewer_user_id is None:
        total_faculty = faculty_q.count()
        return {"totalFaculty": total_faculty, **base}
    return {"assignedFaculty": faculty_q.count(), **base}


def paginated_faculty_directory(
    *,
    page: int,
    page_size: int,
    query: str = "",
    department: str = "",
    reviewer_user_id: int | None = None,
    reviewer_filter_user_id: int | None = None,
    sort: str = "name",
    has_pending: bool | None = None,
    employee_no: str = "",
) -> dict:
    page = max(1, page)
    page_size = min(100, max(1, page_size))
    stats = _doc_stats_subquery()

    base = (
        FacultyProfile.query.join(User, FacultyProfile.user_id == User.id)
        .outerjoin(stats, stats.c.profile_id == FacultyProfile.id)
        .filter(User.role == "faculty", User.is_active.is_(True))
    )
    if reviewer_user_id is not None:
        base = base.filter(FacultyProfile.reviewer_user_id == reviewer_user_id)
    if reviewer_filter_user_id is not None:
        base = base.filter(FacultyProfile.reviewer_user_id == reviewer_filter_user_id)
    if department:
        base = base.filter(FacultyProfile.department.ilike(f"%{department}%"))
    if query:
        like = f"%{query.strip()}%"
        base = base.filter(
            or_(
                User.full_name.ilike(like),
                User.email.ilike(like),
                FacultyProfile.employee_no.ilike(like),
            )
        )
    if employee_no:
        base = base.filter(FacultyProfile.employee_no.ilike(f"%{employee_no.strip()}%"))
    if has_pending is True:
        base = base.filter(func.coalesce(stats.c.doc_pending, 0) > 0)
    elif has_pending is False:
        base = base.filter(func.coalesce(stats.c.doc_pending, 0) == 0)

    total = base.count()

    if sort == "pending":
        base = base.order_by(desc(func.coalesce(stats.c.doc_pending, 0)), User.full_name.asc())
    elif sort == "activity":
        base = base.order_by(desc(func.coalesce(stats.c.last_activity, stats.c.last_upload)), User.full_name.asc())
    elif sort == "documents":
        base = base.order_by(desc(func.coalesce(stats.c.doc_total, 0)), User.full_name.asc())
    else:
        base = base.order_by(User.full_name.asc())

    rows = base.offset((page - 1) * page_size).limit(page_size).all()

    profile_ids = [p.id for p in rows]
    docs_by_profile: dict[int, list[Document]] = {pid: [] for pid in profile_ids}
    if profile_ids:
        for doc in (
            Document.query.filter(
                Document.faculty_profile_id.in_(profile_ids),
                Document.deleted_at.is_(None),
            ).all()
        ):
            docs_by_profile.setdefault(doc.faculty_profile_id, []).append(doc)

    page_docs: list[Document] = []
    for doc_list in docs_by_profile.values():
        page_docs.extend(doc_list)
    if page_docs:
        from documents.criterion_c_evidence.workflow_sync import heal_criterion_c_workflow_for_documents
        from documents.set_sef_parent_review_sync import sync_set_sef_parent_reviews

        if heal_criterion_c_workflow_for_documents(page_docs):
            db.session.commit()
        sync_set_sef_parent_reviews(page_docs, None, trigger="faculty_directory")

    def row_dict(profile: FacultyProfile) -> dict:
        user = profile.user
        reviewer = profile.reviewer
        stat_row = (
            db.session.query(stats)
            .filter(stats.c.profile_id == profile.id)
            .first()
        )
        profile_docs = docs_by_profile.get(profile.id) or []
        metrics = profile_evidence_metrics(profile_docs)
        last_at = None
        if stat_row:
            last_at = stat_row.last_activity or stat_row.last_upload
        return {
            "id": profile.public_id,
            "name": user.full_name,
            "email": user.email,
            "employeeNo": profile.employee_no,
            "department": profile.department,
            "college": profile.college,
            "reviewerId": reviewer.public_id if reviewer else None,
            "reviewerName": reviewer.full_name if reviewer else None,
            "documentTotal": metrics["documentTotal"],
            "documentPending": metrics["sourcePdfPendingWorkflow"],
            "documentApproved": int(stat_row.doc_approved or 0) if stat_row else 0,
            "documentRevision": int(stat_row.doc_revision or 0) if stat_row else 0,
            "lastActivity": last_at.isoformat() if last_at else None,
            **metrics,
        }

    return {
        "faculty": [row_dict(p) for p in rows],
        "pagination": {
            "page": page,
            "pageSize": page_size,
            "total": total,
            "totalPages": max(1, (total + page_size - 1) // page_size),
        },
    }
