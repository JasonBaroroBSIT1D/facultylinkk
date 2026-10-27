"""Administrator faculty/reviewer management (PostgreSQL)."""

from __future__ import annotations

from auth.admin_directory import faculty_row, reviewer_row
from auth.permissions import ROLE_FACULTY, ROLE_REVIEWER
from extensions import db
from models import Document, FacultyProfile, KraScore, User

_PENDING_DOC_STATUSES = ("pending_review", "needs_revision", "reviewer_required")
_COMPLETED_DOC_STATUSES = ("approved", "rejected", "valid")


def _faculty_profile(public_id: str) -> FacultyProfile | None:
    return FacultyProfile.query.filter_by(public_id=public_id).first()


def _reviewer_user(public_id: str) -> User | None:
    return User.query.filter_by(public_id=public_id, role=ROLE_REVIEWER).first()


def _user_by_public_id(public_id: str) -> User | None:
    return User.query.filter_by(public_id=public_id).first()


def faculty_detail(public_id: str) -> dict:
    profile = _faculty_profile(public_id)
    if not profile or not profile.user or profile.user.role != ROLE_FACULTY:
        raise ValueError("not_found")

    user = profile.user
    docs = Document.query.filter_by(faculty_profile_id=profile.id).filter(Document.deleted_at.is_(None)).all()
    kra_rows = KraScore.query.filter_by(faculty_profile_id=profile.id).all()

    pending = [d for d in docs if d.status in _PENDING_DOC_STATUSES]
    completed = [d for d in docs if d.status in _COMPLETED_DOC_STATUSES]

    detail = faculty_row(profile)
    detail["createdAt"] = user.created_at.isoformat() if user.created_at else None
    detail["passwordSetupStatus"] = (
        "Must change temporary password" if user.must_change_password else "Password updated"
    )
    detail["documentSummary"] = {
        "total": len(docs),
        "pendingReview": len(pending),
        "completed": len(completed),
    }
    if kra_rows:
        detail["kraScores"] = [
            {
                "kraKey": row.kra_key,
                "estimatedPoints": row.estimated_points,
                "verifiedPoints": row.verified_points,
                "statusLabel": row.status_label or "",
            }
            for row in kra_rows
        ]
    else:
        detail["kraScores"] = []

    detail["documents"] = [
        {
            "id": doc.public_id,
            "title": doc.title,
            "status": doc.status,
            "submittedAt": doc.submitted_at.isoformat() if doc.submitted_at else None,
        }
        for doc in docs[:50]
    ]
    if len(docs) > 50:
        detail["documentsNote"] = f"Showing 50 of {len(docs)} documents."
    return detail


def set_faculty_reviewer(faculty_public_id: str, reviewer_public_id: str | None) -> dict:
    profile = _faculty_profile(faculty_public_id)
    if not profile or not profile.user or profile.user.role != ROLE_FACULTY:
        raise ValueError("not_found")

    if not profile.user.is_active:
        raise ValueError("inactive_faculty")

    previous_reviewer_id = profile.reviewer_user_id
    reviewer_user_id = None
    if reviewer_public_id:
        reviewer = _reviewer_user(reviewer_public_id)
        if not reviewer or not reviewer.is_active:
            raise ValueError("invalid_reviewer")
        reviewer_user_id = reviewer.id

    if profile.reviewer_user_id == reviewer_user_id:
        return {
            "faculty": faculty_row(profile),
            "previousReviewerId": None,
            "pendingDocumentsUnchanged": 0,
        }

    profile.reviewer_user_id = reviewer_user_id
    db.session.commit()

    pending_on_profile = Document.query.filter(
        Document.faculty_profile_id == profile.id,
        Document.deleted_at.is_(None),
        Document.status.in_(_PENDING_DOC_STATUSES),
    ).count()

    return {
        "faculty": faculty_row(profile),
        "previousReviewerId": previous_reviewer_id,
        "pendingDocumentsUnchanged": pending_on_profile,
        "note": (
            "Existing pending document reviews keep their original reviewer assignment. "
            "Only the faculty profile assignment was updated."
            if pending_on_profile
            else None
        ),
    }


def sync_reviewer_faculty_assignments(
    reviewer_public_id: str,
    faculty_public_ids: list[str],
    *,
    confirm_reassign: bool = False,
) -> dict:
    reviewer = _reviewer_user(reviewer_public_id)
    if not reviewer or not reviewer.is_active:
        raise ValueError("invalid_reviewer")

    desired = {fid.strip() for fid in faculty_public_ids if fid and fid.strip()}
    reassignment_conflicts: list[dict] = []

    for fac_id in desired:
        profile = _faculty_profile(fac_id)
        if not profile or not profile.user.is_active:
            raise ValueError("invalid_faculty")
        if profile.reviewer_user_id and profile.reviewer_user_id != reviewer.id:
            other = User.query.get(profile.reviewer_user_id)
            reassignment_conflicts.append(
                {
                    "facultyId": profile.public_id,
                    "facultyName": profile.user.full_name,
                    "currentReviewerId": other.public_id if other else None,
                    "currentReviewerName": other.full_name if other else None,
                }
            )

    if reassignment_conflicts and not confirm_reassign:
        raise ValueError("reassign_confirmation_required")

    currently_assigned = FacultyProfile.query.filter_by(reviewer_user_id=reviewer.id).all()
    for profile in currently_assigned:
        if profile.public_id not in desired:
            profile.reviewer_user_id = None

    for fac_id in desired:
        profile = _faculty_profile(fac_id)
        if profile:
            profile.reviewer_user_id = reviewer.id

    db.session.commit()
    return {
        "reviewer": reviewer_row(reviewer),
        "assignedFacultyIds": list(desired),
        "reassigned": len(reassignment_conflicts),
    }


def reviewer_work_detail(reviewer_public_id: str) -> dict:
    reviewer = _reviewer_user(reviewer_public_id)
    if not reviewer:
        raise ValueError("not_found")

    assigned_profiles = (
        FacultyProfile.query.filter_by(reviewer_user_id=reviewer.id)
        .join(User, FacultyProfile.user_id == User.id)
        .order_by(User.full_name.asc())
        .all()
    )
    faculty_items = [
        {
            "id": p.public_id,
            "name": p.user.full_name,
            "email": p.user.email,
            "department": p.department,
            "rank": p.current_rank,
        }
        for p in assigned_profiles
    ]

    profile_ids = [p.id for p in assigned_profiles]
    documents: list[Document] = []
    if profile_ids:
        documents = (
            Document.query.filter(
                Document.faculty_profile_id.in_(profile_ids),
                Document.deleted_at.is_(None),
            )
            .order_by(Document.submitted_at.desc())
            .limit(100)
            .all()
        )

    pending = [d for d in documents if d.status in _PENDING_DOC_STATUSES]
    completed = [d for d in documents if d.status in _COMPLETED_DOC_STATUSES]

    def doc_row(doc: Document) -> dict:
        fac = doc.faculty_profile
        return {
            "id": doc.public_id,
            "title": doc.title,
            "status": doc.status,
            "facultyId": fac.public_id if fac else None,
            "facultyName": fac.user.full_name if fac and fac.user else None,
            "submittedAt": doc.submitted_at.isoformat() if doc.submitted_at else None,
            "reviewerId": doc.reviewer.public_id if doc.reviewer else None,
        }

    return {
        "reviewer": reviewer_row(reviewer),
        "faculty": faculty_items,
        "documents": {
            "available": bool(documents),
            "totalListed": len(documents),
            "pending": [doc_row(d) for d in pending],
            "completed": [doc_row(d) for d in completed],
            "note": (
                None
                if documents
                else "No documents are recorded in PostgreSQL for assigned faculty."
            ),
        },
    }


def deactivate_user(public_id: str) -> dict:
    user = _user_by_public_id(public_id)
    if not user:
        raise ValueError("not_found")

    if user.role == ROLE_REVIEWER:
        faculty_count = FacultyProfile.query.filter_by(reviewer_user_id=user.id).count()
        pending_docs = Document.query.filter(
            Document.reviewer_user_id == user.id,
            Document.deleted_at.is_(None),
            Document.status.in_(_PENDING_DOC_STATUSES),
        ).count()
        if faculty_count or pending_docs:
            raise ValueError("reviewer_has_assignments")

    if not user.is_active:
        return {"userId": user.public_id, "isActive": False, "alreadyInactive": True}

    user.is_active = False
    user.auth_epoch += 1
    if user.role == ROLE_FACULTY and user.faculty_profile:
        user.faculty_profile.employment_status = "Inactive"
    db.session.commit()
    return {"userId": user.public_id, "isActive": False, "alreadyInactive": False}


def reactivate_user(public_id: str) -> dict:
    user = _user_by_public_id(public_id)
    if not user:
        raise ValueError("not_found")

    if user.is_active:
        return {"userId": user.public_id, "isActive": True, "alreadyActive": True}

    user.is_active = True
    if user.role == ROLE_FACULTY and user.faculty_profile:
        user.faculty_profile.employment_status = "Active"
    db.session.commit()
    return {"userId": user.public_id, "isActive": True, "alreadyActive": False}
