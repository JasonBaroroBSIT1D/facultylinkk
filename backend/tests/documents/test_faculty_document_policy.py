from documents.faculty_document_policy import (
    faculty_can_delete,
    faculty_can_replace,
    faculty_can_request_withdrawal,
)


class _Doc:
    def __init__(self, **kwargs):
        self.deleted_at = kwargs.get("deleted_at")
        self.status = kwargs.get("status", "pending_review")
        self.ocr_status = kwargs.get("ocr_status", "pending")
        self.verified_points = kwargs.get("verified_points")


def test_delete_pending_review():
    assert faculty_can_delete(_Doc(status="pending_review", ocr_status="pending"))


def test_delete_failed_ocr():
    assert faculty_can_delete(_Doc(status="pending_review", ocr_status="failed"))


def test_delete_needs_revision():
    assert faculty_can_delete(_Doc(status="needs_revision"))


def test_no_delete_approved():
    assert not faculty_can_delete(_Doc(status="approved", ocr_status="completed"))


def test_replace_needs_revision():
    assert faculty_can_replace(_Doc(status="needs_revision"))


def test_withdrawal_approved_with_points():
    assert faculty_can_request_withdrawal(_Doc(status="approved", verified_points=10.0))
