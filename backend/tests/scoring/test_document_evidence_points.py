from documents.scoring.document_evidence_points import effective_document_points


class _Doc:
    def __init__(self, **kwargs):
        self.deleted_at = kwargs.get("deleted_at")
        self.status = kwargs.get("status", "pending_review")
        self.extracted_info = kwargs.get("extracted_info") or {}
        self.indicator_id = kwargs.get("indicator_id", "kra2-a-1")
        self.verified_points = kwargs.get("verified_points")
        self.reviewer_score = kwargs.get("reviewer_score")
        self.estimated_points = kwargs.get("estimated_points")
        self.ocr_status = kwargs.get("ocr_status", "completed")


def test_rejected_document_excluded():
    doc = _Doc(status="rejected", extracted_info={"Simulation eligible": "yes", "Provisional score": "10"})
    assert effective_document_points(doc) is None


def test_pending_simulation_eligible_counts():
    doc = _Doc(
        status="pending_review",
        extracted_info={"Simulation eligible": "yes", "Provisional score": "12.5"},
    )
    assert effective_document_points(doc) == 12.5


def test_approved_uses_verified_points():
    doc = _Doc(status="approved", verified_points=15.0)
    assert effective_document_points(doc) == 15.0
