"""Prevent duplicate income claims with identical certified amounts (same evaluation context)."""

from __future__ import annotations

from typing import Any


def assess_income_duplicate_flags(
    bundle: dict[str, Any],
    *,
    indicator_id: str,
    peer_bundles: list[tuple[str, dict[str, Any]]],
    self_public_id: str,
) -> list[str]:
    if "income" not in (indicator_id or ""):
        return list(bundle.get("duplicateFlags") or [])
    flags = list(bundle.get("duplicateFlags") or [])
    try:
        amount = float(bundle.get("grossIncomeAmount"))
    except (TypeError, ValueError):
        return flags
    if amount <= 0:
        return flags
    for pub_id, peer in peer_bundles:
        if pub_id == self_public_id:
            continue
        if (peer.get("indicatorId") or "").strip() != indicator_id:
            continue
        try:
            peer_amt = float(peer.get("grossIncomeAmount"))
        except (TypeError, ValueError):
            continue
        if abs(peer_amt - amount) < 0.01:
            if "duplicate_income_amount" not in flags:
                flags.append("duplicate_income_amount")
            break
    return flags
