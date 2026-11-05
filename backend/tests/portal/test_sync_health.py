"""Sync health (read-only against configured PostgreSQL)."""

from __future__ import annotations


def test_health_includes_database_identity(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body.get("database") == "connected"
    identity = body.get("databaseIdentity") or {}
    assert identity.get("databaseName")
    assert identity.get("databaseCategory") in {"production", "qa", "test", "other"}


def test_reviewer_dashboard_payload_shape(app):
    with app.app_context():
        from portal.dashboard_service import reviewer_dashboard_payload
        from models import User

        reviewer = User.query.filter_by(role="reviewer", is_active=True).first()
        if not reviewer:
            return
        payload = reviewer_dashboard_payload(reviewer)
        assert payload.get("dataSource") == "postgresql"
        assert "evaluationPeriods" in payload
        assert isinstance(payload["evaluationPeriods"], list)
