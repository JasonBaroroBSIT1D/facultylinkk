"""Role-aware sync diagnostics (PostgreSQL identity + aggregate counts, no secrets)."""

from __future__ import annotations

from auth import assignment_queries as aq
from documents.directory import workspace_stats
from evaluation_periods import service as eval_periods
from extensions import db
from models import Document, User


def database_identity() -> dict:
    """Sanitized PostgreSQL target for cross-client alignment checks."""
    raw = (db.engine.url.database or "").strip() or "unknown"
    host = (db.engine.url.host or "localhost").strip()
    port = db.engine.url.port
    host_label = f"{host}:{port}" if port else host

    lowered = raw.lower()
    if lowered in {"facultylink", "facultylink_prod", "facultylink_production"}:
        category = "production"
    elif "qa" in lowered:
        category = "qa"
    elif "test" in lowered:
        category = "test"
    else:
        category = "other"

    return {
        "databaseName": raw,
        "databaseCategory": category,
        "databaseHost": host_label,
    }


def _user_slice(user: User) -> dict:
    profile = user.faculty_profile if user.role == "faculty" else None
    reviewer_id = None
    if profile and profile.reviewer_user_id:
        rev = User.query.get(profile.reviewer_user_id)
        reviewer_id = rev.public_id if rev else None
    return {
        "publicId": user.public_id,
        "role": user.role,
        "email": user.email,
        "fullName": user.full_name,
        "facultyProfileId": profile.public_id if profile else None,
        "assignedReviewerId": reviewer_id,
    }


def admin_sync_health_payload(user: User) -> dict:
    stats = workspace_stats()
    published = eval_periods.list_published_periods_api()
    return {
        **database_identity(),
        "actor": _user_slice(user),
        "workspaceStats": stats,
        "publishedEvaluationPeriods": len(published),
        "metricDefinitions": {
            "totalFaculty": "Active users with role faculty.",
            "totalDocuments": "Non-deleted source PDF workflow documents.",
        },
        "dataSource": "postgresql",
    }


def reviewer_sync_health_payload(user: User) -> dict:
    stats = workspace_stats(reviewer_user_id=user.id)
    published = eval_periods.list_published_periods_api()
    assigned = aq.list_assigned_faculty_for_reviewer(user)
    return {
        **database_identity(),
        "actor": _user_slice(user),
        "workspaceStats": stats,
        "assignedFacultyCount": len(assigned),
        "publishedEvaluationPeriods": len(published),
        "dataSource": "postgresql",
    }


def faculty_sync_health_payload(user: User) -> dict:
    profile = user.faculty_profile
    if not profile:
        return {**database_identity(), "actor": _user_slice(user), "message": "no_faculty_profile"}
    docs = (
        Document.query.filter_by(faculty_profile_id=profile.id)
        .filter(Document.deleted_at.is_(None))
        .count()
    )
    prep = eval_periods.faculty_preparation_period_api()
    reviewer = None
    if profile.reviewer_user_id:
        rev = User.query.get(profile.reviewer_user_id)
        if rev:
            reviewer = {"publicId": rev.public_id, "fullName": rev.full_name}
    return {
        **database_identity(),
        "actor": _user_slice(user),
        "documentCount": docs,
        "preparationPeriodPublished": prep is not None,
        "assignedReviewer": reviewer,
        "dataSource": "postgresql",
    }
