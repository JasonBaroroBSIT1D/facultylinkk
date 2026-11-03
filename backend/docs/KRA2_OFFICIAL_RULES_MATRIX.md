# KRA II — Official Rules Matrix (Implementation Reference)

**Source:** DBM–CHED Joint Circular No. 01, s. 2026 (Enhanced Implementing Guidelines).

Official PDF present at `backend\docs\2026-DBM-CHED-JC-01-Enhanced-Implementing-Guidelines-of-JC3-series-of-2022 (1).pdf` (130 pages). Text extraction is empty (scanned). **Sample annex/body pages visually verified** — see `backend/docs/KRA2_PDF_VERIFICATION_NOTES.md`. Point values for implementation remain **published Admin configuration**; matrix labels below still reference the catalog export, not `rules.js` as proof.

## KRA II totals (catalog)

| Field | Official value (catalog) |
|---|---|
| KRA ID | `kra2` |
| Title | Research, Innovation and/or Creative Work |
| KRA maximum | 100 points (alternative categories — not sum of 300) |
| Criterion A max | 100 |
| Criterion B max | 100 |
| Criterion C max | 100 |

## Implementation status snapshot

- **Admin Scoring Config:** PARTIAL — KRA II in rules.js + publish JSON; no JC-enforced validation
- **Backend Evidence Bundles:** NOT STARTED — no kra2_evidence module (generic Document rows only)
- **Backend Scoring Engine:** PARTIAL — aggregate_documents_for_kra + document-stored points
- **Faculty Mobile:** PARTIAL — KRA explorer + generic upload; no KRA II accomplishment wizard
- **Reviewer Web:** PARTIAL — generic document review; no Criterion A/B/C accomplishment workspaces
- **Rank Simulation:** PARTIAL — kra2 slot uses document aggregates, not full criterion adapters
- **Ocr:** PARTIAL — generic OCR; no KRA II structured metadata extractors

## Indicators by criterion

### Criterion A — Research Outputs Published

| Indicator ID | Name | Base pts | Ind. max | Contribution | Evidence (see rules.js) | Backend bundle |
|---|---|---:|---:|---|---|---|
| `kra2-a-book-co` | Co-author of an academic book | 100.0 | 100.0 | declared | Annex D–G as applicable | NOT STARTED |
| `kra2-a-book-sole` | Sole author of an academic book | 100.0 | 100.0 | sole | Annex D–G as applicable | NOT STARTED |
| `kra2-a-chapter-co` | Co-author of an edited academic book chapter | 35.0 | 35.0 | declared | Annex D–G as applicable | NOT STARTED |
| `kra2-a-chapter-sole` | Sole author of an edited academic book chapter | 35.0 | 35.0 | sole | Annex D–G as applicable | NOT STARTED |
| `kra2-a-cite` | Research publication cited | 10.0 | 60.0 | not-applicable | Annex D–G as applicable | NOT STARTED |
| `kra2-a-journal-co` | Co-author of a journal article | 50.0 | 50.0 | declared | Annex D–G as applicable | **REFERENCE E2E** (Phase 2) |
| `kra2-a-journal-sole` | Sole author of a journal article | 50.0 | 50.0 | sole | Annex D–G as applicable | **REFERENCE E2E** (Phase 2) |
| `kra2-a-monograph-co` | Co-author of an academic monograph | 100.0 | 100.0 | declared | Annex D–G as applicable | NOT STARTED |
| `kra2-a-monograph-sole` | Sole author of an academic monograph | 100.0 | 100.0 | sole | Annex D–G as applicable | NOT STARTED |
| `kra2-a-translation-co` | Research translated into a project, policy, or product — Co-contributor | 35.0 | 70.0 | declared | Annex D–G as applicable | NOT STARTED |
| `kra2-a-translation-sole` | Research translated into a project, policy, or product — Sole / Lead | 35.0 | 70.0 | sole | Annex D–G as applicable | NOT STARTED |

### Criterion B — Inventions

| Indicator ID | Name | Base pts | Ind. max | Contribution | Evidence (see rules.js) | Backend bundle |
|---|---|---:|---:|---|---|---|
| `kra2-b-comm-intl` | Commercialized patented product — International | 10.0 | 30.0 | not-applicable | Annex D–G as applicable | NOT STARTED |
| `kra2-b-comm-local` | Commercialized patented product — Local | 5.0 | 20.0 | not-applicable | Annex D–G as applicable | NOT STARTED |
| `kra2-b-id-co` | Industrial design — Registration (co-inventor) | 5.0 | 5.0 | declared | Annex D–G as applicable | NOT STARTED |
| `kra2-b-id-sole` | Industrial design — Registration (sole inventor) | 5.0 | 5.0 | sole | Annex D–G as applicable | NOT STARTED |
| `kra2-b-patent-a-co` | Invention patent — Acceptance (co-inventor) | 10.0 | 10.0 | declared | Annex D–G as applicable | NOT STARTED |
| `kra2-b-patent-a-sole` | Invention patent — Acceptance (sole inventor) | 10.0 | 10.0 | sole | Annex D–G as applicable | NOT STARTED |
| `kra2-b-patent-g-co` | Invention patent — Grant (co-inventor) | 80.0 | 80.0 | declared | Annex D–G as applicable | NOT STARTED |
| `kra2-b-patent-g-sole` | Invention patent — Grant (sole inventor) | 80.0 | 80.0 | sole | Annex D–G as applicable | NOT STARTED |
| `kra2-b-patent-p-co` | Invention patent — Publication (co-inventor) | 20.0 | 20.0 | declared | Annex D–G as applicable | NOT STARTED |
| `kra2-b-patent-p-sole` | Invention patent — Publication (sole inventor) | 20.0 | 20.0 | sole | Annex D–G as applicable | NOT STARTED |
| `kra2-b-sw-new-co` | New copyrighted and utilized software — Co-developer | 10.0 | 10.0 | declared | Annex D–G as applicable | NOT STARTED |
| `kra2-b-sw-new-sole` | New copyrighted and utilized software — Sole developer | 10.0 | 10.0 | sole | Annex D–G as applicable | NOT STARTED |
| `kra2-b-sw-upd-co` | Updated copyrighted and utilized software — Co-developer | 4.0 | 4.0 | declared | Annex D–G as applicable | NOT STARTED |
| `kra2-b-sw-upd-sole` | Updated copyrighted and utilized software — Sole developer | 4.0 | 4.0 | sole | Annex D–G as applicable | NOT STARTED |
| `kra2-b-um-co` | Utility model — Registration (co-inventor) | 10.0 | 10.0 | declared | Annex D–G as applicable | NOT STARTED |
| `kra2-b-um-sole` | Utility model — Registration (sole inventor) | 10.0 | 10.0 | sole | Annex D–G as applicable | NOT STARTED |
| `kra2-b-variety-co` | New plant variety, animal breed, or microbial strain — Co-developer | 10.0 | 10.0 | declared | Annex D–G as applicable | NOT STARTED |
| `kra2-b-variety-sole` | New plant variety, animal breed, or microbial strain — Sole developer | 10.0 | 10.0 | sole | Annex D–G as applicable | NOT STARTED |

### Criterion C — Citations and Research Impact

| Indicator ID | Name | Base pts | Ind. max | Contribution | Evidence (see rules.js) | Backend bundle |
|---|---|---:|---:|---|---|---|
| `kra2-c-acting` | Acting | 20.0 | 20.0 | not-applicable | Annex D–G as applicable | NOT STARTED |
| `kra2-c-arch-design` | Architectural, engineering, or interior design (exhibition or juried) | 20.0 | 20.0 | not-applicable | Annex D–G as applicable | NOT STARTED |
| `kra2-c-choreo-co` | Original choreography — Co-choreographer | 20.0 | 20.0 | declared | Annex D–G as applicable | NOT STARTED |
| `kra2-c-choreo-sole` | Original choreography | 20.0 | 20.0 | sole | Annex D–G as applicable | NOT STARTED |
| `kra2-c-conducting` | Conducting | 10.0 | 10.0 | not-applicable | Annex D–G as applicable | NOT STARTED |
| `kra2-c-dance-perf` | Dance performance | 10.0 | 10.0 | not-applicable | Annex D–G as applicable | NOT STARTED |
| `kra2-c-directing` | Theatrical directing | 20.0 | 20.0 | not-applicable | Annex D–G as applicable | NOT STARTED |
| `kra2-c-essay` | Literary publication — Literary essay | 2.0 | 2.0 | not-applicable | Annex D–G as applicable | NOT STARTED |
| `kra2-c-film` | Film (short, feature, documentary, experimental, animated) | 20.0 | 20.0 | not-applicable | Annex D–G as applicable | NOT STARTED |
| `kra2-c-music-arr-co` | Musical arrangement — Co-arranger | 20.0 | 20.0 | declared | Annex D–G as applicable | NOT STARTED |
| `kra2-c-music-arr-sole` | Musical arrangement | 20.0 | 20.0 | sole | Annex D–G as applicable | NOT STARTED |
| `kra2-c-music-comp-co` | Musical composition — Co-composer | 20.0 | 20.0 | declared | Annex D–G as applicable | NOT STARTED |
| `kra2-c-music-comp-sole` | Musical composition | 20.0 | 20.0 | sole | Annex D–G as applicable | NOT STARTED |
| `kra2-c-music-perf` | Musical performance (vocal or instrumental) | 10.0 | 10.0 | not-applicable | Annex D–G as applicable | NOT STARTED |
| `kra2-c-music-prod-co` | Music production — Co-producer | 20.0 | 20.0 | declared | Annex D–G as applicable | NOT STARTED |
| `kra2-c-music-prod-sole` | Music production | 20.0 | 20.0 | sole | Annex D–G as applicable | NOT STARTED |
| `kra2-c-novel-co` | Literary publication — Novel (co-author) | 20.0 | 20.0 | declared | Annex D–G as applicable | NOT STARTED |
| `kra2-c-novel-sole` | Literary publication — Novel | 20.0 | 20.0 | sole | Annex D–G as applicable | NOT STARTED |
| `kra2-c-playwright-co` | Playwright — Co-author | 20.0 | 20.0 | declared | Annex D–G as applicable | NOT STARTED |
| `kra2-c-playwright-sole` | Playwright | 20.0 | 20.0 | sole | Annex D–G as applicable | NOT STARTED |
| `kra2-c-poetry` | Literary publication — Poetry | 2.0 | 2.0 | not-applicable | Annex D–G as applicable | NOT STARTED |
| `kra2-c-prod-design` | Production design | 20.0 | 20.0 | not-applicable | Annex D–G as applicable | NOT STARTED |
| `kra2-c-story-co` | Literary publication — Short story (co-author) | 10.0 | 10.0 | declared | Annex D–G as applicable | NOT STARTED |
| `kra2-c-story-sole` | Literary publication — Short story | 10.0 | 10.0 | sole | Annex D–G as applicable | NOT STARTED |
| `kra2-c-visual` | Visual arts exhibition (painting, drawing, mixed media, sculpture, photography, digital art) | 20.0 | 20.0 | not-applicable | Annex D–G as applicable | NOT STARTED |

## Scoring rules (all criteria)

- Use **published** Admin configuration for base points and caps (`kra_settings` JSON).
- **Co-authored / declared contribution:** points = base × declared % (Annex D/F/G forms).
- **Group caps:** translation (70), citations (60), commercialization sub-groups — see `groupMax` in rules.js.
- **Patent stages:** credit highest stage only within evaluation period (Criterion B).
- **KRA II total:** min(sum of criterion totals A+B+C, 100) — each criterion capped at 100 first (`criteria_sum_cap_at_kra_max`). PDF p. 78 (KRA II header 100) + Sec. 23.1.f patent rule p. 18.
- **Estimated vs verified:** faculty estimates from published indicator points; reviewer-assessed points on approval.

_Generated 54 indicators from rules.js._
