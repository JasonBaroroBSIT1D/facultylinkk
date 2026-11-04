# KRA III evidence matrix (implementation)

Structured slots live in `backend/documents/kra3_evidence/kra3_evidence_slots.py`.

Families: linkage, income, accreditation, judging, consultancy, media (column/host/guest), resource_person, extension_project, csr, designation, generic_service.

API exposes `requiredEvidenceSlots`, `slotLabels`, and `evidenceChecklist` on bundle GET/PATCH.

Prior audit mapping: `docs/KRA3_OFFICIAL_EVIDENCE_MATRIX.md`.
