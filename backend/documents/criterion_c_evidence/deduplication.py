"""Duplicate service detection for Criterion C accomplishments."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from kra_configuration.criterion_c_annex import ROLE_ADVISER, ROLE_PANEL


def _norm(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def accomplishment_dedup_key(bundle: dict[str, Any], *, faculty_profile_id: int) -> str:
    """Stable key for the same service instance (not merely same title/year)."""
    parts = [
        str(faculty_profile_id),
        _norm(bundle.get("projectTitle")),
        _norm(bundle.get("studentNames")),
        _norm(bundle.get("studentGroupLabel")),
        _norm(bundle.get("role")),
        _norm(bundle.get("researchType")),
        _norm(bundle.get("completionDate")),
        _norm(bundle.get("academicYear")),
    ]
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def research_overlap_key(bundle: dict[str, Any], *, faculty_profile_id: int) -> str:
    """Key for adviser/panel overlap on the same thesis (ignores role)."""
    parts = [
        str(faculty_profile_id),
        _norm(bundle.get("projectTitle")),
        _norm(bundle.get("studentNames")),
        _norm(bundle.get("completionDate")),
    ]
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def assess_peer_duplicates(
    bundle: dict[str, Any],
    *,
    faculty_profile_id: int,
    peer_bundles: list[tuple[str, dict[str, Any]]],
    self_public_id: str,
) -> tuple[list[str], list[str]]:
    """
    Returns (duplicate_flags, policy_flags) to store on bundle.
    duplicate_flags: duplicate_service_suspected
    policy_flags: adviser_panel_same_thesis_review
    """
    duplicate_flags: list[str] = []
    policy_flags: list[str] = []
    if not bundle:
        return duplicate_flags, policy_flags

    key = accomplishment_dedup_key(bundle, faculty_profile_id=faculty_profile_id)
    overlap = research_overlap_key(bundle, faculty_profile_id=faculty_profile_id)
    role = _norm(bundle.get("role"))

    for pub_id, peer in peer_bundles:
        if pub_id == self_public_id:
            continue
        if accomplishment_dedup_key(peer, faculty_profile_id=faculty_profile_id) == key:
            duplicate_flags.append("duplicate_service_suspected")
            break

    if role in (ROLE_ADVISER, ROLE_PANEL):
        for pub_id, peer in peer_bundles:
            if pub_id == self_public_id:
                continue
            peer_role = _norm(peer.get("role"))
            if peer_role not in (ROLE_ADVISER, ROLE_PANEL):
                continue
            if peer_role == role:
                continue
            if research_overlap_key(peer, faculty_profile_id=faculty_profile_id) == overlap:
                if _norm(peer.get("projectTitle")) and _norm(bundle.get("projectTitle")):
                    policy_flags.append("adviser_panel_same_thesis_review")
                    break

    return duplicate_flags, policy_flags
