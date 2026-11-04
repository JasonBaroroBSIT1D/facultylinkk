# KRA II Criterion C (Creative Works) — official rules audit

Source: DBM–CHED Joint Circular No. 01, s. 2026 — **Sections 25–27**, Annex A pp. **84–92**.

Point values cross-check `kra2_indicator_pdf_verification.py`. Evidence slot IDs: 
`backend/documents/kra2_evidence/kra2_c_evidence_slots.py` (aligned to catalog `evidenceHints`).

## Policy rules (Sections 25–27)

| Rule | PDF reference | Implementation |
|---|---|---|
| Criterion C maximum **100** points | Sec. 25, p. 24; Annex p. 84 | `published_kra2_criterion_max_points('kra2-c')` |
| KRA II total = A + B + C capped at **100** | Annex p. 78 | `aggregate_kra2_kra_from_documents` |
| Co-creator points = base × declared % (Annex I) | Sec. 26 / Annex I | `estimated_points_for_bundle` + contribution certificate slot |
| Multiple accomplishments sum to criterion cap | Annex “per output” rows | `aggregate_kra2_criterion_from_documents` |
| Verified points only after reviewer approval | General KRA II workflow | `score_accomplishment_document` |

## Scoring matrix (25 indicators)

| Indicator | Official base | Output max | Configured | PDF status | Annex ref | Required evidence slots |
|---|---:|---:|---:|---|---|---|
| `kra2-c-music-comp-sole` | 20 | 20 | 20.0 / 20.0 | VERIFIED_POINTS | C.1.1.1.1 Composition | `primary_output, invitation_acceptance, performance_proof` |
| `kra2-c-music-comp-co` | 20 | 20 | 20.0 / 20.0 | PARTIAL | C.1.1.1.1 + Annex I | `primary_output, contribution_certificate` |
| `kra2-c-music-arr-sole` | 20 | 20 | 20.0 / 20.0 | VERIFIED_POINTS | C.1.1.1.2 Arrangement | `primary_output, invitation_acceptance, performance_proof, role_certification` |
| `kra2-c-music-arr-co` | 20 | 20 | 20.0 / 20.0 | PARTIAL | C.1.1.1.2 + Annex I | `primary_output, contribution_certificate` |
| `kra2-c-music-perf` | 10 | 10 | 10.0 / 10.0 | VERIFIED_POINTS | C.1.1.1.3 Performance | `primary_output, invitation_acceptance, role_certification` |
| `kra2-c-conducting` | 10 | 10 | 10.0 / 10.0 | VERIFIED_POINTS | C.1.1.1.4 Conducting | `primary_output, invitation_acceptance, role_certification` |
| `kra2-c-music-prod-sole` | 20 | 20 | 20.0 / 20.0 | VERIFIED_POINTS | C.1.1.1.5 Music production | `primary_output, copyright_registration, published_release, role_certification` |
| `kra2-c-music-prod-co` | 20 | 20 | 20.0 / 20.0 | PARTIAL | C.1.1.1.5 + Annex I | `primary_output, contribution_certificate` |
| `kra2-c-choreo-sole` | 20 | 20 | 20.0 / 20.0 | VERIFIED_POINTS | C.1.1.2 Choreography | `primary_output, invitation_acceptance, performance_proof, role_certification` |
| `kra2-c-choreo-co` | 20 | 20 | 20.0 / 20.0 | PARTIAL | C.1.1.2 + Annex I | `primary_output, contribution_certificate` |
| `kra2-c-dance-perf` | 10 | 10 | 10.0 / 10.0 | VERIFIED_POINTS | C.1.1.2 Dance performance | `primary_output, role_certification` |
| `kra2-c-playwright-sole` | 20 | 20 | 20.0 / 20.0 | VERIFIED_POINTS | C.1.1.3.1 Playwright | `primary_output, copyright_registration, invitation_acceptance, production_proof, role_certification` |
| `kra2-c-playwright-co` | 20 | 20 | 20.0 / 20.0 | PARTIAL | C.1.1.3.1 + Annex I | `primary_output, contribution_certificate` |
| `kra2-c-directing` | 20 | 20 | 20.0 / 20.0 | VERIFIED_POINTS | C.1.1.3.2 Directing | `primary_output, program_documentation, media_documentation, role_certification` |
| `kra2-c-acting` | 20 | 20 | 20.0 / 20.0 | VERIFIED_POINTS | C.1.1.3.3 Acting | `primary_output, program_documentation, media_documentation, role_certification` |
| `kra2-c-prod-design` | 20 | 20 | 20.0 / 20.0 | VERIFIED_POINTS | C.1.1.3.4 Production design | `primary_output, design_portfolio, media_documentation, program_documentation, role_certification` |
| `kra2-c-visual` | 20 | 20 | 20.0 / 20.0 | VERIFIED_POINTS | C.1.2 Visual arts | `primary_output, invitation_acceptance, exhibition_catalog, gallery_documentation, role_certification` |
| `kra2-c-arch-design` | 20 | 20 | 20.0 / 20.0 | VERIFIED_POINTS | C.1.2.7 Arch/interior | `primary_output, invitation_acceptance, exhibition_documentation, authorship_documentation, organizing_body_info` |
| `kra2-c-film` | 20 | 20 | 20.0 / 20.0 | VERIFIED_POINTS | C.1.3 Film | `primary_output, invitation_acceptance, festival_program, role_certification` |
| `kra2-c-novel-sole` | 20 | 20 | 20.0 / 20.0 | VERIFIED_POINTS | C.1.4.1 Novel | `primary_output, editorial_review, publisher_credibility` |
| `kra2-c-novel-co` | 20 | 20 | 20.0 / 20.0 | PARTIAL | C.1.4.1 + Annex I | `primary_output, contribution_certificate` |
| `kra2-c-story-sole` | 10 | 10 | 10.0 / 10.0 | VERIFIED_POINTS | C.1.4.2 Short story | `primary_output, editorial_review, publisher_credibility` |
| `kra2-c-story-co` | 10 | 10 | 10.0 / 10.0 | PARTIAL | C.1.4.2 + Annex I | `primary_output, contribution_certificate` |
| `kra2-c-poetry` | 2 | 2 | 2.0 / 2.0 | VERIFIED_POINTS | C.1.4.3 Poetry | `primary_output, editorial_review, publisher_credibility` |
| `kra2-c-essay` | 2 | 2 | 2.0 / 2.0 | VERIFIED_POINTS | C.1.4.4 Literary essay | `primary_output, editorial_review, publisher_credibility` |

## Points vs Maximum (Admin UI)

- **Points** — official **base points per qualifying output** (Annex A “Points” column).
- **Maximum** — for Criterion C indicators, equals **per-accomplishment cap** (same as base for fixed rows; 
co-authored rows use base × verified contribution %, capped by this maximum).
- **Criterion C `maxPoints` (100)** — **aggregate cap** for all approved Criterion C accomplishments in the evaluation period.
- **Not** a separate “group max” tier for creative works (unlike translation or commercialization in Criteria A/B).

## Discrepancies

**None** — catalog, `rules.js`, and PDF verification map agree on base/max for all 25 indicators.
