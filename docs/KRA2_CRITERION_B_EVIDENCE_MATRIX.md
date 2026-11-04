# KRA II Criterion B — evidence matrix (18 indicators)

Authority: DBM–CHED Joint Circular No. 01, s. 2026 — **Sections 22–24**, Annex A pp. **81–84**, Annex F/G/H contribution forms.  
Implementation: `backend/documents/kra2_evidence/kra2_b_evidence_slots.py` (must match Faculty Mobile `Kra2Catalog` and Reviewer Web `CRITERION_B_REQUIRED_SLOTS`).

## Co-authored evidence rule (Annex A + catalog `evidenceHints`)

| Family | Sole inventor / developer | Co-inventor / co-developer |
|---|---|---|
| Invention patent (A/P/G) | IPOPHL stage document + invention photo + President Special Order | **IPOPHL stage document only** + **Annex F** (not photo/SO per catalog hints) |
| Utility model / industrial design | Registration certificate + photo + Special Order | **Registration certificate** + **Annex F** |
| Commercialization (local/intl) | Five-slot bundle (no contribution) | Same (not co-scored) |
| New / updated software | Full software checklist (SO, summary, copyright, utilization, …) | **Same checklist as sole** + **Annex G** |
| Plant variety / breed / strain | Special Order + registration/deposit | **Registration/deposit only** + **Annex H** (no separate SO in catalog hints) |

Co-authored rows still require **declared contribution %** at submit time; OCR does not auto-verify contribution certificates.

## Slot matrix

| Indicator | Required checklist slot IDs |
|---|---|
| `kra2-b-patent-a-sole` | `primary_output`, `invention_photo`, `president_special_order` |
| `kra2-b-patent-p-sole` | same as acceptance sole |
| `kra2-b-patent-g-sole` | same as acceptance sole |
| `kra2-b-patent-a-co` | `primary_output`, `contribution_certificate` |
| `kra2-b-patent-p-co` | same as patent A co |
| `kra2-b-patent-g-co` | same as patent A co |
| `kra2-b-comm-local` | `product_photo`, `patent_certificate`, `licensing_or_cpr_evidence`, `commercialization_proof`, `rd_itso_certification` |
| `kra2-b-comm-intl` | same as comm local |
| `kra2-b-um-sole` | `primary_output`, `invention_photo`, `president_special_order` |
| `kra2-b-id-sole` | same as UM sole |
| `kra2-b-um-co` | `primary_output`, `contribution_certificate` |
| `kra2-b-id-co` | same as UM co |
| `kra2-b-sw-new-sole` | `president_special_order`, `project_summary`, `software_documentation`, `primary_output`, `utilization_certification` |
| `kra2-b-sw-new-co` | sole new-software slots + `contribution_certificate` |
| `kra2-b-sw-upd-sole` | `president_special_order`, `project_summary`, `primary_output`, `utilization_certification`, `software_update_description` |
| `kra2-b-sw-upd-co` | sole updated-software slots + `contribution_certificate` |
| `kra2-b-variety-sole` | `president_special_order`, `registration_deposit_evidence` |
| `kra2-b-variety-co` | `registration_deposit_evidence`, `contribution_certificate` |

**Primary upload routing:** When `primary_output` is not in the required list (commercialization, variety co), the faculty’s first accomplishment PDF is stored on the **first required slot** (`product_photo` or `registration_deposit_evidence`) via `primary_evidence_slot()`.

## Reviewer parity

- Reviewer Web loads `requiredEvidenceSlots` from the accomplishments API; fallback catalog matches backend.
- Each slot supports authenticated in-workspace preview (same mechanism as Criterion A primary/supporting).
- `approvalBlockers` on the bundle validation payload is authoritative for the approval checklist UI.
