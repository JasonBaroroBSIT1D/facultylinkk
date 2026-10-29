"""Configuration-driven document scoring (SET/SEF and related)."""

from documents.scoring.set_sef_aggregate import (
    aggregate_indicator,
    build_criterion_a_summary,
    document_period_row,
)

__all__ = [
    "aggregate_indicator",
    "build_criterion_a_summary",
    "document_period_row",
]
