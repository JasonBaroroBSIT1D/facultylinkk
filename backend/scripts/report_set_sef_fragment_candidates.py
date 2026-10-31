"""Read-only report: suspected duplicate or fragmented SET/SEF child rows (no writes)."""

from __future__ import annotations

import json
import sys
from collections import defaultdict

from factory import create_app
from config import Config
from models import Document, DocumentTeachingEvaluation


def main() -> int:
    app = create_app(Config)
    with app.app_context():
        rows = (
            DocumentTeachingEvaluation.query.join(Document)
            .filter(Document.deleted_at.is_(None))
            .all()
        )
        by_doc: dict[str, list[DocumentTeachingEvaluation]] = defaultdict(list)
        for row in rows:
            doc = row.document
            if not doc:
                continue
            by_doc[doc.public_id].append(row)

        report = []
        for doc_id, evals in sorted(by_doc.items()):
            incomplete = [
                r
                for r in evals
                if not (r.academic_year and r.semester and r.rating_raw)
            ]
            if len(incomplete) < 2 and len(evals) < 3:
                continue
            report.append(
                {
                    "documentId": doc_id,
                    "fileName": evals[0].document.file_name if evals[0].document else "",
                    "childCount": len(evals),
                    "incompleteRows": [
                        {
                            "id": r.public_id,
                            "type": r.evaluation_type,
                            "academicYear": r.academic_year,
                            "semester": r.semester,
                            "ratingRaw": r.rating_raw,
                            "sourceSectionRef": r.source_section_ref,
                            "reviewStatus": r.reviewer_validation_status,
                        }
                        for r in incomplete
                    ],
                }
            )
        print(json.dumps({"candidateDocuments": report, "count": len(report)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
