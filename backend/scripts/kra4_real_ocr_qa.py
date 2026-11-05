"""Run one real OCR job on facultylink_qa without injecting ocr_text."""

from __future__ import annotations

import io
import json
import os
import sys

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


def main() -> int:
    if os.environ.get("FACULTYLINK_KRA4_QA_RUN", "").strip() != "1":
        print("Set FACULTYLINK_KRA4_QA_RUN=1", file=sys.stderr)
        return 2
    from scripts.qa_db_guard import require_qa_test_database, qa_faculty_user

    require_qa_test_database()
    tess_cmd = (os.environ.get("TESSERACT_CMD") or "").strip()
    if not tess_cmd:
        for candidate in (
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ):
            if os.path.isfile(candidate):
                os.environ["TESSERACT_CMD"] = candidate
                break
    from documents.ocr.config import refresh_tesseract_availability

    ocr = refresh_tesseract_availability()
    if not ocr.available:
        payload = {
            "status": "BLOCKED",
            "reason": "tesseract_unavailable",
            "message": ocr.message,
            "hint": "Install Tesseract and/or set TESSERACT_CMD (see backend/docs/OCR.md)",
        }
        out = os.path.join(BACKEND, "..", "docs", "KRA4_REAL_OCR_QA.json")
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        print(json.dumps(payload, indent=2))
        return 3

    from config import Config
    from factory import create_app
    from documents.service import create_upload
    from documents.ocr.queue import process_pending_jobs
    from werkzeug.datastructures import FileStorage
    import pymupdf

    pdf = pymupdf.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "KRA IV OCR QA: Organization QA Professional Society", fontsize=12)
    page.insert_text((72, 96), "Degree: Master of Science at QA State University", fontsize=12)
    page.insert_text((72, 120), "Experience: 2 years", fontsize=12)
    buf = io.BytesIO()
    pdf.save(buf)
    pdf.close()

    app = create_app(Config)
    report: dict = {"status": "FAIL", "checks": {}}
    with app.app_context():
        faculty_user, _profile = qa_faculty_user()
        fs = FileStorage(stream=io.BytesIO(buf.getvalue()), filename="kra4-real-ocr-qa.pdf", content_type="application/pdf")
        doc = create_upload(
            faculty_user,
            file=fs,
            title="[KRA4-QA] real-ocr smoke",
            kra_id="kra4",
            criterion_id="kra4-a",
            indicator_id="kra4-a-member",
        )
        from extensions import db

        db.session.commit()
        db.session.refresh(doc)
        report["documentId"] = doc.public_id
        report["checks"]["upload_ok"] = bool(doc.public_id)

        processed_count = 0
        for _ in range(3):
            processed_count += process_pending_jobs(limit=5)
            db.session.refresh(doc)
            if (doc.ocr_status or "") in ("completed", "failed"):
                break
        report["checks"]["worker_processed"] = processed_count >= 1 or (doc.ocr_status or "") == "completed"
        report["ocrJobsProcessed"] = processed_count
        db.session.refresh(doc)
        report["ocrStatus"] = doc.ocr_status
        extracted = (getattr(doc, "extracted_text", None) or "").strip()
        report["extractedTextLength"] = len(extracted)
        report["checks"]["extracted_text_present"] = bool(extracted)

        from documents.kra4_evidence.ocr_extraction import ensure_kra4_ocr_extraction

        extraction = ensure_kra4_ocr_extraction(doc)
        report["ocrExtraction"] = extraction
        report["checks"]["kra4_hints"] = bool(
            isinstance(extraction, dict) and isinstance(extraction.get("hints"), dict) and extraction["hints"]
        )
        failed = [k for k, v in report["checks"].items() if not v]
        report["status"] = "PASS" if not failed else "FAIL"

    out = os.path.join(BACKEND, "..", "docs", "KRA4_REAL_OCR_QA.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
