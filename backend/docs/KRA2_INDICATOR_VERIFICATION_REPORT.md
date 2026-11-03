# KRA II — Per-indicator PDF verification report

**Total indicators:** 54
**Points match annex (VERIFIED_POINTS):** 32
**PARTIAL (points OK; co-author/indexing eligibility):** 22
**MISMATCH:** 0

## KRA II aggregation (official)

- **Status:** CONFIRMED_IMPLEMENTATION
- **Formula:** `kra2_total = min(criterion_a + criterion_b + criterion_c, 100)`
- **Per criterion:** `criterion_total = min(sum(eligible_accomplishments_after_dedup_and_group_caps), 100)`
- **PDF evidence:**
  - Annex p.78: KRA II total 100; Criteria A/B/C each Max=100
  - Sec. 28 (KRA III) explicit sum-then-cap pattern (parallel structure)
  - Sec. 23.1.f p.18: patent highest stage within period

## Indicators

| ID | Status | PDF pages | Points (cat/PDF) | Max | Formula |
|---|---|---|---:|---:|---|
| `kra2-a-book-sole` | VERIFIED_POINTS | [78] | 100.0/100 | 100.0/100 | fixed |
| `kra2-a-book-co` | PARTIAL | [78, 12] | 100.0/100 | 100.0/100 | percent × base |
| `kra2-a-chapter-sole` | VERIFIED_POINTS | [78] | 35.0/35 | 35.0/35 | fixed |
| `kra2-a-chapter-co` | PARTIAL | [78, 12] | 35.0/35 | 35.0/35 | percent × base |
| `kra2-a-journal-sole` | PARTIAL | [79] | 50.0/50 | 50.0/50 | fixed |
| `kra2-a-journal-co` | PARTIAL | [79, 12] | 50.0/50 | 50.0/50 | percent × base |
| `kra2-a-monograph-sole` | VERIFIED_POINTS | [79] | 100.0/100 | 100.0/100 | fixed |
| `kra2-a-monograph-co` | PARTIAL | [79, 12] | 100.0/100 | 100.0/100 | percent × base |
| `kra2-a-translation-sole` | VERIFIED_POINTS | [80] | 35.0/35 | 70.0/35 | fixed |
| `kra2-a-translation-co` | PARTIAL | [80, 16] | 35.0/35 | 70.0/35 | percent × base |
| `kra2-a-cite` | PARTIAL | [17, 81] | 10.0/10 | 60.0/10 | per cited article |
| `kra2-b-patent-a-sole` | VERIFIED_POINTS | [81, 18] | 10.0/10 | 10.0/10 | stage A; highest stage only |
| `kra2-b-patent-a-co` | PARTIAL | [81, 18, 19] | 10.0/10 | 10.0/10 | percent × stage A |
| `kra2-b-patent-p-sole` | VERIFIED_POINTS | [81, 18] | 20.0/20 | 20.0/20 | stage P; highest stage only |
| `kra2-b-patent-p-co` | PARTIAL | [81, 18, 19] | 20.0/20 | 20.0/20 | percent × stage P |
| `kra2-b-patent-g-sole` | VERIFIED_POINTS | [81, 18] | 80.0/80 | 80.0/80 | stage G; highest stage only |
| `kra2-b-patent-g-co` | PARTIAL | [81, 18, 19] | 80.0/80 | 80.0/80 | percent × stage G |
| `kra2-b-comm-local` | VERIFIED_POINTS | [20, 82] | 5.0/5 | 20.0/5 | per product |
| `kra2-b-comm-intl` | VERIFIED_POINTS | [20, 82] | 10.0/10 | 30.0/10 | per product |
| `kra2-b-um-sole` | VERIFIED_POINTS | [82] | 10.0/10 | 10.0/10 | fixed |
| `kra2-b-um-co` | PARTIAL | [82, 19] | 10.0/10 | 10.0/10 | percent × base |
| `kra2-b-id-sole` | VERIFIED_POINTS | [82] | 5.0/5 | 5.0/5 | fixed |
| `kra2-b-id-co` | PARTIAL | [82, 19] | 5.0/5 | 5.0/5 | percent × base |
| `kra2-b-sw-new-sole` | VERIFIED_POINTS | [83] | 10.0/10 | 10.0/10 | fixed |
| `kra2-b-sw-new-co` | PARTIAL | [83] | 10.0/10 | 10.0/10 | percent × base |
| `kra2-b-sw-upd-sole` | VERIFIED_POINTS | [83] | 4.0/4 | 4.0/4 | fixed |
| `kra2-b-sw-upd-co` | PARTIAL | [83] | 4.0/4 | 4.0/4 | percent × base |
| `kra2-b-variety-sole` | VERIFIED_POINTS | [83, 84] | 10.0/10 | 10.0/10 | fixed |
| `kra2-b-variety-co` | PARTIAL | [83, 84] | 10.0/10 | 10.0/10 | percent × base |
| `kra2-c-music-comp-sole` | VERIFIED_POINTS | [84, 85] | 20.0/20 | 20.0/20 | fixed |
| `kra2-c-music-comp-co` | PARTIAL | [84, 85] | 20.0/20 | 20.0/20 | percent × base |
| `kra2-c-music-arr-sole` | VERIFIED_POINTS | [85] | 20.0/20 | 20.0/20 | fixed |
| `kra2-c-music-arr-co` | PARTIAL | [85] | 20.0/20 | 20.0/20 | percent × base |
| `kra2-c-music-perf` | VERIFIED_POINTS | [86] | 10.0/10 | 10.0/10 | fixed |
| `kra2-c-conducting` | VERIFIED_POINTS | [86] | 10.0/10 | 10.0/10 | fixed |
| `kra2-c-music-prod-sole` | VERIFIED_POINTS | [86] | 20.0/20 | 20.0/20 | fixed |
| `kra2-c-music-prod-co` | PARTIAL | [86] | 20.0/20 | 20.0/20 | percent × base |
| `kra2-c-choreo-sole` | VERIFIED_POINTS | [87] | 20.0/20 | 20.0/20 | fixed |
| `kra2-c-choreo-co` | PARTIAL | [87] | 20.0/20 | 20.0/20 | percent × base |
| `kra2-c-dance-perf` | VERIFIED_POINTS | [87] | 10.0/10 | 10.0/10 | fixed |
| `kra2-c-playwright-sole` | VERIFIED_POINTS | [88] | 20.0/20 | 20.0/20 | fixed |
| `kra2-c-playwright-co` | PARTIAL | [88] | 20.0/20 | 20.0/20 | percent × base |
| `kra2-c-directing` | VERIFIED_POINTS | [88] | 20.0/20 | 20.0/20 | fixed |
| `kra2-c-acting` | VERIFIED_POINTS | [88] | 20.0/20 | 20.0/20 | fixed |
| `kra2-c-prod-design` | VERIFIED_POINTS | [88, 89] | 20.0/20 | 20.0/20 | fixed |
| `kra2-c-visual` | VERIFIED_POINTS | [89] | 20.0/20 | 20.0/20 | fixed |
| `kra2-c-arch-design` | VERIFIED_POINTS | [89] | 20.0/20 | 20.0/20 | fixed |
| `kra2-c-film` | VERIFIED_POINTS | [90] | 20.0/20 | 20.0/20 | fixed |
| `kra2-c-novel-sole` | VERIFIED_POINTS | [91] | 20.0/20 | 20.0/20 | fixed |
| `kra2-c-novel-co` | PARTIAL | [91] | 20.0/20 | 20.0/20 | percent × base |
| `kra2-c-story-sole` | VERIFIED_POINTS | [91] | 10.0/10 | 10.0/10 | fixed |
| `kra2-c-story-co` | PARTIAL | [91] | 10.0/10 | 10.0/10 | percent × base |
| `kra2-c-poetry` | VERIFIED_POINTS | [92] | 2.0/2 | 2.0/2 | fixed |
| `kra2-c-essay` | VERIFIED_POINTS | [92] | 2.0/2 | 2.0/2 | fixed |

## PARTIAL indicator IDs (eligibility / co-author)

`kra2-a-book-co`, `kra2-a-chapter-co`, `kra2-a-journal-sole`, `kra2-a-journal-co`, `kra2-a-monograph-co`, `kra2-a-translation-co`, `kra2-a-cite`, `kra2-b-patent-a-co`, `kra2-b-patent-p-co`, `kra2-b-patent-g-co`, `kra2-b-um-co`, `kra2-b-id-co`, `kra2-b-sw-new-co`, `kra2-b-sw-upd-co`, `kra2-b-variety-co`, `kra2-c-music-comp-co`, `kra2-c-music-arr-co`, `kra2-c-music-prod-co`, `kra2-c-choreo-co`, `kra2-c-playwright-co`, `kra2-c-novel-co`, `kra2-c-story-co`
