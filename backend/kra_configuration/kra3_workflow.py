"""KRA III metadata fields and user-facing labels (faculty Check your work)."""

from __future__ import annotations

from kra_configuration.kra3_indicator_registry import workflow_family

# Shared bundle keys (stored on kra3EvidenceBundle).
FIELD_ACTIVITY_TITLE = "activityTitle"
FIELD_ORGANIZATION = "organizationName"
FIELD_FACULTY_ROLE = "facultyRole"
FIELD_ACTIVITY_DATE = "activityDate"
FIELD_SERVICE_START = "serviceStartDate"
FIELD_SERVICE_END = "serviceEndDate"
FIELD_GROSS_INCOME = "grossIncomeAmount"
FIELD_DELIVERY_HOURS = "deliveryHours"
FIELD_CSR_RATING = "csrOverallRating"
FIELD_LINKED_PROJECT_ID = "linkedExtensionProjectId"
FIELD_DESIGNATION_TITLE = "designationTitle"
FIELD_APPROVAL_REFERENCE = "approvalReference"
FIELD_SERVICE_MONTHS = "serviceDurationMonths"

_FIELD_LABELS: dict[str, str] = {
    FIELD_ACTIVITY_TITLE: "Activity or project name",
    FIELD_ORGANIZATION: "Organization or partner",
    FIELD_FACULTY_ROLE: "Your role",
    FIELD_ACTIVITY_DATE: "Date",
    FIELD_SERVICE_START: "Start date",
    FIELD_SERVICE_END: "End date",
    FIELD_GROSS_INCOME: "Gross income amount (₱)",
    FIELD_DELIVERY_HOURS: "Eligible service hours",
    FIELD_CSR_RATING: "Overall satisfaction rating (0–100)",
    FIELD_LINKED_PROJECT_ID: "Linked extension project",
    FIELD_DESIGNATION_TITLE: "Administrative designation",
    FIELD_APPROVAL_REFERENCE: "Approval or Special Order reference",
    FIELD_SERVICE_MONTHS: "Months of service",
}

_FAMILY_FIELDS: dict[str, tuple[str, ...]] = {
    "linkage": (
        FIELD_ACTIVITY_TITLE,
        FIELD_ORGANIZATION,
        FIELD_FACULTY_ROLE,
        FIELD_ACTIVITY_DATE,
        FIELD_APPROVAL_REFERENCE,
    ),
    "income": (
        FIELD_ACTIVITY_TITLE,
        FIELD_ORGANIZATION,
        FIELD_FACULTY_ROLE,
        FIELD_GROSS_INCOME,
        FIELD_ACTIVITY_DATE,
    ),
    "accreditation": (
        FIELD_ACTIVITY_TITLE,
        FIELD_ORGANIZATION,
        FIELD_FACULTY_ROLE,
        FIELD_SERVICE_START,
        FIELD_SERVICE_END,
    ),
    "judging": (
        FIELD_ACTIVITY_TITLE,
        FIELD_ORGANIZATION,
        FIELD_FACULTY_ROLE,
        FIELD_ACTIVITY_DATE,
    ),
    "consultancy": (
        FIELD_ACTIVITY_TITLE,
        FIELD_ORGANIZATION,
        FIELD_FACULTY_ROLE,
        FIELD_SERVICE_START,
        FIELD_SERVICE_END,
    ),
    "media_column": (
        FIELD_ACTIVITY_TITLE,
        FIELD_ORGANIZATION,
        FIELD_ACTIVITY_DATE,
    ),
    "media_host": (
        FIELD_ACTIVITY_TITLE,
        FIELD_ORGANIZATION,
        FIELD_SERVICE_START,
        FIELD_SERVICE_END,
        FIELD_SERVICE_MONTHS,
    ),
    "media_guest": (
        FIELD_ACTIVITY_TITLE,
        FIELD_ORGANIZATION,
        FIELD_ACTIVITY_DATE,
    ),
    "resource_person": (
        FIELD_ACTIVITY_TITLE,
        FIELD_ORGANIZATION,
        FIELD_FACULTY_ROLE,
        FIELD_ACTIVITY_DATE,
        FIELD_DELIVERY_HOURS,
    ),
    "extension_project": (
        FIELD_ACTIVITY_TITLE,
        FIELD_ORGANIZATION,
        FIELD_FACULTY_ROLE,
        FIELD_SERVICE_START,
        FIELD_SERVICE_END,
    ),
    "csr": (
        FIELD_ACTIVITY_TITLE,
        FIELD_CSR_RATING,
        FIELD_LINKED_PROJECT_ID,
    ),
    "designation": (
        FIELD_DESIGNATION_TITLE,
        FIELD_APPROVAL_REFERENCE,
        FIELD_SERVICE_START,
        FIELD_SERVICE_END,
        FIELD_SERVICE_MONTHS,
    ),
    "generic_service": (
        FIELD_ACTIVITY_TITLE,
        FIELD_ORGANIZATION,
        FIELD_FACULTY_ROLE,
        FIELD_ACTIVITY_DATE,
    ),
}


def metadata_field_ids(indicator_id: str) -> tuple[str, ...]:
    fam = workflow_family(indicator_id)
    return _FAMILY_FIELDS.get(fam, _FAMILY_FIELDS["generic_service"])


def metadata_field_label(field_id: str) -> str:
    return _FIELD_LABELS.get(field_id, field_id.replace("_", " ").title())
