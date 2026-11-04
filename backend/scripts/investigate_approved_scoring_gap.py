"""List approved KRA III accomplishments where system eligible != approved points."""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from documents.kra3_evidence.bundle import bundle_from_document
from documents.kra3_evidence.scoring import estimated_points_for_bundle
from kra_configuration.version_lock import resolve_settings_for_faculty_simulation
from models import Document


def main() -> None:
    app = create_app()
    with app.app_context():
        settings, _ = resolve_settings_for_faculty_simulation()
        rows = []
        q = Document.query.filter(Document.criterion_id.like("kra3-%"), Document.deleted_at.is_(None))
        for doc in q.limit(500):
            bundle = bundle_from_document(doc)
            if not isinstance(bundle, dict):
                continue
            if (bundle.get("reviewStatus") or "").lower() != "approved":
                continue
            ra = bundle.get("reviewerAssessment") or {}
            approved = ra.get("approvedPoints")
            if approved is None:
                approved = ra.get("assessedPoints")
            try:
                system = estimated_points_for_bundle(
                    bundle,
                    indicator_id=doc.indicator_id,
                    settings=settings,
                    applicable_config_present=True,
                )
            except Exception:
                system = None
            if approved is None or system is None:
                continue
            if abs(float(approved) - float(system)) > 0.001:
                rows.append(
                    {
                        "publicId": doc.public_id,
                        "indicatorId": doc.indicator_id,
                        "title": doc.title,
                        "deliveryHours": bundle.get("deliveryHours"),
                        "approvedPoints": approved,
                        "systemCalculatedNow": system,
                        "storedSystemInRa": ra.get("systemCalculatedPoints"),
                        "scoringVersion": ra.get("scoringConfigurationVersion"),
                        "assessedAt": ra.get("assessedAt"),
                        "adjustmentReason": ra.get("scoreAdjustmentReason"),
                    }
                )
        print(json.dumps({"mismatchCount": len(rows), "rows": rows}, indent=2))


if __name__ == "__main__":
    main()
