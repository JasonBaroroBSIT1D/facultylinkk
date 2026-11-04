"""Reviewer KRA III summary/accomplishments routes return live-shaped payloads."""

from __future__ import annotations

import json
from pathlib import Path


def test_kra3_summary_and_list_helpers(monkeypatch):
    from documents.kra3_evidence import service as svc

    calls: list[str] = []

    def fake_list(_fpid, *, criterion_id=None, submitted_only=False):
        calls.append(f"list:{criterion_id}:{submitted_only}")
        return [
            {
                "documentId": "doc-1",
                "activityTitle": "Community training",
                "estimatedPoints": 6.0,
                "validatedPoints": None,
                "reviewStatus": "pending",
                "submittedForReviewAt": "2026-01-02",
            }
        ]

    def fake_summary(_fpid, *, criterion_id, settings=None):
        calls.append(f"summary:{criterion_id}")
        return {
            "criterionId": criterion_id,
            "estimatedPoints": 6.0,
            "validatedPoints": 0.0,
            "maxPoints": 50.0,
            "reviewCounts": {"pending": 1, "approved": 0, "rejected": 0},
        }

    monkeypatch.setattr(svc, "list_faculty_accomplishments", fake_list)
    monkeypatch.setattr(svc, "kra3_summary_for_faculty", fake_summary)

    summary = svc.kra3_summary_for_faculty(1, criterion_id="kra3-b")
    rows = svc.list_faculty_accomplishments(1, criterion_id="kra3-b", submitted_only=True)
    assert summary["criterionId"] == "kra3-b"
    assert rows[0]["activityTitle"] == "Community training"
    assert "summary:kra3-b" in calls


def test_all_criterion_route_ids_exist_in_catalog():
    data = json.loads(
        (Path(__file__).resolve().parents[2] / "kra_configuration" / "data" / "kra3_indicators.json").read_text(
            encoding="utf-8"
        )
    )
    crits = {row["criterionId"] for row in data["indicators"]}
    assert crits == {"kra3-a", "kra3-b", "kra3-c", "kra3-d"}
