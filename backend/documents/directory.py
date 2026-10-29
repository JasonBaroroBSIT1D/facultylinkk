"""Paginated faculty directories for the Evidence Workspace."""

from __future__ import annotations

from sqlalchemy import and_, case, desc, func, or_

from extensions import db
from models import Document, FacultyProfile, User

from documents.status_map import is_awaiting_review

_PENDING = ("pending_review", "reviewer_required", "needs_revision")
_LEGACY_PENDING = and_(Document.status == "draft", Document.file_path.isnot(None))
_APPROVED = ("approved", "valid")
_REVISION = ("needs_revision",)
_REJECTED = ("rejected",)


def _doc_stats_subquery():
    return (
        db.session.query(
            Document.faculty_profile_id.label("profile_id"),
            func.count(Document.id).label("doc_total"),
            func.sum(
                case(
                    (or_(Document.status.in_(_PENDING), _LEGACY_PENDING), 1),
                    else_=0,
                )
            ).label("doc_pending"),
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
            return {
                "facultyWithDocuments": 0,
                "totalDocuments": 0,
                "pendingReview": 0,
                "approvedEvidence": 0,
                "needsRevision": 0,
                "rejected": 0,
            }
        doc_q = doc_q.filter(Document.faculty_profile_id.in_(assigned_ids))

    docs = doc_q.all()
    faculty_with_docs = len({d.faculty_profile_id for d in docs})
    pending = sum(1 for d in docs if is_awaiting_review(d))
    approved = sum(1 for d in docs if d.status in _APPROVED)
    revision = sum(1 for d in docs if d.status in _REVISION)
    rejected = sum(1 for d in docs if d.status in _REJECTED)

    if reviewer_user_id is None:
        total_faculty = faculty_q.count()
        return {
            "totalFaculty": total_faculty,
            "facultyWithDocuments": faculty_with_docs,
            "totalDocuments": len(docs),
            "pendingReview": pending,
            "approvedEvidence": approved,
            "needsRevision": revision,
            "rejected": rejected,
        }
    return {
        "assignedFaculty": faculty_q.count(),
        "facultyWithDocuments": faculty_with_docs,
        "totalDocuments": len(docs),
        "pendingReview": pending,
        "approvedEvidence": approved,
        "needsRevision": revision,
        "rejected": rejected,
    }


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

    tuples = (
        base.with_entities(
            FacultyProfile,
            func.coalesce(stats.c.doc_total, 0),
            func.coalesce(stats.c.doc_pending, 0),
            func.coalesce(stats.c.doc_approved, 0),
            func.coalesce(stats.c.doc_revision, 0),
            stats.c.last_activity,
            stats.c.last_upload,
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    def row_dict(entry) -> dict:
        profile, doc_total, doc_pending, doc_approved, doc_revision, last_activity, last_upload = entry
        user = profile.user
        reviewer = profile.reviewer
        last_at = last_activity or last_upload
        return {
            "id": profile.public_id,
            "name": user.full_name,
            "email": user.email,
            "employeeNo": profile.employee_no,
            "department": profile.department,
            "college": profile.college,
            "reviewerId": reviewer.public_id if reviewer else None,
            "reviewerName": reviewer.full_name if reviewer else None,
            "documentTotal": int(doc_total or 0),
            "documentPending": int(doc_pending or 0),
            "documentApproved": int(doc_approved or 0),
            "documentRevision": int(doc_revision or 0),
            "lastActivity": last_at.isoformat() if last_at else None,
        }

    return {
        "faculty": [row_dict(t) for t in tuples],
        "pagination": {
            "page": page,
            "pageSize": page_size,
            "total": total,
            "totalPages": max(1, (total + page_size - 1) // page_size),
        },
    }
