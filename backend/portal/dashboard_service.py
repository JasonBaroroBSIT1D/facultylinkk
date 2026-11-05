"""Dashboard and reports payloads for Admin / Reviewer web portals."""

from __future__ import annotations

from sqlalchemy import desc, func

from documents.directory import paginated_faculty_directory, workspace_stats
from documents.serializers import document_to_web
from documents.service import list_admin_documents, list_reviewer_documents
from documents.status_map import is_awaiting_review
from extensions import db
from faculty.rank_simulation_engine import compute_rank_simulation
from evaluation_periods import service as eval_periods
from models import AuditLog, Document, FacultyProfile, KraScore, Notification, User


def _kra_averages(*, verified: bool = False) -> list[dict]:
    keys = ("kra1", "kra2", "kra3", "kra4")
    labels = {
        "kra1": "Instruction",
        "kra2": "Research",
        "kra3": "Extension",
        "kra4": "Professional Development",
    }
    out: list[dict] = []
    for key in keys:
        col = KraScore.verified_points if verified else KraScore.estimated_points
        row = (
            db.session.query(func.avg(col), func.max(KraScore.target_points))
            .filter(KraScore.kra_key == key)
            .first()
        )
        avg = float(row[0]) if row and row[0] is not None else None
        cap = float(row[1]) if row and row[1] is not None else 100.0
        out.append(
            {
                "kraId": key,
                "label": labels[key],
                "averagePoints": round(avg, 2) if avg is not None else None,
                "maxPoints": cap,
                "metric": "verified_average" if verified else "estimated_average",
            }
        )
    return out


def _serialize_queue_doc(doc: Document, *, api_role: str) -> dict:
    base = "admin" if api_role == "admin" else "reviewer"
    return document_to_web(doc, api_base=f"/api/{base}/documents/{doc.public_id}")


def _attention_admin(stats: dict) -> list[dict]:
    items: list[dict] = []
    pending = int(stats.get("pendingReview") or 0)
    if pending > 0:
        items.append(
            {
                "id": "pending_review",
                "title": f"{pending} document{'s' if pending != 1 else ''} waiting for review",
                "detail": "Open the evidence workspace to validate submitted files.",
                "href": "documents.html?filter=pending-review",
            }
        )
    unassigned = (
        FacultyProfile.query.join(User, FacultyProfile.user_id == User.id)
        .filter(User.role == "faculty", User.is_active.is_(True), FacultyProfile.reviewer_user_id.is_(None))
        .count()
    )
    if unassigned > 0:
        items.append(
            {
                "id": "unassigned_faculty",
                "title": f"{unassigned} faculty member{'s' if unassigned != 1 else ''} without a reviewer",
                "detail": "Assign reviewers so documents can be validated.",
                "href": "faculty.html",
            }
        )
    revision = int(stats.get("needsRevision") or 0)
    if revision > 0:
        items.append(
            {
                "id": "needs_revision",
                "title": f"{revision} document{'s' if revision != 1 else ''} need changes",
                "detail": "Faculty may need to upload corrected evidence.",
                "href": "documents.html?filter=revision",
            }
        )
    return items[:8]


def admin_dashboard_payload() -> dict:
    stats = workspace_stats()
    directory = paginated_faculty_directory(page=1, page_size=12, sort="pending")
    for row in directory.get("faculty") or []:
        profile = FacultyProfile.query.filter_by(public_id=row.get("id")).first()
        row["rank"] = profile.current_rank if profile else ""
        row["preparationStatus"] = "Has pending items" if (row.get("documentPending") or 0) > 0 else "In progress"
    kra_est = _kra_averages(verified=False)
    kra_ver = _kra_averages(verified=True)

    recent_docs = (
        Document.query.filter(Document.deleted_at.is_(None))
        .order_by(desc(Document.submitted_at), desc(Document.created_at))
        .limit(8)
        .all()
    )

    return {
        "summary": {
            "totalFaculty": int(stats.get("totalFaculty") or 0),
            "submittedDocuments": int(stats.get("totalDocuments") or 0),
            "waitingForReview": int(stats.get("pendingReview") or 0),
            "approvedDocuments": int(stats.get("approvedEvidence") or 0),
            "needsRevision": int(stats.get("needsRevision") or 0),
            "metricDefinitions": {
                "submittedDocuments": "Uploaded source PDF files (not SET/SEF semester rows).",
                "waitingForReview": "Files awaiting reviewer decision (pending or needs revision).",
                "approvedDocuments": "Reviewer-approved or valid workflow status.",
            },
        },
        "kraOverview": {"estimated": kra_est, "verified": kra_ver},
        "facultyProgress": directory.get("faculty") or [],
        "facultyProgressPagination": directory.get("pagination") or {},
        "attentionRequired": _attention_admin(stats),
        "recentDocuments": [
            {
                "id": d.public_id,
                "title": d.title,
                "facultyId": d.faculty_profile.public_id if d.faculty_profile else None,
                "facultyName": d.faculty_profile.user.full_name if d.faculty_profile and d.faculty_profile.user else "",
                "status": d.status,
                "submittedAt": d.submitted_at.isoformat() if d.submitted_at else None,
            }
            for d in recent_docs
        ],
        "dataSource": "postgresql",
    }


def reviewer_dashboard_payload(reviewer: User) -> dict:
    stats = workspace_stats(reviewer_user_id=reviewer.id)
    docs = list_reviewer_documents(reviewer)
    queue = [d for d in docs if is_awaiting_review(d)]
    revision = [d for d in docs if d.status == "needs_revision"]
    recent_reviewed = sorted(
        [d for d in docs if d.reviewed_at],
        key=lambda d: d.reviewed_at or d.created_at,
        reverse=True,
    )[:6]

    periods = eval_periods.list_published_periods_api()

    return {
        "summary": {
            "assignedFaculty": int(stats.get("assignedFaculty") or 0),
            "submittedDocuments": int(stats.get("totalDocuments") or 0),
            "waitingForReview": int(stats.get("pendingReview") or 0),
            "revisionsRequested": int(stats.get("needsRevision") or len(revision)),
            "metricDefinitions": {
                "submittedDocuments": "Files uploaded by faculty assigned to you.",
                "waitingForReview": "Assigned files that still need your review.",
            },
        },
        "evaluationPeriods": periods,
        "reviewQueue": [_serialize_queue_doc(d, api_role="reviewer") for d in queue[:15]],
        "recentReviewActivity": [
            {
                "documentId": d.public_id,
                "title": d.title,
                "facultyId": d.faculty_profile.public_id if d.faculty_profile else None,
                "facultyName": d.faculty_profile.user.full_name if d.faculty_profile and d.faculty_profile.user else "",
                "status": d.status,
                "reviewedAt": d.reviewed_at.isoformat() if d.reviewed_at else None,
                "feedback": (d.reviewer_remarks or "")[:240],
            }
            for d in recent_reviewed
        ],
        "dataSource": "postgresql",
    }


def admin_reports_payload(
    *,
    college: str = "",
    faculty_public_id: str = "",
    kra_id: str = "",
    status: str = "",
    page: int = 1,
    page_size: int = 50,
) -> dict:
    page = max(1, page)
    page_size = min(100, max(1, page_size))
    stats = workspace_stats()

    q = (
        FacultyProfile.query.join(User, FacultyProfile.user_id == User.id)
        .filter(User.role == "faculty", User.is_active.is_(True))
    )
    if college:
        q = q.filter(FacultyProfile.college.ilike(f"%{college.strip()}%"))
    if faculty_public_id:
        q = q.filter(FacultyProfile.public_id == faculty_public_id.strip())

    total = q.count()
    profiles = q.order_by(User.full_name.asc()).offset((page - 1) * page_size).limit(page_size).all()

    status_counts: dict[str, int] = {}
    for row in (
        db.session.query(Document.status, func.count(Document.id))
        .filter(Document.deleted_at.is_(None))
        .group_by(Document.status)
        .all()
    ):
        status_counts[str(row[0])] = int(row[1])

    colleges = [
        c[0]
        for c in db.session.query(FacultyProfile.college)
        .filter(FacultyProfile.college.isnot(None), FacultyProfile.college != "")
        .distinct()
        .order_by(FacultyProfile.college.asc())
        .all()
        if c[0]
    ]

    readiness_rows: list[dict] = []
    for profile in profiles:
        sim = compute_rank_simulation(profile)
        kra_scores = sim.get("kraScores") or []
        by_id = {b.get("kraId"): b for b in kra_scores if isinstance(b, dict)}
        readiness_rows.append(
            {
                "id": profile.public_id,
                "name": profile.user.full_name if profile.user else "",
                "college": profile.college or "",
                "rank": profile.current_rank,
                "kra1": (by_id.get("kra1") or {}).get("estimatedWeightedContribution")
                or (by_id.get("kra1") or {}).get("estimatedPoints"),
                "kra2": (by_id.get("kra2") or {}).get("estimatedWeightedContribution")
                or (by_id.get("kra2") or {}).get("estimatedPoints"),
                "kra3": (by_id.get("kra3") or {}).get("estimatedWeightedContribution")
                or (by_id.get("kra3") or {}).get("estimatedPoints"),
                "kra4": (by_id.get("kra4") or {}).get("estimatedWeightedContribution")
                or (by_id.get("kra4") or {}).get("estimatedPoints"),
                "weightedScore": sim.get("weightedEstimatedScore"),
                "preparationReadiness": sim.get("preparationReadinessPercentage"),
                "status": sim.get("eligibilityLabel") or "Under assessment",
                "scoreLabel": "Estimated weighted total (simulation)",
            }
        )

    return {
        "summary": {
            "totalFaculty": int(stats.get("totalFaculty") or 0),
            "totalSubmissions": int(stats.get("totalDocuments") or 0),
            "approvedDocuments": int(stats.get("approvedEvidence") or 0),
            "needsAttention": int(stats.get("pendingReview") or 0) + int(stats.get("needsRevision") or 0),
        },
        "documentStatusCounts": status_counts,
        "colleges": colleges,
        "facultyReadiness": readiness_rows,
        "pagination": {
            "page": page,
            "pageSize": page_size,
            "total": total,
            "totalPages": max(1, (total + page_size - 1) // page_size),
        },
        "filtersApplied": {
            "college": college or None,
            "facultyId": faculty_public_id or None,
            "kraId": kra_id or None,
            "status": status or None,
        },
    }


def audit_log_payload(
    *,
    query: str = "",
    role: str = "",
    page: int = 1,
    page_size: int = 40,
) -> dict:
    page = max(1, page)
    page_size = min(100, max(1, page_size))
    q = AuditLog.query.outerjoin(User, AuditLog.actor_user_id == User.id).order_by(
        desc(AuditLog.created_at)
    )
    if role:
        q = q.filter(User.role == role.strip().lower())
    if query:
        like = f"%{query.strip()}%"
        q = q.filter(
            db.or_(
                AuditLog.action.ilike(like),
                AuditLog.target_id.ilike(like),
                AuditLog.detail.ilike(like),
                User.full_name.ilike(like),
            )
        )
    total = q.count()
    rows = q.offset((page - 1) * page_size).limit(page_size).all()

    def serialize(log: AuditLog) -> dict:
        actor = log.actor
        role_key = actor.role if actor else "system"
        role_label = {
            "administrator": "Administrator",
            "reviewer": "Reviewer",
            "faculty": "Faculty",
        }.get(role_key, role_key.title() if role_key else "System")
        return {
            "id": log.public_id,
            "at": log.created_at.isoformat() if log.created_at else None,
            "user": actor.full_name if actor else "System",
            "role": role_label,
            "action": log.action,
            "ref": log.target_id or "",
            "description": log.detail or "",
        }

    return {
        "entries": [serialize(r) for r in rows],
        "pagination": {
            "page": page,
            "pageSize": page_size,
            "total": total,
            "totalPages": max(1, (total + page_size - 1) // page_size),
        },
    }


def notifications_payload(user: User) -> dict:
    rows = (
        Notification.query.filter_by(user_id=user.id)
        .order_by(desc(Notification.created_at))
        .limit(200)
        .all()
    )

    def row(n: Notification) -> dict:
        return {
            "id": n.public_id,
            "title": n.title,
            "body": n.body,
            "at": n.created_at.isoformat() if n.created_at else None,
            "read": bool(n.read),
            "kind": n.kind or "",
            "ref": n.related_document_id or n.related_faculty_id or "",
            "documentId": n.related_document_id,
            "facultyId": n.related_faculty_id,
            "audience": user.role,
            "userId": user.public_id,
        }

    items = [row(n) for n in rows]
    unread = sum(1 for i in items if not i["read"])
    return {"notifications": items, "unreadCount": unread}
