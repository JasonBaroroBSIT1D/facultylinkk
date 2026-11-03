"""KRA I Criterion B instructional materials evidence bundles (JSON on Document rows)."""

from documents.criterion_b_evidence.bundle import (
    BUNDLE_EXTRACTED_KEY,
    LINK_EXTRACTED_KEY,
    bundle_from_document,
    link_from_document,
)
from documents.criterion_b_evidence.validation import validate_instructional_material_bundle

__all__ = [
    "BUNDLE_EXTRACTED_KEY",
    "LINK_EXTRACTED_KEY",
    "bundle_from_document",
    "link_from_document",
    "validate_instructional_material_bundle",
]
