# KRA II OCR coverage matrix (54 indicators)

OCR extraction version: **1.7**.

| Indicator | Criterion | Family | Parser | Metadata fields | OCR keys | Automated |
|---|---|---|---|---|---|---|
| kra2-a-book-co | kra2-a | publication_output | publication | outputTitle,authorsLine,outputVenue,publicationDate,declaredContributionPercent | outputTitle,authorsLine,outputVenue,journalTitle,publicationDate,publicationReference | routing + family snippet |
| kra2-a-book-sole | kra2-a | publication_output | publication | outputTitle,authorsLine,outputVenue,publicationDate | outputTitle,authorsLine,outputVenue,journalTitle,publicationDate,publicationReference | routing + family snippet |
| kra2-a-chapter-co | kra2-a | publication_output | publication | outputTitle,authorsLine,outputVenue,publicationDate,declaredContributionPercent | outputTitle,authorsLine,outputVenue,journalTitle,publicationDate,publicationReference | routing + family snippet |
| kra2-a-chapter-sole | kra2-a | publication_output | publication | outputTitle,authorsLine,outputVenue,publicationDate | outputTitle,authorsLine,outputVenue,journalTitle,publicationDate,publicationReference | routing + family snippet |
| kra2-a-cite | kra2-a | citation_impact | citation | outputTitle,citationContext,publicationDate | outputTitle,citationContext,publicationDate,publicationReference | routing + family snippet |
| kra2-a-journal-co | kra2-a | publication_output | publication | outputTitle,authorsLine,outputVenue,publicationDate,declaredContributionPercent | outputTitle,authorsLine,outputVenue,journalTitle,publicationDate,publicationReference | routing + family snippet |
| kra2-a-journal-sole | kra2-a | publication_output | publication | outputTitle,authorsLine,outputVenue,publicationDate | outputTitle,authorsLine,outputVenue,journalTitle,publicationDate,publicationReference | routing + family snippet |
| kra2-a-monograph-co | kra2-a | publication_output | publication | outputTitle,authorsLine,outputVenue,publicationDate,declaredContributionPercent | outputTitle,authorsLine,outputVenue,journalTitle,publicationDate,publicationReference | routing + family snippet |
| kra2-a-monograph-sole | kra2-a | publication_output | publication | outputTitle,authorsLine,outputVenue,publicationDate | outputTitle,authorsLine,outputVenue,journalTitle,publicationDate,publicationReference | routing + family snippet |
| kra2-a-translation-co | kra2-a | publication_output | publication | outputTitle,authorsLine,outputVenue,publicationDate,declaredContributionPercent | outputTitle,authorsLine,outputVenue,journalTitle,publicationDate,publicationReference | routing + family snippet |
| kra2-a-translation-sole | kra2-a | publication_output | publication | outputTitle,authorsLine,outputVenue,publicationDate | outputTitle,authorsLine,outputVenue,journalTitle,publicationDate,publicationReference | routing + family snippet |
| kra2-b-comm-intl | kra2-b | commercialization | commercial | outputTitle,outputVenue,publicationDate,authorsLine | outputTitle,authorsLine,outputVenue,publicationDate,registrationNumber,registrationDate | routing + family snippet |
| kra2-b-comm-local | kra2-b | commercialization | commercial | outputTitle,outputVenue,publicationDate,authorsLine | outputTitle,authorsLine,outputVenue,publicationDate,registrationNumber,registrationDate | routing + family snippet |
| kra2-b-id-co | kra2-b | invention_ip | invention | outputTitle,registrationNumber,registrationDate,authorsLine,declaredContributionPercent | outputTitle,authorsLine,registrationNumber,registrationDate,outputVenue | routing + family snippet |
| kra2-b-id-sole | kra2-b | invention_ip | invention | outputTitle,registrationNumber,registrationDate,authorsLine | outputTitle,authorsLine,registrationNumber,registrationDate,outputVenue | routing + family snippet |
| kra2-b-patent-a-co | kra2-b | invention_ip | invention | outputTitle,registrationNumber,registrationDate,authorsLine,declaredContributionPercent | outputTitle,authorsLine,registrationNumber,registrationDate,outputVenue | routing + family snippet |
| kra2-b-patent-a-sole | kra2-b | invention_ip | invention | outputTitle,registrationNumber,registrationDate,authorsLine | outputTitle,authorsLine,registrationNumber,registrationDate,outputVenue | routing + family snippet |
| kra2-b-patent-g-co | kra2-b | invention_ip | invention | outputTitle,registrationNumber,registrationDate,authorsLine,declaredContributionPercent | outputTitle,authorsLine,registrationNumber,registrationDate,outputVenue | routing + family snippet |
| kra2-b-patent-g-sole | kra2-b | invention_ip | invention | outputTitle,registrationNumber,registrationDate,authorsLine | outputTitle,authorsLine,registrationNumber,registrationDate,outputVenue | routing + family snippet |
| kra2-b-patent-p-co | kra2-b | invention_ip | invention | outputTitle,registrationNumber,registrationDate,authorsLine,declaredContributionPercent | outputTitle,authorsLine,registrationNumber,registrationDate,outputVenue | routing + family snippet |
| kra2-b-patent-p-sole | kra2-b | invention_ip | invention | outputTitle,registrationNumber,registrationDate,authorsLine | outputTitle,authorsLine,registrationNumber,registrationDate,outputVenue | routing + family snippet |
| kra2-b-sw-new-co | kra2-b | invention_ip | software | outputTitle,registrationNumber,registrationDate,authorsLine,declaredContributionPercent | outputTitle,authorsLine,registrationNumber,registrationDate,outputVenue | labeled software/copyright fixture |
| kra2-b-sw-new-sole | kra2-b | invention_ip | software | outputTitle,registrationNumber,registrationDate,authorsLine | outputTitle,authorsLine,registrationNumber,registrationDate,outputVenue | labeled software/copyright fixture |
| kra2-b-sw-upd-co | kra2-b | invention_ip | software | outputTitle,registrationNumber,registrationDate,authorsLine,declaredContributionPercent | outputTitle,authorsLine,registrationNumber,registrationDate,outputVenue | labeled software/copyright fixture |
| kra2-b-sw-upd-sole | kra2-b | invention_ip | software | outputTitle,registrationNumber,registrationDate,authorsLine | outputTitle,authorsLine,registrationNumber,registrationDate,outputVenue | labeled software/copyright fixture |
| kra2-b-um-co | kra2-b | invention_ip | invention | outputTitle,registrationNumber,registrationDate,authorsLine,declaredContributionPercent | outputTitle,authorsLine,registrationNumber,registrationDate,outputVenue | routing + family snippet |
| kra2-b-um-sole | kra2-b | invention_ip | invention | outputTitle,registrationNumber,registrationDate,authorsLine | outputTitle,authorsLine,registrationNumber,registrationDate,outputVenue | routing + family snippet |
| kra2-b-variety-co | kra2-b | invention_ip | variety | outputTitle,registrationNumber,registrationDate,authorsLine,declaredContributionPercent | outputTitle,authorsLine,registrationNumber,registrationDate,outputVenue | labeled cultivar/deposit fixture |
| kra2-b-variety-sole | kra2-b | invention_ip | variety | outputTitle,registrationNumber,registrationDate,authorsLine | outputTitle,authorsLine,registrationNumber,registrationDate,outputVenue | labeled cultivar/deposit fixture |
| kra2-c-acting | kra2-c | performance_work | creative | outputTitle,authorsLine,outputVenue,publicationDate | outputTitle,authorsLine,outputVenue,publicationDate | routing + family snippet |
| kra2-c-arch-design | kra2-c | creative_work | creative | outputTitle,authorsLine,outputVenue,publicationDate | outputTitle,authorsLine,outputVenue,publicationDate,publicationReference | routing + family snippet |
| kra2-c-choreo-co | kra2-c | creative_work | creative | outputTitle,authorsLine,outputVenue,publicationDate,declaredContributionPercent | outputTitle,authorsLine,outputVenue,publicationDate,publicationReference | routing + family snippet |
| kra2-c-choreo-sole | kra2-c | creative_work | creative | outputTitle,authorsLine,outputVenue,publicationDate | outputTitle,authorsLine,outputVenue,publicationDate,publicationReference | routing + family snippet |
| kra2-c-conducting | kra2-c | performance_work | creative | outputTitle,authorsLine,outputVenue,publicationDate | outputTitle,authorsLine,outputVenue,publicationDate | routing + family snippet |
| kra2-c-dance-perf | kra2-c | performance_work | creative | outputTitle,authorsLine,outputVenue,publicationDate | outputTitle,authorsLine,outputVenue,publicationDate | routing + family snippet |
| kra2-c-directing | kra2-c | performance_work | creative | outputTitle,authorsLine,outputVenue,publicationDate | outputTitle,authorsLine,outputVenue,publicationDate | routing + family snippet |
| kra2-c-essay | kra2-c | creative_work | creative | outputTitle,authorsLine,outputVenue,publicationDate | outputTitle,authorsLine,outputVenue,publicationDate,publicationReference | routing + family snippet |
| kra2-c-film | kra2-c | creative_work | creative | outputTitle,authorsLine,outputVenue,publicationDate | outputTitle,authorsLine,outputVenue,publicationDate,publicationReference | routing + family snippet |
| kra2-c-music-arr-co | kra2-c | creative_work | creative | outputTitle,authorsLine,outputVenue,publicationDate,declaredContributionPercent | outputTitle,authorsLine,outputVenue,publicationDate,publicationReference | routing + family snippet |
| kra2-c-music-arr-sole | kra2-c | creative_work | creative | outputTitle,authorsLine,outputVenue,publicationDate | outputTitle,authorsLine,outputVenue,publicationDate,publicationReference | routing + family snippet |
| kra2-c-music-comp-co | kra2-c | creative_work | creative | outputTitle,authorsLine,outputVenue,publicationDate,declaredContributionPercent | outputTitle,authorsLine,outputVenue,publicationDate,publicationReference | routing + family snippet |
| kra2-c-music-comp-sole | kra2-c | creative_work | creative | outputTitle,authorsLine,outputVenue,publicationDate | outputTitle,authorsLine,outputVenue,publicationDate,publicationReference | routing + family snippet |
| kra2-c-music-perf | kra2-c | performance_work | creative | outputTitle,authorsLine,outputVenue,publicationDate | outputTitle,authorsLine,outputVenue,publicationDate | routing + family snippet |
| kra2-c-music-prod-co | kra2-c | creative_work | creative | outputTitle,authorsLine,outputVenue,publicationDate,declaredContributionPercent | outputTitle,authorsLine,outputVenue,publicationDate,publicationReference | routing + family snippet |
| kra2-c-music-prod-sole | kra2-c | creative_work | creative | outputTitle,authorsLine,outputVenue,publicationDate | outputTitle,authorsLine,outputVenue,publicationDate,publicationReference | routing + family snippet |
| kra2-c-novel-co | kra2-c | creative_work | creative | outputTitle,authorsLine,outputVenue,publicationDate,declaredContributionPercent | outputTitle,authorsLine,outputVenue,publicationDate,publicationReference | routing + family snippet |
| kra2-c-novel-sole | kra2-c | creative_work | creative | outputTitle,authorsLine,outputVenue,publicationDate | outputTitle,authorsLine,outputVenue,publicationDate,publicationReference | routing + family snippet |
| kra2-c-playwright-co | kra2-c | creative_work | creative | outputTitle,authorsLine,outputVenue,publicationDate,declaredContributionPercent | outputTitle,authorsLine,outputVenue,publicationDate,publicationReference | routing + family snippet |
| kra2-c-playwright-sole | kra2-c | creative_work | creative | outputTitle,authorsLine,outputVenue,publicationDate | outputTitle,authorsLine,outputVenue,publicationDate,publicationReference | routing + family snippet |
| kra2-c-poetry | kra2-c | creative_work | creative | outputTitle,authorsLine,outputVenue,publicationDate | outputTitle,authorsLine,outputVenue,publicationDate,publicationReference | routing + family snippet |
| kra2-c-prod-design | kra2-c | creative_work | creative | outputTitle,authorsLine,outputVenue,publicationDate | outputTitle,authorsLine,outputVenue,publicationDate,publicationReference | routing + family snippet |
| kra2-c-story-co | kra2-c | creative_work | creative | outputTitle,authorsLine,outputVenue,publicationDate,declaredContributionPercent | outputTitle,authorsLine,outputVenue,publicationDate,publicationReference | routing + family snippet |
| kra2-c-story-sole | kra2-c | creative_work | creative | outputTitle,authorsLine,outputVenue,publicationDate | outputTitle,authorsLine,outputVenue,publicationDate,publicationReference | routing + family snippet |
| kra2-c-visual | kra2-c | creative_work | creative | outputTitle,authorsLine,outputVenue,publicationDate | outputTitle,authorsLine,outputVenue,publicationDate,publicationReference | routing + family snippet |

## Status legend

- **IMPLEMENTED**: Family parser + `ocr_profiles` row + `extract_fields_for_indicator` routing.
- **TESTED (automated)**: `test_kra2_ocr_indicator_coverage` (218 parametrized cases) + layout fixtures.
- **PARTIAL**: Real-world PDF layouts vary; only representative snippets per family, not 54 unique PDFs.
- **NOT TESTED (E2E)**: Full Faculty Mobile upload → draft → submit → Reviewer Web on device/browser.
