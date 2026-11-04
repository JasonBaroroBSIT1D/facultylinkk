# KRA III scoring verification (implementation)

| Rule | Implementation | Test |
|------|----------------|------|
| CSR `(R/100)×20` | `estimated_points_for_bundle` | PASS |
| Train local/intl per hour | `base × deliveryHours` | PASS |
| Criterion caps A30 B50 C20 D20 bonus | `published_kra3_criterion_max_points` | Catalog + admin |
| KRA max 100 (ABC + bonus) | `aggregate_kra3_kra_from_documents` | Smoke PASS |
| Income lead/co separate indicators | Catalog IDs; no bracket stacking | Manual |
| Host ≥ 6 months | `validation.py` blocker | NOT TESTED E2E |
| Group caps (column, guest, ISR) | `group_caps.py` | NOT TESTED matrix |
| Criterion D points | Catalog fallback; **UNVERIFIED** vs Annex D table | BLOCKED |
