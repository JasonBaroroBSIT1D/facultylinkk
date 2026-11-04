# KRA III — OCR & validation profile recommendations (advisory only)

**Scope:** Design recommendations for a future KRA III workflow. **No OCR or validation code exists for KRA III** in FacultyLink today (unlike `backend/documents/kra2_evidence/ocr_extraction.py`).

**Principles (JC + KRA II precedent)**

- OCR is **advisory**; faculty confirm all fields before submission.  
- OCR must **not** auto-verify authenticity, approve documents, or assign reviewer-verified points.  
- Reject label lines, disclaimers, and instruction boilerplate (see KRA II `is_metadata_label_value` patterns).  
- Income bands and CSR formulas require **structured numeric fields** + Finance/Extension officer certifications — OCR may suggest, reviewer confirms.

---

## Profile summary by family

| Family | Indicators | Primary OCR targets | Validation (backend) |
|--------|------------|---------------------|--------------------|
| Linkage | `kra3-a-linkage` | Partner org, MOA date, signatories, faculty role | MOA + approval + terminal report slots present |
| Income | `kra3-a-income-*` | Amount, date range, Sub-ARO #, cert signatory | Band matches amount; lead/co indicator matches cert |
| Accreditation | `kra3-b-qa-*` | Agency name, appointment date, role | President auth; one row per agency |
| Judging | `kra3-b-judge-*` | Event, organizer, dates | Invitation + engagement + auth |
| Consultancy | `kra3-b-consult-*` | Client, scope, start/end, duration | ≤6 months hint; contract vs invitation |
| Media | column/host/guest | Publication name, date, column title | Count caps (10); broadsheet check manual |
| Resource person | `kra3-b-train-*` | Event, role, **hours**, program time | Hours × rate; exclude in-house-only |
| Extension/ISR | `kra3-b-ext-*` | Project title, role, beneficiaries | Link project ID for CSR |
| CSR | `kra3-c-satisfaction` | Overall rating, AY, instrument version | Formula; B-ISR cross-reference |
| Designation | `kra3-d-*` | Position, effectivity from/to | ≥1 year continuous; per-year row |

---

## Per-indicator OCR field map (recommended metadata keys)

### Criterion A

| Indicator | Suggested fields |
|-----------|------------------|
| `kra3-a-linkage` | `partnerOrganization`, `moaTitle`, `moaDate`, `facultyRole`, `approvingAuthority`, `implementationDate` |
| `kra3-a-income-lead-*` / `co-*` | `incomeSourceType` (commercialization \| grant \| industry), `grossAmount`, `currency`, `periodStart`, `periodEnd`, `financeCertificationDate`, `contributorRole` (lead \| co), `subAroReference` |

### Criterion B

| Indicator | Suggested fields |
|-----------|------------------|
| `kra3-b-qa-local/intl` | `accreditingAgency`, `appointmentTitle`, `serviceDates`, `authorizationReference` |
| `kra3-b-judge-research/academic` | `competitionName`, `organizer`, `eventDate`, `judgeRole` |
| `kra3-b-consult-local/intl` | `clientOrganization`, `scopeSummary`, `durationMonths`, `contractDate` |
| `kra3-b-column-occasional` | `publicationName`, `articleTitle`, `issueDate` (repeat → count toward 10) |
| `kra3-b-column-regular` | `columnName`, `publicationName`, `frequency` |
| `kra3-b-host` | `programTitle`, `station`, `schedule`, `startDate`, `endDate` |
| `kra3-b-guest` | `programTitle`, `stationOrPublisher`, `appearanceDate` |
| `kra3-b-train-local/intl` | `eventTitle`, `facultyRole`, `deliveryHours`, `eventDate`, `venue` |
| `kra3-b-ext-head/participant` | `projectTitle`, `projectRole`, `beneficiarySummary`, `reportDate`, `specialOrderReference` |

### Criterion C

| Indicator | Suggested fields |
|-----------|------------------|
| `kra3-c-satisfaction` | `overallCsrPercent`, `academicYear1`, `rating1`, `academicYear2`, `rating2`, `academicYear3`, `rating3`, `instrumentVersion`, `linkedExtensionProjectIds[]` |

### Criterion D

| Indicator | Suggested fields |
|-----------|------------------|
| All `kra3-d-*` | `designationTitle`, `organizationalLevel` (institutional \| collegial \| department), `effectivityStart`, `effectivityEnd`, `serviceYear`, `governingBoardReference` (committees) |

---

## Parser routing (future)

Mirror KRA II `criterion_c_ocr_parser_id()` pattern:

- `linkage_moa`  
- `finance_certification`  
- `appointment_letter`  
- `invitation_program`  
- `media_clipping`  
- `extension_report`  
- `csr_summary`  
- `designation_order`  

Route by `indicatorId` prefix + detected document layout (MOA vs Sub-ARO vs invitation).

---

## Validation rules (future backend)

| Rule | Source |
|------|--------|
| CSR formula `(overallCSR/100)*20` | §35, Annex |
| ISR group caps 30 head/participant | Annex p. 96 |
| Column/guest group max 10 | Annex |
| Hourly local 2 / intl 3 | Annex |
| Co-income half of lead | §31 |
| CSR requires linked B-ISR accomplishments | §35e |
| Bonus D counts toward KRA III total max 100 | §28 |
| Exclude SUC-internal-only judging | §32e |
| Resource person: program must show **allocated time** | §33.5d |

---

## Reuse from KRA I / II

| Component | Reuse for KRA III |
|-----------|-------------------|
| Admin publish + version lock | **Yes** — already has `kra3-*` criteria rows |
| `Kra2SubmitReadiness` pattern | Adapt to `Kra3SubmitReadiness` |
| Multi-slot checklist API | Copy `kra2_c_evidence_slots.py` pattern → `kra3_evidence_slots.py` |
| OCR merge + faculty confirm | Same `merge_ocr_into_bundle` discipline |
| Rank sim caps | Already `published_kra_max_points('kra3')` |

**Not reusable without extension:** KRA II indicator registry (`kra2_indicators.json`) — KRA III needs parallel `kra3_indicators.json` + registry.
