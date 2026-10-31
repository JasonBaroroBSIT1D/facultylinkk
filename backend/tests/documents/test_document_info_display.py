"""Document information display (unit tests, no database writes)."""

from __future__ import annotations

from types import SimpleNamespace

from documents.document_info_display import build_document_information


def _doc(**kwargs):
    base = {
        "public_id": "doc_test",
        "kra_id": "kra1",
        "criterion_id": "kra1-a",
        "indicator_id": "kra1-a-teaching-evidence",
        "ocr_status": "completed",
        "status": "pending_review",
        "extracted_info": {},
        "faculty_profile": None,
        "submitted_at": None,
        "created_at": None,
    }
    base.update(kwargs)
    return SimpleNamespace(**base)


def _profile(name: str):
    user = SimpleNamespace(full_name=name)
    return SimpleNamespace(user=user, public_id="fac_x")


def test_faculty_name_from_document():
    doc = _doc(
        extracted_info={
            "Faculty name on document": "Maria Santos",
            "Faculty name extraction status": "detected",
            "Document type": "Mixed SET/SEF",
        }
    )
    profile = _profile("Maria Santos")
    info = build_document_information(doc, profile)
    assert info["facultyName"] == "Maria Santos"
    assert info["facultyNameSource"] == "document"
    assert info["documentType"] == "Mixed SET/SEF"
    assert info["kraLabel"] == "Instruction"
    assert info["criterionLabel"] == "Teaching Effectiveness"


def test_faculty_name_not_detected_does_not_use_profile():
    doc = _doc(extracted_info={"Faculty name extraction status": "not_detected"})
    profile = _profile("Ana Reyes")
    info = build_document_information(doc, profile)
    assert info["facultyName"] == "Not detected"
    assert info["facultyNameOnDocument"] == "Not detected"
    assert info["uploadedBy"] == "Ana Reyes"
    assert info["nameVerificationLabel"] == "Name Not Detected"


def test_faculty_name_needs_verification():
    doc = _doc(
        extracted_info={
            "Faculty name on document": "Diego Ramos",
            "Faculty name extraction status": "detected",
        }
    )
    profile = _profile("Maria Santos")
    info = build_document_information(doc, profile)
    assert info["nameVerificationLabel"] == "Name Mismatch"
    assert info["needsVerification"] is True
    assert info["documentNameOnFile"] == "Diego Ramos"
    assert info["facultyNameOnDocument"] == "Diego Ramos"
