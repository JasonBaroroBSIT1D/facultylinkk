"""Plain-language validation messages for KRA III faculty and reviewers."""

from __future__ import annotations

from kra_configuration.kra3_workflow import metadata_field_label

FIELD_MESSAGES = {
    "activityTitle": "Please enter the activity or project name.",
    "organizationName": "Please enter the organization or partner name.",
    "facultyRole": "Please enter your role in this activity.",
    "activityDate": "Please enter the date of the activity.",
    "serviceStartDate": "Please enter the start date.",
    "serviceEndDate": "Please enter the end date.",
    "grossIncomeAmount": "Please enter the certified gross income amount.",
    "deliveryHours": "Please enter eligible service hours.",
    "csrOverallRating": "Please enter the overall satisfaction rating (0–100).",
    "linkedExtensionProjectId": "Please link this CSR to your eligible extension project.",
    "designationTitle": "Please enter your administrative designation.",
    "approvalReference": "Please enter the approval or Special Order reference.",
    "serviceDurationMonths": "Please enter months of service (hosting needs at least 6 months).",
    "metadata_not_confirmed": "Confirm the information below before approving.",
    "metadata_not_confirmed_faculty": "Check your details below, then send for review.",
    "not_submitted": "Submit for review when you are ready.",
}


def message_for_field(field_id: str) -> str:
    if field_id in FIELD_MESSAGES:
        return FIELD_MESSAGES[field_id]
    return f"Please complete: {metadata_field_label(field_id)}."
