"""One-off: retarget copied kra2_evidence → kra3_evidence imports and keys."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "documents" / "kra3_evidence"

REPLACEMENTS = [
    ("kra2EvidenceBundle", "kra3EvidenceBundle"),
    ("kra2EvidenceLink", "kra3EvidenceLink"),
    ("KRA II", "KRA III"),
    ("kra2_evidence", "kra3_evidence"),
    ("kra2_annex", "kra3_annex"),
    ("kra2_indicator_registry", "kra3_indicator_registry"),
    ("Kra2EvidenceError", "Kra3EvidenceError"),
    ("validate_kra2_bundle", "validate_kra3_bundle"),
    ("maybe_initialize_kra2_bundle", "maybe_initialize_kra3_bundle"),
    ("reviewer_update_kra2", "reviewer_update_kra3"),
    ("heal_kra2_workflow", "heal_kra3_workflow"),
    ("sync_kra2_document_workflow", "sync_kra3_document_workflow"),
    ("record_configuration_in_kra2_bundle", "record_configuration_in_kra3_bundle"),
    ("published_kra2_", "published_kra3_"),
    ("aggregate_kra2_", "aggregate_kra3_"),
    ("is_kra2_", "is_kra3_"),
    ("kra2_summary_for_faculty", "kra3_summary_for_faculty"),
    ("Kra2AccomplishmentScore", "Kra3AccomplishmentScore"),
    ("is_kra2_primary_accomplishment", "is_kra3_primary_accomplishment"),
    ("[KRA2-B-QA]", "[KRA3-QA]"),
]

SKIP_FILES = {
    "kra2_a_evidence_slots.py",
    "kra2_b_evidence_slots.py",
    "kra2_c_evidence_slots.py",
    "patent_deduplication.py",
    "deduplication.py",
    "ocr_publication.py",
    "indicator_config.py",
}


def main() -> None:
    for path in ROOT.rglob("*.py"):
        if path.name in SKIP_FILES:
            path.unlink()
            continue
        text = path.read_text(encoding="utf-8")
        for old, new in REPLACEMENTS:
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")
    print("Adapted", ROOT)


if __name__ == "__main__":
    main()
