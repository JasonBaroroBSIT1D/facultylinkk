"""KRA configuration row status constants."""

STATUS_DRAFT = "draft"
STATUS_PUBLISHED = "published"
STATUS_SUPERSEDED = "superseded"

SCORABLE_STATUSES = frozenset({STATUS_PUBLISHED, STATUS_SUPERSEDED})
