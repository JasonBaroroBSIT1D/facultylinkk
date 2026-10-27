"""Shared PostgreSQL faculty–reviewer assignment reads."""

from __future__ import annotations

from auth.permissions import ROLE_FACULTY, ROLE_REVIEWER
from models import FacultyProfile, User


def reviewer_public_payload(user: User) -> dict:
    return {
        "id": user.public_id,
        "name": user.full_name,
        "role": ROLE_REVIEWER,
        "designation": "Institutional Reviewer",
        "office": user.office or "",
        "department": user.office or "",
        "specialization": user.specialization or "",
    }


def faculty_assigned_reviewer(faculty_user: User) -> dict:
    profile = faculty_user.faculty_profile
    if not profile:
        raise ValueError("no_profile")
    reviewer = profile.reviewer
    if not reviewer or not reviewer.is_active:
        return {"reviewer": None, "assignmentStatus": "unassigned"}
    return {
        "reviewer": reviewer_public_payload(reviewer),
        "assignmentStatus": "assigned",
    }


def list_assigned_faculty_for_reviewer(reviewer_user: User) -> list[dict]:
    profiles = (
        FacultyProfile.query.filter_by(reviewer_user_id=reviewer_user.id)
        .join(User, FacultyProfile.user_id == User.id)
        .filter(User.is_active.is_(True))
        .order_by(User.full_name.asc())
        .all()
    )
    return [
        {
            "id": profile.public_id,
            "userId": profile.user.public_id,
            "name": profile.user.full_name,
            "email": profile.user.email,
            "rank": profile.current_rank,
            "department": profile.department,
            "college": profile.college,
            "reviewerId": reviewer_user.public_id,
        }
        for profile in profiles
    ]


def current_faculty_user(public_id: str) -> User | None:
    return User.query.filter_by(public_id=public_id, role=ROLE_FACULTY, is_active=True).first()


def current_reviewer_user(public_id: str) -> User | None:
    return User.query.filter_by(public_id=public_id, role=ROLE_REVIEWER, is_active=True).first()
