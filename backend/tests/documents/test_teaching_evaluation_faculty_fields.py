"""Teaching evaluation faculty display (unit tests, no database)."""

from __future__ import annotations

from types import SimpleNamespace

from documents.faculty_name_display import teaching_evaluation_faculty_fields


def _doc(**kwargs):
    base = {
        "extracted_info": {},
        "faculty_profile": None,
    }
    base.update(kwargs)
    return SimpleNamespace(**base)


def _profile(name: str):
    return SimpleNamespace(user=SimpleNamespace(full_name=name), public_id="fac_x")


def _tev(faculty_name: str | None):
    return SimpleNamespace(
        extracted_metadata={"facultyName": faculty_name} if faculty_name else {}
    )


def test_faculty_from_tev_metadata():
    doc = _doc()
    profile = _profile("Jason Baroro")
    fields = teaching_evaluation_faculty_fields(doc, profile, tev=_tev("Jason Baroro"))
    assert fields["facultyName"] == "Jason Baroro"
    assert fields["facultyNameSource"] == "document"
    assert fields["needsVerification"] is False


def test_faculty_not_detected_without_profile_substitution():
    doc = _doc(extracted_info={"Faculty name extraction status": "not_detected"})
    profile = _profile("Ana Reyes")
    fields = teaching_evaluation_faculty_fields(doc, profile, tev=_tev(None))
    assert fields["facultyName"] == "Not detected"
    assert fields["uploadedBy"] == "Ana Reyes"
    assert fields["nameVerificationLabel"] == "Name Not Detected"


def test_faculty_needs_verification_from_record_metadata():
    doc = _doc()
    profile = _profile("Maria Santos")
    fields = teaching_evaluation_faculty_fields(doc, profile, tev=_tev("Diego Ramos"))
    assert fields["facultyName"] == "Diego Ramos"
    assert fields["nameVerificationLabel"] == "Name Mismatch"
    assert fields["needsVerification"] is True
    assert fields["documentNameOnFile"] == "Diego Ramos"
