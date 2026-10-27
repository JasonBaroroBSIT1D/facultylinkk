"""Administrator directory listings (PostgreSQL)."""

from __future__ import annotations

from auth.permissions import ROLE_FACULTY, ROLE_REVIEWER
from models import Document, FacultyProfile, User

_PENDING_DOC_STATUSES = ("pending_review", "needs_revision", "reviewer_required")


def faculty_row(profile: FacultyProfile) -> dict:
    user = profile.user
    reviewer = profile.reviewer
    row = profile.to_web_faculty()
    row["userId"] = user.public_id
    row["isActive"] = user.is_active
    row["mustChangePassword"] = user.must_change_password
    row["reviewerId"] = reviewer.public_id if reviewer else None
    row["reviewerName"] = reviewer.full_name if reviewer else None
    row["accountStatus"] = "Inactive" if not user.is_active else (profile.employment_status or "Active")
    return row


def list_faculty_rows() -> list[dict]:
    profiles = (
        FacultyProfile.query.join(User, FacultyProfile.user_id == User.id)
        .filter(User.role == ROLE_FACULTY)
        .order_by(User.full_name.asc())
        .all()
    )
    return [faculty_row(profile) for profile in profiles]


def reviewer_row(user: User) -> dict:
    faculty_count = FacultyProfile.query.filter_by(reviewer_user_id=user.id).count()
    doc_query = Document.query.filter(
        Document.reviewer_user_id == user.id,
        Document.deleted_at.is_(None),
    )
    document_count = doc_query.count()
    open_count = doc_query.filter(Document.status.in_(_PENDING_DOC_STATUSES)).count()

    if document_count == 0 and faculty_count == 0:
        review_status = "No assignments"
    elif open_count > 0:
        review_status = f"{open_count} open for review"
    elif document_count > 0:
        review_status = "No open items"
    else:
        review_status = "Not available"

    return {
        "id": user.public_id,
        "name": user.full_name,
        "email": user.email,
        "office": user.office or "",
        "department": user.office or "",
        "role": ROLE_REVIEWER,
        "isActive": user.is_active,
        "mustChangePassword": user.must_change_password,
        "assignedFacultyCount": faculty_count,
        "assignedDocumentCount": document_count,
        "openDocumentCount": open_count,
        "reviewStatus": review_status,
    }


def list_reviewer_rows() -> list[dict]:
    reviewers = User.query.filter_by(role=ROLE_REVIEWER).order_by(User.full_name.asc()).all()
    return [reviewer_row(reviewer) for reviewer in reviewers]
