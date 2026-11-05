"""Sample metadata payloads for KRA IV live QA (one per official indicator)."""

from __future__ import annotations

from typing import Any

from kra_configuration.kra4_indicator_registry import all_indicators, metadata_field_ids, workflow_family


def qa_metadata_for(indicator_id: str, *, run_id: str) -> dict[str, Any]:
    fam = workflow_family(indicator_id)
    base: dict[str, Any] = {}
    if fam == "organization":
        base = {
            "activityTitle": "QA Professional Organization Membership",
            "organizationName": "QA Professional Society",
            "facultyRole": "Active member",
            "serviceStartDate": "2024-01-01",
            "serviceEndDate": "2026-01-01",
        }
    elif fam == "education":
        base = {
            "degreeTitle": "QA Post-Master Diploma",
            "institutionName": "QA State University",
            "activityDate": "2025-06-15",
        }
    elif fam == "capacity_building":
        scope = "international" if indicator_id.endswith("-intl") else "local"
        base = {
            "eventTitle": "QA Capacity Building Workshop",
            "organizationName": "QA Training Council",
            "eventDurationHours": 8 if scope == "international" else 6,
            "eventScope": scope,
            "activityDate": "2025-09-01",
            "approvalReference": f"GB-APPROVAL-{run_id[-6:]}",
        }
    elif fam == "paper_presentation":
        scope = "international" if indicator_id.endswith("-intl") else "local"
        base = {
            "paperTitle": "QA Research Paper on Professional Development",
            "eventTitle": "QA National Conference",
            "organizationName": "QA Conference Host",
            "eventScope": scope,
            "activityDate": "2025-10-10",
            "approvalReference": f"PRES-APPROVAL-{run_id[-6:]}",
        }
    elif fam == "award":
        level = "Institutional"
        if "local" in indicator_id:
            level = "Local"
        elif "national" in indicator_id:
            level = "National"
        base = {
            "awardTitle": "QA Excellence Award",
            "awardLevel": level,
            "organizationName": "QA Awarding Body",
            "activityDate": "2025-11-01",
        }
    elif fam == "prior_experience":
        base = {
            "employerName": "QA Prior Employer",
            "positionTitle": "QA Prior Role",
            "serviceStartDate": "2018-01-01",
            "serviceEndDate": "2020-01-01",
            "experienceYears": 2,
        }
    else:
        base = {
            "activityTitle": "QA Accomplishment",
            "organizationName": "QA Org",
            "activityDate": "2025-01-01",
        }
    allowed = set(metadata_field_ids(indicator_id))
    return {k: v for k, v in base.items() if k in allowed}


def all_qa_indicators() -> list[tuple[str, str, dict[str, Any]]]:
    rows: list[tuple[str, str, dict[str, Any]]] = []
    for row in all_indicators():
        iid = (row.get("id") or "").strip()
        cid = (row.get("criterionId") or "").strip()
        if not iid or not cid:
            continue
        rows.append((iid, cid, dict(row)))
    return rows
