from __future__ import annotations

from datetime import date, datetime, timezone

from models import Document, EvaluationPeriod, FacultyProfile, KraScore, RankSimulation, User

MOBILE_KRA_KEYS = ("kra1", "kra2", "kra3", "kra4")


def _iso_date(value: date | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _iso_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def faculty_profile_payload(user: User, profile: FacultyProfile | None) -> dict:
    base = {
        "fullName": user.full_name,
        "email": user.email,
        "phone": user.contact or "",
        "specialization": user.specialization or "",
        "office": user.office or "",
        "facultyId": "",
        "employeeNo": "",
        "department": "",
        "college": "",
        "currentRank": "",
        "targetRank": "",
        "campus": "",
        "yearsInService": 0,
        "employmentStatus": "",
        "highestDegree": "",
    }
    if not profile:
        return base
    base.update(
        {
            "facultyId": profile.public_id,
            "employeeNo": profile.employee_no,
            "department": profile.department,
            "college": profile.college,
            "currentRank": profile.current_rank,
            "targetRank": profile.target_rank or "",
            "campus": profile.campus,
            "yearsInService": profile.years_of_service,
            "employmentStatus": profile.employment_status,
        }
    )
    return base


def _document_counts_by_kra(profile: FacultyProfile) -> dict[str, int]:
    counts = {key: 0 for key in MOBILE_KRA_KEYS}
    rows = (
        Document.query.filter_by(faculty_profile_id=profile.id)
        .filter(Document.deleted_at.is_(None))
        .all()
    )
    for doc in rows:
        key = (doc.kra_id or "").strip()
        if key in counts:
            counts[key] += 1
    return counts


def _kra_scores_payload(profile: FacultyProfile) -> list[dict]:
    stored = {row.kra_key: row for row in profile.kra_scores}
    doc_counts = _document_counts_by_kra(profile)
    payload: list[dict] = []
    for key in MOBILE_KRA_KEYS:
        row = stored.get(key)
        if row:
            payload.append(
                {
                    "kraId": key,
                    "currentPoints": int(round(row.verified_points or row.estimated_points or 0)),
                    "targetPoints": int(round(row.target_points or 0)),
                    "documentCount": row.document_count or doc_counts.get(key, 0),
                    "statusLabel": row.status_label or "In progress",
                    "breakdown": row.breakdown_json if isinstance(row.breakdown_json, list) else [],
                }
            )
        else:
            payload.append(
                {
                    "kraId": key,
                    "currentPoints": 0,
                    "targetPoints": 0,
                    "documentCount": doc_counts.get(key, 0),
                    "statusLabel": "Not yet calculated",
                    "breakdown": [],
                }
            )
    return payload


def _simulation_payload(profile: FacultyProfile) -> dict | None:
    sim: RankSimulation | None = profile.rank_simulation
    if not sim:
        return None
    return {
        "currentRank": sim.current_rank,
        "targetRank": sim.target_rank,
        "currentPoints": int(round(sim.verified_total_points or sim.estimated_total_points or 0)),
        "requiredPoints": int(round(sim.estimated_total_points or 0)),
        "eligibilityLabel": sim.readiness_label or "Simulation snapshot",
        "missingRequirements": sim.missing_requirements or "",
        "simulatedAt": _iso_datetime(sim.simulated_at),
    }


def _preparation_period_payload() -> dict | None:
    period = (
        EvaluationPeriod.query.filter(EvaluationPeriod.status != "draft")
        .order_by(EvaluationPeriod.start_date.desc())
        .first()
    )
    if not period:
        return None
    today = date.today()
    status = "open"
    if period.submission_close and today > period.submission_close:
        status = "closed"
    elif period.submission_close and (period.submission_close - today).days <= 14:
        status = "closing_soon"
    return {
        "cycleName": period.label,
        "startDate": _iso_date(period.start_date),
        "endDate": _iso_date(period.end_date),
        "reviewerAvailableUntil": _iso_date(period.review_close or period.end_date),
        "status": status,
        "periodType": period.period_type,
    }


def _recent_activity(profile: FacultyProfile, limit: int = 5) -> list[dict]:
    rows = (
        Document.query.filter_by(faculty_profile_id=profile.id)
        .filter(Document.deleted_at.is_(None))
        .order_by(Document.submitted_at.desc())
        .limit(limit)
        .all()
    )
    activity: list[dict] = []
    for doc in rows:
        activity.append(
            {
                "title": doc.title,
                "subtitle": doc.kra_id or "Document",
                "submittedAt": _iso_datetime(doc.submitted_at),
                "status": doc.status,
            }
        )
    return activity


def _recent_feedback(profile: FacultyProfile, limit: int = 5) -> list[dict]:
    rows = (
        Document.query.filter_by(faculty_profile_id=profile.id)
        .filter(Document.deleted_at.is_(None))
        .filter(Document.reviewer_remarks.isnot(None))
        .filter(Document.reviewer_remarks != "")
        .order_by(Document.reviewed_at.desc().nulls_last(), Document.submitted_at.desc())
        .limit(limit)
        .all()
    )
    feedback: list[dict] = []
    for doc in rows:
        feedback.append(
            {
                "documentTitle": doc.title,
                "message": doc.reviewer_remarks or "",
                "reviewedAt": _iso_datetime(doc.reviewed_at or doc.submitted_at),
            }
        )
    return feedback


def faculty_dashboard_payload(user: User, profile: FacultyProfile) -> dict:
    kra_scores = _kra_scores_payload(profile)
    total_verified = sum(item["currentPoints"] for item in kra_scores)
    docs = (
        Document.query.filter_by(faculty_profile_id=profile.id)
        .filter(Document.deleted_at.is_(None))
        .all()
    )
    validated = sum(1 for d in docs if d.status in ("approved", "valid", "validated"))
    pending = sum(1 for d in docs if d.status in ("pending_review", "pending-review", "processing"))
    action = sum(1 for d in docs if d.status in ("needs_revision", "revision", "rejected", "invalid"))
    sim = _simulation_payload(profile)

    return {
        "totalPoints": total_verified,
        "targetPoints": 100,
        "documentCompletionPercent": 0 if not docs else int(round((validated / len(docs)) * 100)),
        "validatedCount": validated,
        "pendingCount": pending,
        "actionRequiredCount": action,
        "kraScores": kra_scores,
        "simulation": sim,
        "preparationPeriod": _preparation_period_payload(),
        "recentActivity": _recent_activity(profile),
        "recentFeedback": _recent_feedback(profile),
        "profileSummary": {
            "fullName": user.full_name,
            "currentRank": profile.current_rank,
            "targetRank": profile.target_rank or "",
            "department": profile.department,
        },
    }
