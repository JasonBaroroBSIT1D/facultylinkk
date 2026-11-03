"""Faculty submit vs reviewer approval validation separation."""

from documents.kra2_evidence.bundle import build_initial_bundle, SLOT_STATUS_PRESENT_UNVERIFIED
from documents.kra2_evidence.validation import validate_kra2_bundle


def _patent_bundle_ready_fields():
    bundle = build_initial_bundle(
        primary_document_id="doc-patent",
        primary_file_hash="hash",
        indicator_id="kra2-b-patent-g-sole",
    )
    bundle["outputTitle"] = "Smart Irrigation Device"
    bundle["authorsLine"] = "Jason Baroro"
    bundle["registrationNumber"] = "FAKE-IP-2025-00003"
    bundle["registrationDate"] = "2025"
    bundle["metadataConfirmed"] = {
        "outputTitle": True,
        "authorsLine": True,
        "registrationNumber": True,
        "registrationDate": True,
    }
    bundle["checklist"]["primary_output"]["status"] = SLOT_STATUS_PRESENT_UNVERIFIED
    return bundle


def test_unverified_primary_does_not_block_faculty_submission():
    v = validate_kra2_bundle(_patent_bundle_ready_fields(), indicator_id="kra2-b-patent-g-sole")
    assert v["readyForSubmission"] is True
    assert v["submissionBlockers"] == []
    assert any("Verify supporting evidence" in b for b in v["reviewerBlockers"])
    assert any("Verify supporting evidence" in b for b in v["approvalBlockers"])


def test_missing_inventor_blocks_submission():
    bundle = _patent_bundle_ready_fields()
    bundle["authorsLine"] = ""
    bundle["metadataConfirmed"]["authorsLine"] = False
    v = validate_kra2_bundle(bundle, indicator_id="kra2-b-patent-g-sole")
    assert v["readyForSubmission"] is False
    assert any("author" in b.lower() or "inventor" in b.lower() for b in v["submissionBlockers"])
