"""Plain-language validation messages for faculty and reviewers."""

from __future__ import annotations

FIELD_MESSAGES = {
    "outputTitle": "Please enter the title of your accomplishment.",
    "authorsLine": "Please enter the author or inventor names.",
    "outputVenue": "Please enter the journal, publisher, venue, or registry name.",
    "journalTitle": "Please enter the journal, publisher, venue, or registry name.",
    "publicationDate": "Please enter the publication or registration date.",
    "registrationNumber": "Please enter the registration or patent number.",
    "registrationDate": "Please enter the registration date.",
    "citationContext": "Please describe what cited your work.",
    "declaredContributionPercent": "Please enter your contribution percentage (1–100).",
    "metadata_not_confirmed": "Confirm accomplishment metadata (title, authors, venue, date) before approving.",
    "metadata_not_confirmed_faculty": "Check your details below, then send for review.",
    "not_submitted": "Submit for review when you are ready.",
}


def message_for_field(field_id: str) -> str:
    return FIELD_MESSAGES.get(field_id, "Please complete this required field.")


def message_for_blocker(text: str) -> str:
    return FIELD_MESSAGES.get(text.strip(), text)
