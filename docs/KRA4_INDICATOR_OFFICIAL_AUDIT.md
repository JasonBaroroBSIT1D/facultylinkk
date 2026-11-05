# KRA IV — Official Indicator Audit (JC 01 s. 2026)

**Scope:** Sections 37–44 and Annex A (Professional Development) as encoded in `backend/kra_configuration/data/kra4_indicators.json` and `web/js/rules.js`.  
**PDF line-by-line verification:** **BLOCKED** — official JC PDF in `backend/docs/` is scanned (no extractable text; see `KRA4_PDF_AUDIT_RESULTS.json`). Catalog `pdfVerified` remains `false`. Manual DBM–CHED PDF cross-check still required.

| Indicator ID | Official reference (in-repo) | Scoring rule (implemented) | Required evidence (families) | Status | Discrepancy / note |
|--------------|-------------------------------|----------------------------|------------------------------|--------|---------------------|
| kra4-a-member | Criterion A — professional org membership | 5 pts; group cap 20 | membership, org profile, participation | Implemented | Non-APO org rules enforced in hints only; full SEC/convention rules need reviewer judgment |
| kra4-b-postmaster | Criterion B — education | 10 pts; educ group cap 40 | diploma, transcript | Implemented | |
| kra4-b-postdoc | Criterion B — education | 10 pts; educ group cap 40 | diploma, transcript | Implemented | |
| kra4-b-masters | Criterion B — education | 20 pts; educ group cap 40 | diploma, transcript | Implemented | |
| kra4-b-doctorate | Criterion B — education | 40 pts; educ group cap 40 | diploma, transcript | Implemented | |
| kra4-b-part-local | Criterion B — capacity building | 1 pt; part group cap 10 | participation cert, program, approval | Implemented | Min 6 hours validated when `eventDurationHours` set |
| kra4-b-part-intl | Criterion B — capacity building | 2 pts; part group cap 10 | same | Implemented | Min 8 hours when scope international |
| kra4-b-paper-local | Criterion B — paper presentation | 3 pts; paper group cap 10 | acceptance, presenter cert, approval, program | Implemented | |
| kra4-b-paper-intl | Criterion B — paper presentation | 5 pts; paper group cap 10 | same + 3-country rule in hints | Implemented | 3-country rule not auto-validated |
| kra4-c-inst | Criterion C — awards | 2 pts | award cert, criteria, org profile | Implemented | |
| kra4-c-local | Criterion C — awards | 3 pts | same | Implemented | |
| kra4-c-national | Criterion C — awards | 4 pts | same | Implemented | |
| kra4-c-intl | — | — | — | **Not implemented** | No official points in Annex A export — intentional |
| kra4-d-pres | Criterion D — prior experience | 5 pts/year × years; D cap 20 | employment, job description | Implemented | “Newly hired” gate not fully wired to profile flags |
| kra4-d-vp | Criterion D | 4 pts/year | same | Implemented | |
| kra4-d-head | Criterion D | 3 pts/year | same | Implemented | |
| kra4-d-faculty | Criterion D | 2 pts/year | same | Implemented | |
| kra4-d-mgr | Criterion D — industry | 4 pts/year | same | Implemented | |
| kra4-d-tech | Criterion D — industry | 3 pts/year | same | Implemented | |
| kra4-d-support | Criterion D — industry | 2 pts/year | same | Implemented | |

**Criterion caps:** A 20, B 60, C 20, D bonus 20, KRA IV total 100 — match `kra4_annex.py`.

**Ambiguities for official clarification:** international awards (Criterion C); newly hired eligibility for Criterion D; virtual vs face-to-face hour thresholds beyond basic 6/8 validation.
