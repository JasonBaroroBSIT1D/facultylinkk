# KRA II Faculty Mobile — UI/UX & Performance Report

**Date:** 2026-11-03  
**Scope:** KRA II mobile only (Criteria A, B, C).

## 1. Root cause of slow loading

| Bottleneck | Evidence | Impact |
|---|---|---|
| **Full-screen gate on criterion hub** | `Kra2CriterionHubScreen` set `_loading = true` until **both** `fetchKra2Summary` and `fetchKra2Accomplishments` finished sequentially | User saw only a spinner when opening A/B/C; no local catalog UI |
| **Blocking OCR poll on review step** | `Kra2ReviewSubmitScreen` awaited `pollDocumentAfterUpload` (up to 24×3s) **before** showing fields; poll also refreshed teaching + rank simulation | Step 3 could block tens of seconds after upload |
| **Catalog loaded per-screen** | Each screen called `ensureLoaded()` on first open without app-wide preload | Extra asset parse on first KRA II entry (minor vs network) |
| **Duplicate criterion API calls** | New `ApiClient()` per hub refresh; no in-flight deduplication | Repeated navigation could stack identical requests |

Backend slowness could add latency, but the **UI blocked on nonessential data** even when the local `kra2_indicators.json` was available.

## 2. Files modified / added

| Path | Change |
|---|---|
| `lib/main.dart` | Preload `Kra2Catalog` at startup |
| `lib/data/kra2_catalog.dart` | Groups, hub copy, preload, criterion C user-facing label |
| `lib/data/kra2_criterion_remote.dart` | **New** — parallel fetch, cache, dedupe |
| `lib/data/app_state.dart` | Invalidate remote cache on logout; `pollKra2OcrInBackground`; optional side effects on OCR poll |
| `lib/data/kra2_a_ux.dart` | Friendlier blockers / OCR copy |
| `lib/screens/kra2/kra2_main_hub_screen.dart` | Redesigned main hub |
| `lib/screens/kra2/kra2_criterion_hub_screen.dart` | Immediate groups + async submissions |
| `lib/screens/kra2/kra2_wizard_screen.dart` | Authorship step, upload UX |
| `lib/screens/kra2/kra2_review_submit_screen.dart` | Non-blocking OCR; review copy |
| `lib/screens/kra2/kra2_hub_widgets.dart` | **New** shared cards / retry UI |
| `test/kra2_groups_test.dart` | **New** |
| `test/kra2_hub_navigation_test.dart` | **New** |

## 3. UI improvements

- Main hub: welcoming header, “Choose → Upload → Review”, three large criterion cards with icons.
- Criterion screens: accomplishment types from local catalog immediately; submissions/progress load in background.
- Wizard: plain-language authorship question when sole/co exists; large upload target; step copy aligned to spec.
- Review: “Check your information” header; OCR runs in background while fields are editable.
- Errors: retry bars and humanized messages (no raw exception strings).

**Criterion C label:** UI uses “Creative Works & Research Impact” while official catalog/PDF still maps indicators under `kra2-c` (including creative works per annex). Citation (`kra2-a-cite`) remains under **Criterion A** — not moved.

## 4. Performance optimizations

- Single catalog parse + in-memory reuse (`preload` / `ensureLoaded`).
- Criterion summary + accomplishments fetched in **parallel** with cache and in-flight dedupe.
- No full-screen spinner for catalog; inline spinner only for submissions section.
- Review screen shows bundle first; OCR polls in background without teaching/simulation refresh on each poll.

## 5. Loading measurements (Flutter test host, not Android device)

| Navigation | Before (observed behavior) | After (widget test Stopwatch) |
|---|---|---|
| Main hub first paint | Immediate but plain | **&lt; 500 ms**, no spinner |
| Criterion A hub accomplishment list | Blocked until API | **&lt; 500 ms** for “Journal article”, “Book”, etc. |

**NOT measured on physical Android device** in this session.

## 6. Tests executed

| Command | Result |
|---|---|
| `flutter test test/kra2_a_ux_test.dart test/kra2_a_evidence_test.dart test/kra2_catalog_test.dart test/kra2_groups_test.dart test/kra2_hub_navigation_test.dart` | **11 passed** |
| `flutter analyze` (KRA II paths) | **No issues** |
| `flutter analyze lib/screens/kra2 lib/data/kra2_catalog.dart lib/data/kra2_criterion_remote.dart` | Run in CI session |

Upload / Save Draft / Submit / OCR / slow backend: **NOT TESTED** on device or live API in this session.

## 7. Remaining issues

- Live backend timeout behavior depends on network; retry UX added but not soak-tested.
- Very long OCR runs still poll in background (user can submit manually when validation allows).
- Patent-stage groups show three separate cards (official mapping preserved).

## 8. Requires Android device testing

- Cold/warm app launch to KRA II main hub.
- Criterion B/C accomplishment list scroll on small screen (no overflow).
- PDF pick + upload + OCR on real device.
- Save Draft / Submit for Review against staging backend.
- Text scaling / accessibility (large fonts).

## Stop boundary

KRA II Faculty Mobile UI/UX and performance only. No scoring, backend formula, or KRA III/IV changes.
