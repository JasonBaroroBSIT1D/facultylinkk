"""Invention patent stage deduplication (JC Section 23.1.f — highest stage only)."""

from __future__ import annotations

from typing import Any

from kra_configuration.kra2_indicator_registry import patent_stage_key

_STAGE_RANK = {"a": 1, "p": 2, "g": 3}


def _norm(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def invention_patent_group_key(bundle: dict[str, Any], *, indicator_id: str) -> str | None:
    """Group acceptance/publication/grant rows for the same underlying invention."""
    if not (indicator_id or "").startswith("kra2-b-patent-"):
        return None
    reg = _norm(str(bundle.get("registrationNumber") or ""))
    if reg:
        return f"patent|reg:{reg}"
    title = _norm(str(bundle.get("outputTitle") or ""))
    if not title:
        return None
    return f"patent|title:{title}"


def patent_stage_rank(indicator_id: str) -> int:
    stage = patent_stage_key(indicator_id)
    if not stage:
        return 0
    return _STAGE_RANK.get(stage.lower(), 0)


def apply_patent_highest_stage_only(
    points_by_accomplishment: dict[str, float],
    *,
    bundle_by_key: dict[str, dict[str, Any]],
    indicator_by_key: dict[str, str],
) -> dict[str, float]:
    """
    For each invention patent group, keep only the accomplishment key with the highest stage rank.
    Lower stages are zeroed (not summed) per official highest-stage rule.
    """
    if not points_by_accomplishment:
        return points_by_accomplishment

    groups: dict[str, list[str]] = {}
    for key in points_by_accomplishment:
        ind = indicator_by_key.get(key, "")
        bundle = bundle_by_key.get(key) or {}
        gkey = invention_patent_group_key(bundle, indicator_id=ind)
        if not gkey:
            continue
        groups.setdefault(gkey, []).append(key)

    adjusted = dict(points_by_accomplishment)
    for _gkey, keys in groups.items():
        if len(keys) < 2:
            continue
        best_key = max(keys, key=lambda k: patent_stage_rank(indicator_by_key.get(k, "")))
        best_rank = patent_stage_rank(indicator_by_key.get(best_key, ""))
        for k in keys:
            if k == best_key:
                continue
            if patent_stage_rank(indicator_by_key.get(k, "")) < best_rank:
                adjusted[k] = 0.0
    return adjusted


def assess_patent_stage_overlaps(
    bundle: dict[str, Any],
    *,
    indicator_id: str,
    peer_bundles: list[tuple[str, dict[str, Any], str]],
    self_public_id: str,
) -> list[str]:
    """Reviewer-facing flags when multiple stages exist for the same invention."""
    flags: list[str] = []
    gkey = invention_patent_group_key(bundle, indicator_id=indicator_id)
    if not gkey:
        return flags
    my_rank = patent_stage_rank(indicator_id)
    for pub_id, peer, peer_ind in peer_bundles:
        if pub_id == self_public_id:
            continue
        if invention_patent_group_key(peer, indicator_id=peer_ind) != gkey:
            continue
        peer_rank = patent_stage_rank(peer_ind)
        if peer_rank > my_rank:
            flags.append("patent_lower_stage_superseded")
        elif peer_rank < my_rank:
            flags.append("patent_higher_stage_exists_peer")
        elif peer_rank == my_rank and peer_ind != indicator_id:
            flags.append("patent_duplicate_stage_suspected")
    return flags
