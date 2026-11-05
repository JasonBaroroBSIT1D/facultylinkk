"""Document status breakdown aligns with workspace totals."""

from __future__ import annotations

from documents.directory import workspace_stats
from documents.serializers import stats_from_documents


def test_stats_from_documents_partitions_total(app):
    with app.app_context():
        from models import Document

        docs = Document.query.filter(Document.deleted_at.is_(None)).limit(200).all()
        if not docs:
            return
        breakdown = stats_from_documents(docs)
        accounted = (
            breakdown["pendingReview"]
            + breakdown["approved"]
            + breakdown["needsRevision"]
            + breakdown["rejected"]
            + breakdown.get("draft", 0)
        )
        assert breakdown["total"] == len(docs)
        assert accounted <= breakdown["total"]


def test_workspace_stats_includes_breakdown(app):
    with app.app_context():
        stats = workspace_stats()
        assert "documentStatusBreakdown" in stats
        bd = stats["documentStatusBreakdown"]
        assert bd["total"] == stats["totalDocuments"]
