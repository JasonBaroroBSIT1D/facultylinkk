"""Read-only applicable scoring configuration API payloads (Phase C5 / C6–C7)."""

from __future__ import annotations

from datetime import date
from typing import Any

from kra_configuration.resolver import (
    resolve_scoring_configuration,
    resolution_metadata,
    settings_blob_from_resolution,
)
from kra_configuration.service import configuration_to_api, kra_settings_from_json


def applicable_scoring_configuration_payload(
    *,
    as_of: date | None = None,
    kra_configuration_id: int | None = None,
) -> dict[str, Any]:
    resolution = resolve_scoring_configuration(as_of=as_of, kra_configuration_id=kra_configuration_id)
    meta = resolution_metadata(resolution)
    if not resolution.row:
        return {
            "configuration": None,
            "kraSettings": kra_settings_from_json({}),
            "metadata": meta,
            "message": "No applicable official scoring configuration.",
            "rankWeightsPolicy": _rank_weights_policy(resolution),
        }
    api_row = configuration_to_api(resolution.row)
    return {
        "configuration": {
            "id": api_row["id"],
            "status": api_row["status"],
            "guidelineLabel": api_row["guidelineLabel"],
            "publishedAt": api_row["publishedAt"],
            "metadata": api_row["metadata"],
        },
        "kraSettings": settings_blob_from_resolution(resolution),
        "metadata": meta,
        "rankWeightsPolicy": _rank_weights_policy(resolution),
    }


def _rank_weights_policy(resolution) -> dict[str, Any]:
    blob = settings_blob_from_resolution(resolution)
    rw = blob.get("rankWeights")
    column_rw = {}
    if resolution.row and isinstance(resolution.row.rank_weights, dict):
        column_rw = resolution.row.rank_weights
    has_published = bool(rw) or bool(column_rw)
    return {
        "source": "published_admin_configuration" if has_published else "table_22_defaults_in_engine",
        "publishedRankWeightsPresent": has_published,
        "note": (
            "When published rank weights are empty, rank simulation uses DBM–CHED Joint Circular "
            "Table 2.2 defaults defined in the backend engine (not generated arbitrarily)."
        ),
    }
