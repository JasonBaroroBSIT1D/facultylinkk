"""Criterion A (Annex A) evidence checklist slots — JC 01 s. 2026 Sections 16–21."""

from __future__ import annotations

from typing import Any, Final

from kra_configuration.kra2_annex import CRITERION_A_ID

SLOT_PRIMARY_OUTPUT: Final[str] = "primary_output"
SLOT_PEER_REVIEW: Final[str] = "peer_review_evidence"
SLOT_INDEXING_CERT: Final[str] = "indexing_certification"
SLOT_CONTRIBUTION_CERT: Final[str] = "contribution_certificate"
SLOT_CITING_PUBLICATION: Final[str] = "citing_publication_evidence"
SLOT_TRANSLATION_IMPACT: Final[str] = "translation_impact_evidence"

# Annex A documentary requirements (PDF pp. 78–81).
_CRITERION_A_SLOTS: dict[str, tuple[str, ...]] = {
    "kra2-a-book-sole": (SLOT_PRIMARY_OUTPUT, SLOT_PEER_REVIEW),
    "kra2-a-book-co": (SLOT_PRIMARY_OUTPUT, SLOT_CONTRIBUTION_CERT),
    "kra2-a-chapter-sole": (SLOT_PRIMARY_OUTPUT, SLOT_PEER_REVIEW),
    "kra2-a-chapter-co": (SLOT_PRIMARY_OUTPUT, SLOT_CONTRIBUTION_CERT),
    "kra2-a-journal-sole": (SLOT_PRIMARY_OUTPUT, SLOT_INDEXING_CERT),
    "kra2-a-journal-co": (SLOT_PRIMARY_OUTPUT, SLOT_INDEXING_CERT, SLOT_CONTRIBUTION_CERT),
    "kra2-a-monograph-sole": (SLOT_PRIMARY_OUTPUT, SLOT_PEER_REVIEW),
    "kra2-a-monograph-co": (SLOT_PRIMARY_OUTPUT, SLOT_CONTRIBUTION_CERT),
    "kra2-a-translation-sole": (SLOT_PRIMARY_OUTPUT, SLOT_TRANSLATION_IMPACT),
    "kra2-a-translation-co": (SLOT_PRIMARY_OUTPUT, SLOT_TRANSLATION_IMPACT, SLOT_CONTRIBUTION_CERT),
    "kra2-a-cite": (SLOT_PRIMARY_OUTPUT, SLOT_CITING_PUBLICATION, SLOT_INDEXING_CERT),
}

_SLOT_LABELS: dict[str, str] = {
    SLOT_PRIMARY_OUTPUT: "Published output (copy showing author, date, and title)",
    SLOT_PEER_REVIEW: "Peer review and reputable academic press evidence",
    SLOT_INDEXING_CERT: "Research Director certification of Scopus/WoS/ACI indexing at publication",
    SLOT_CONTRIBUTION_CERT: "Certificate of Contribution (Annex D — research output)",
    SLOT_CITING_PUBLICATION: "Citing article published in Scopus/WoS/ACI-indexed journal",
    SLOT_TRANSLATION_IMPACT: "Research basis and proof of project, policy, or product utilization",
}


def is_criterion_a_indicator(indicator_id: str) -> bool:
    return (indicator_id or "").startswith(f"{CRITERION_A_ID}-")


def criterion_a_required_slots(indicator_id: str) -> tuple[str, ...]:
    return _CRITERION_A_SLOTS.get((indicator_id or "").strip(), (SLOT_PRIMARY_OUTPUT,))


def criterion_a_slot_label(slot_id: str, *, indicator_id: str = "") -> str:
    iid = (indicator_id or "").strip()
    if slot_id == SLOT_PRIMARY_OUTPUT:
        if "book" in iid or "monograph" in iid:
            return "Published book (PDF)"
        if "chapter" in iid:
            return "Published chapter (PDF)"
        if "journal" in iid:
            return "Published article (PDF)"
        if "translation" in iid:
            return "Research output (PDF)"
        if "cite" in iid:
            return "Your cited article (PDF)"
    if slot_id == SLOT_CONTRIBUTION_CERT and iid == "kra2-a-translation-co":
        return "Certificate of Contribution (Annex E — translated research)"
    return _SLOT_LABELS.get(slot_id, slot_id.replace("_", " "))


# Legacy mobile/web slot ids that map to the canonical Annex A peer-review slot.
CRITERION_A_LEGACY_SLOT_ALIASES: dict[str, str] = {
    "peer_review": SLOT_PEER_REVIEW,
    "peer_review_document": SLOT_PEER_REVIEW,
    "reputable_press_evidence": SLOT_PEER_REVIEW,
    "academic_press_evidence": SLOT_PEER_REVIEW,
}


def migrate_legacy_criterion_a_checklist_slots(
    checklist: dict[str, Any],
    *,
    indicator_id: str,
) -> bool:
    """Move uploaded legacy slot rows onto canonical ids without deleting documents."""
    if not is_criterion_a_indicator(indicator_id):
        return False
    changed = False
    for legacy_id, canonical_id in CRITERION_A_LEGACY_SLOT_ALIASES.items():
        legacy_entry = checklist.get(legacy_id)
        if not isinstance(legacy_entry, dict):
            continue
        canonical = checklist.get(canonical_id)
        if not isinstance(canonical, dict):
            from documents.kra2_evidence.bundle import empty_checklist_entry

            canonical = empty_checklist_entry()
            checklist[canonical_id] = canonical
        if legacy_entry.get("documentId") and not canonical.get("documentId"):
            canonical.update(
                {
                    "documentId": legacy_entry.get("documentId"),
                    "fileHash": legacy_entry.get("fileHash"),
                    "status": legacy_entry.get("status") or canonical.get("status"),
                    "reviewerNote": legacy_entry.get("reviewerNote") or "",
                }
            )
            changed = True
        del checklist[legacy_id]
        changed = True
    return changed
