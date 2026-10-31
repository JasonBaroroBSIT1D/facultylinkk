"""Read-only: parent PDF approved vs child SET/SEF still pending (no writes)."""

from __future__ import annotations

import json
import sys

from factory import create_app
from config import Config
from models import Document

from documents.set_sef_parent_context import set_sef_parent_context


def main() -> int:
    app = create_app(Config)
    with app.app_context():
        docs = Document.query.filter(
            Document.deleted_at.is_(None),
            Document.criterion_id == "kra1-a",
            Document.status.in_(("approved", "valid")),
        ).all()
        report = []
        for doc in docs:
            ctx = set_sef_parent_context(doc)
            if not ctx:
                continue
            all_c = ctx.get("allChildValidationSummary") or {}
            if all_c.get("total", 0) == 0:
                continue
            if all_c.get("pending", 0) == 0 and all_c.get("incomplete", 0) == 0:
                continue
            report.append(
                {
                    "documentId": doc.public_id,
                    "fileName": doc.file_name,
                    "documentStatus": doc.status,
                    "summaryLine": ctx.get("summaryLine"),
                    "childValidationSummary": all_c,
                    "estimatedPointsExplanation": ctx.get("estimatedPointsExplanation"),
                }
            )
        print(
            json.dumps(
                {
                    "discrepancyCount": len(report),
                    "note": "Parent approved/simulation-accepted while child evaluations still pending or incomplete.",
                    "documents": report,
                },
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
