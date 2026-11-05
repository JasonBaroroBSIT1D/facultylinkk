"""KRA IV metadata fields and user-facing labels."""

from __future__ import annotations

from kra_configuration.kra4_indicator_registry import workflow_family

FIELD_ACTIVITY_TITLE = "activityTitle"
FIELD_ORGANIZATION = "organizationName"
FIELD_FACULTY_ROLE = "facultyRole"
FIELD_ACTIVITY_DATE = "activityDate"
FIELD_SERVICE_START = "serviceStartDate"
FIELD_SERVICE_END = "serviceEndDate"
FIELD_INSTITUTION = "institutionName"
FIELD_DEGREE_TITLE = "degreeTitle"
FIELD_EVENT_TITLE = "eventTitle"
FIELD_EVENT_DURATION_HOURS = "eventDurationHours"
FIELD_SCOPE = "eventScope"
FIELD_PAPER_TITLE = "paperTitle"
FIELD_AWARD_TITLE = "awardTitle"
FIELD_AWARD_LEVEL = "awardLevel"
FIELD_EMPLOYER = "employerName"
FIELD_POSITION_TITLE = "positionTitle"
FIELD_EXPERIENCE_YEARS = "experienceYears"
FIELD_APPROVAL_REFERENCE = "approvalReference"

_FIELD_LABELS: dict[str, str] = {
    FIELD_ACTIVITY_TITLE: "Membership or certificate title",
    FIELD_ORGANIZATION: "Professional organization name",
    FIELD_FACULTY_ROLE: "Active participation / role",
    FIELD_ACTIVITY_DATE: "Date completed or awarded",
    FIELD_SERVICE_START: "Start date",
    FIELD_SERVICE_END: "End date",
    FIELD_INSTITUTION: "School or institution",
    FIELD_DEGREE_TITLE: "Degree or qualification",
    FIELD_EVENT_TITLE: "Event or training title",
    FIELD_EVENT_DURATION_HOURS: "Total duration (hours)",
    FIELD_SCOPE: "Local or international",
    FIELD_PAPER_TITLE: "Paper title",
    FIELD_AWARD_TITLE: "Award name",
    FIELD_AWARD_LEVEL: "Award level",
    FIELD_EMPLOYER: "Employer or organization",
    FIELD_POSITION_TITLE: "Position or designation",
    FIELD_EXPERIENCE_YEARS: "Qualifying years of experience",
    FIELD_APPROVAL_REFERENCE: "Approval reference (if required)",
}

_FAMILY_FIELDS: dict[str, tuple[str, ...]] = {
    "organization": (
        FIELD_ACTIVITY_TITLE,
        FIELD_ORGANIZATION,
        FIELD_FACULTY_ROLE,
        FIELD_SERVICE_START,
        FIELD_SERVICE_END,
    ),
    "education": (
        FIELD_DEGREE_TITLE,
        FIELD_INSTITUTION,
        FIELD_ACTIVITY_DATE,
    ),
    "capacity_building": (
        FIELD_EVENT_TITLE,
        FIELD_ORGANIZATION,
        FIELD_EVENT_DURATION_HOURS,
        FIELD_SCOPE,
        FIELD_ACTIVITY_DATE,
        FIELD_APPROVAL_REFERENCE,
    ),
    "paper_presentation": (
        FIELD_PAPER_TITLE,
        FIELD_EVENT_TITLE,
        FIELD_ORGANIZATION,
        FIELD_SCOPE,
        FIELD_ACTIVITY_DATE,
        FIELD_APPROVAL_REFERENCE,
    ),
    "award": (
        FIELD_AWARD_TITLE,
        FIELD_AWARD_LEVEL,
        FIELD_ORGANIZATION,
        FIELD_ACTIVITY_DATE,
    ),
    "prior_experience": (
        FIELD_EMPLOYER,
        FIELD_POSITION_TITLE,
        FIELD_SERVICE_START,
        FIELD_SERVICE_END,
        FIELD_EXPERIENCE_YEARS,
    ),
    "generic": (FIELD_ACTIVITY_TITLE, FIELD_ORGANIZATION, FIELD_ACTIVITY_DATE),
}


def metadata_field_ids(indicator_id: str) -> tuple[str, ...]:
    fam = workflow_family(indicator_id)
    return _FAMILY_FIELDS.get(fam, _FAMILY_FIELDS["generic"])


def metadata_field_label(field_id: str) -> str:
    return _FIELD_LABELS.get(field_id, field_id.replace("_", " ").title())
