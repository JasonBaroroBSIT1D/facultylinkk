"""Phase C7: read API payload shape (mocked resolver, no DB)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from kra_configuration.read_api import applicable_scoring_configuration_payload


@patch("kra_configuration.read_api.settings_blob_from_resolution", return_value={"criteria": {"kra1-c": {"maxPoints": 10}}})
@patch("kra_configuration.read_api.resolution_metadata", return_value={"provenance": "applicable_as_of", "version": 1})
@patch("kra_configuration.read_api.configuration_to_api")
@patch("kra_configuration.read_api.resolve_scoring_configuration")
def test_applicable_payload_when_configuration_present(mock_resolve, mock_to_api, _meta, _settings):
    row = SimpleNamespace(id=5, settings_json={"version": 1}, rank_weights={})
    mock_resolve.return_value = SimpleNamespace(row=row, provenance="applicable_as_of")
    mock_to_api.return_value = {
        "id": 5,
        "status": "published",
        "guidelineLabel": "Test",
        "publishedAt": "2024-01-01T00:00:00+00:00",
        "metadata": {"version": 1, "effectiveFrom": "2023-08-01"},
    }
    payload = applicable_scoring_configuration_payload()
    assert payload["configuration"]["id"] == 5
    assert payload["kraSettings"]["criteria"]["kra1-c"]["maxPoints"] == 10
    assert payload["metadata"]["version"] == 1
    assert "rankWeightsPolicy" in payload


@patch("kra_configuration.read_api.resolution_metadata", return_value={"provenance": "none_available"})
@patch("kra_configuration.read_api.resolve_scoring_configuration")
def test_applicable_payload_when_none(mock_resolve, _meta):
    mock_resolve.return_value = SimpleNamespace(row=None, provenance="none_available")
    payload = applicable_scoring_configuration_payload()
    assert payload["configuration"] is None
    assert "message" in payload
    assert payload["kraSettings"] == {"kras": {}, "criteria": {}, "indicators": {}, "indicatorMeta": {}}
