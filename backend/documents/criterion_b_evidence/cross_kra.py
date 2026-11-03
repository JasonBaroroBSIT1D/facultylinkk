"""Cross-KRA double-counting hints (§35 Item 1; program committee vs Extension Criterion D)."""

from __future__ import annotations

import re
from typing import Any

EXTENSION_ADMIN_INDICATOR_PREFIX = "kra3-d-"
COMMITTEE_ADMIN_INDICATORS = frozenset(
    {
        "kra3-d-inst-chair",
        "kra3-d-inst-member",
        "kra3-d-dept-chair",
        "kra3-d-dept-member",
    }
)

WARNING_EXTENSION_COMMITTEE_OVERLAP = "extension_criterion_d_committee_overlap"
WARNING_SHARED_EVIDENCE_HASH = "shared_evidence_hash_other_kra"
WARNING_SAME_PROGRAM_DUAL_ROLE = "same_program_lead_and_contributor_claims"


def _normalize_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def _tokens(text: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", _normalize_text(text)) if len(t) >= 4}


def assess_cross_kra_warnings(
    bundle: dict[str, Any],
    peer_documents: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """
    Reviewer-visible warnings only — never auto-reject a claim.

    ``peer_documents`` entries: ``publicId``, ``indicatorId``, ``title``,
    optional ``criterionId``, ``fileHash``, ``committeeName``, ``programName``.
    """
    if not bundle or bundle.get("claimType") != "academic_program":
        return []

    warnings: list[dict[str, Any]] = []
    peers = peer_documents or []
    program_name = bundle.get("programName") or ""
    committee = bundle.get("committeeName") or ""
    primary_id = (bundle.get("checklist") or {}).get("primary_contribution_document") or {}
    primary_hash = primary_id.get("fileHash") if isinstance(primary_id, dict) else None
    program_tokens = _tokens(program_name) | _tokens(committee)

    for peer in peers:
        if not isinstance(peer, dict):
            continue
        peer_id = peer.get("publicId") or peer.get("public_id")
        ind = (peer.get("indicatorId") or peer.get("indicator_id") or "").strip()
        crit = (peer.get("criterionId") or peer.get("criterion_id") or "").strip()

        if ind in ("kra1-b-program-lead", "kra1-b-program-contributor"):
            peer_program = peer.get("programName") or peer.get("title") or ""
            if program_name and _normalize_text(peer_program) == _normalize_text(program_name):
                if ind != bundle.get("indicatorId"):
                    warnings.append(
                        {
                            "code": WARNING_SAME_PROGRAM_DUAL_ROLE,
                            "confidence": "uncertain",
                            "message": (
                                "Another Criterion B program claim uses the same program name "
                                "under a different lead/contributor indicator. Review for "
                                "consistent role assignment."
                            ),
                            "relatedDocumentId": peer_id,
                        }
                    )

        if ind.startswith(EXTENSION_ADMIN_INDICATOR_PREFIX) and ind in COMMITTEE_ADMIN_INDICATORS:
            peer_text = " ".join(
                [
                    peer.get("title") or "",
                    peer.get("committeeName") or "",
                    peer.get("programName") or "",
                ]
            )
            overlap = program_tokens & _tokens(peer_text)
            if program_tokens and overlap:
                warnings.append(
                    {
                        "code": WARNING_EXTENSION_COMMITTEE_OVERLAP,
                        "confidence": "confirmed" if committee and committee.lower() in peer_text.lower() else "uncertain",
                        "message": (
                            "Faculty may have an Extension Criterion D administrative-designation "
                            "claim related to the same program development committee (§35 Item 1). "
                            "Confirm no double counting with this program contribution claim."
                        ),
                        "relatedDocumentId": peer_id,
                        "relatedIndicatorId": ind,
                    }
                )

        peer_hash = peer.get("fileHash") or peer.get("file_hash")
        if (
            primary_hash
            and peer_hash
            and primary_hash == peer_hash
            and crit
            and crit != "kra1-b"
        ):
            warnings.append(
                {
                    "code": WARNING_SHARED_EVIDENCE_HASH,
                    "confidence": "uncertain",
                    "message": (
                        "The primary contribution file hash matches a document filed under "
                        "another KRA/criterion. Review whether the same work is being claimed twice."
                    ),
                    "relatedDocumentId": peer_id,
                    "relatedCriterionId": crit,
                }
            )

    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str | None]] = set()
    for item in warnings:
        key = (item.get("code") or "", item.get("relatedDocumentId"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped
