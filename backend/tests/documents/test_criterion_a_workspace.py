"""Criterion A workspace helpers (no database)."""

from __future__ import annotations

from types import SimpleNamespace

from documents.criterion_a_workspace import (
    aggregate_child_validation,
    composition_display_label,
    completeness_status_label,
    ocr_status_label,
    validation_progress_label,
)


def _doc(**kwargs):
    defaults = {
        "extracted_info": {},
        "ocr_status": "completed",
        "teaching_evaluations": [],
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_composition_display_needs_classification():
    doc = _doc(extracted_info={"Document classification status": "needs_classification"})
    assert composition_display_label(doc) == "Needs Classification"


def test_composition_display_mixed():
    doc = _doc(extracted_info={"Document evaluation composition": "Mixed SET and SEF"})
    assert composition_display_label(doc) == "Mixed SET and SEF"


def test_validation_progress_label_dynamic():
    assert validation_progress_label({"total": 12, "validated": 5}) == "5 of 12 evaluations validated"
    assert validation_progress_label({"total": 0, "validated": 0}) is None


def test_aggregate_child_validation_sums_sources():
    sources = [
        {"childValidationSummary": {"total": 4, "validated": 2, "pending": 2}},
        {"childValidationSummary": {"total": 2, "validated": 1, "pending": 1}},
    ]
    agg = aggregate_child_validation(sources)
    assert agg["total"] == 6
    assert agg["validated"] == 3
    assert agg["pending"] == 3
    assert validation_progress_label(agg) == "3 of 6 evaluations validated"


def test_ocr_status_labels():
    assert ocr_status_label(_doc(ocr_status="pending")) == "Pending"
    assert ocr_status_label(_doc(ocr_status="failed")) == "Failed"


def test_completeness_incomplete_when_no_children():
    doc = _doc(ocr_status="completed", extracted_info={"SET/SEF extraction status": "partial"})
    assert completeness_status_label(doc) == "Incomplete"
