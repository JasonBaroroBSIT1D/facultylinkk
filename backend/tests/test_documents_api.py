"""Document API authorization smoke tests."""

from __future__ import annotations


def test_faculty_documents_require_auth(client):
    response = client.get("/api/faculty/me/documents")
    assert response.status_code == 401


def test_reviewer_documents_require_auth(client):
    response = client.get("/api/reviewer/me/documents")
    assert response.status_code == 401


def test_admin_documents_require_auth(client):
    response = client.get("/api/admin/documents")
    assert response.status_code == 401
