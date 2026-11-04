# KRA II Criterion A — official vs configured scoring audit

Source: DBM–CHED Joint Circular No. 01, s. 2026 — Sections 16–21, Annex A (PDF pp. 78–81).

| Indicator | Official base | Official cap / group | Configured points | Configured max | PDF status | Reference |
|---|---:|---:|---:|---:|---|---|
| kra2-a-book-sole | 100 | 100 | 100.0 | 100.0 | VERIFIED_POINTS | Annex A p.78 item 1 |
| kra2-a-book-co | 100 | 100 | 100.0 | 100.0 | PARTIAL | Annex A p.78 + Annex D (Sec. 18) |
| kra2-a-chapter-sole | 35 | 35 | 35.0 | 35.0 | VERIFIED_POINTS | Annex A p.78 item 2 |
| kra2-a-chapter-co | 35 | 35 | 35.0 | 35.0 | PARTIAL | Annex A + Annex D |
| kra2-a-journal-sole | 50 | 50 | 50.0 | 50.0 | PARTIAL | Annex A p.79 item 3; Sec. 19 indexing |
| kra2-a-journal-co | 50 | 50 | 50.0 | 50.0 | PARTIAL | Annex A + Annex D |
| kra2-a-monograph-sole | 100 | 100 | 100.0 | 100.0 | VERIFIED_POINTS | Annex A p.79 item 4 |
| kra2-a-monograph-co | 100 | 100 | 100.0 | 100.0 | PARTIAL | Annex A + Annex D |
| kra2-a-translation-sole | 35 | 70 | 35.0 | 70.0 | VERIFIED_POINTS | Annex A p.80 item 5; group max 70 |
| kra2-a-translation-co | 35 | 70 | 35.0 | 70.0 | PARTIAL | Annex A + Annex E |
| kra2-a-cite | 10 | 60 | 10.0 | 60.0 | PARTIAL | Sec. 21; Annex A p.81 item 6; group max 60 |

## Criterion / KRA caps

| Level | Official | Configured |
|---|---:|---:|
| Criterion A maximum | 100 | 100 (`kra2-a` in rules + published settings) |
| KRA II maximum | 100 | 100 |

## Discrepancies corrected

**None.** Catalog (`kra2_indicators.json`), `rules.js`, and Admin indicator rows already match Annex A base points and group caps. This audit added Annex A evidence checklists and reviewer UI clarity; no silent change to historical published scoring versions.

## Configuration versioning

- New accomplishments lock scoring via `record_configuration_in_kra2_bundle` on reviewer approval.
- Existing approved assessments retain their locked `scoringConfigurationVersion`.
- Catalog metadata version remains admin-published; bump only through the normal publish workflow.
