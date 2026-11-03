"""Peer duplicate detection for KRA II accomplishments."""

from __future__ import annotations

from typing import Any


def _norm(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def _bundle_signature(bundle: dict[str, Any]) -> str:
    title = _norm(str(bundle.get("outputTitle") or ""))
    venue = _norm(str(bundle.get("outputVenue") or bundle.get("journalTitle") or ""))
    reg = _norm(str(bundle.get("registrationNumber") or ""))
    ind = (bundle.get("indicatorId") or "").strip()
    if reg:
        return f"{ind}|reg:{reg}"
    return f"{ind}|{title}|{venue}"


def assess_peer_duplicates(
    bundle: dict[str, Any],
    *,
    peer_bundles: list[tuple[str, dict[str, Any]]],
    self_public_id: str,
) -> list[str]:
    flags: list[str] = []
    sig = _bundle_signature(bundle)
    if not sig or sig.endswith("||"):
        return flags
    for pub_id, peer in peer_bundles:
        if pub_id == self_public_id:
            continue
        if _bundle_signature(peer) == sig:
            flags.append("duplicate_output_suspected")
            break
    return flags
