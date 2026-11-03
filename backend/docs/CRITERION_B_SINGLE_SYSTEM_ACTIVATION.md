# Criterion B — single system activation (facultylink + Flask :5000)

One PostgreSQL database (`facultylink`), one backend (`http://127.0.0.1:5000`), one current score everywhere when the adapter is enabled via **environment only**.

## What changes when you activate

| Surface | Adapter **OFF** (today) | Adapter **ON** (after env + restart) |
|---------|---------------------------|--------------------------------------|
| Accomplishment detail | Reviewer Assessed **14** | Same |
| KRA I / Criterion B | Preview **14** or **0** in total | **14** in Criterion B and KRA I |
| Rank simulation total | May show **0** from Criterion B | Includes **14** |
| Audit estimate **15** | Preserved in `scoringContext` | Unchanged |

Supporting documents never create separate scoring claims. Legacy rows without bundles may still use `verified_points` fallback when no bundle primary exists.

## Before activation

1. Confirm a restorable backup exists under `backend/backups/` (e.g. `facultylink_phase6b2_*.dump`).
2. Run preflight (read-only):

```powershell
cd backend
python scripts/criterion_b_activation_preflight.py
```

3. Run smoke tests (optional):

```powershell
python -m pytest tests/staging/ tests/documents/test_criterion_b_current_score_integration.py tests/faculty/test_rank_simulation_criterion_b_wiring.py -q
node ../web/tests/faculty-kra-criterion-b-integration.test.js
cd ../mobile && flutter test test/kra_staging_integration_display_test.dart
```

## Activation (requires your explicit approval)

**Do not commit `=1` to git unless policy allows.** Set on the machine that runs Flask:

1. Edit `backend/.env` (local only):

```env
# Criterion B: include reviewer-assessed / estimated current scores in KRA + rank simulation
CRITERION_B_SIMULATION_ADAPTER_ENABLED=1
```

2. **Restart** the Flask process on port **5000** (env is read at import time of `criterion_b_simulation_adapter`).

```powershell
cd backend
# Stop the running flask run / service, then:
python -m flask --app app run --port 5000
```

3. Verify adapter loaded:

```powershell
python -c "from dotenv import load_dotenv; load_dotenv(); import importlib; import documents.scoring.criterion_b_simulation_adapter as m; importlib.reload(m); print(m.CRITERION_B_SIMULATION_ADAPTER_ENABLED)"
```

Expect `True` only after `.env` contains `1` and a **fresh** Python process started.

## Post-activation verification (same system)

1. **API** (reviewer token):  
   `GET /api/reviewer/faculty/{facultyPublicId}/estimated-assessment`  
   → `estimatedAssessment.kraScores` → KRA I `estimatedPoints` **14**, `criteriaScores` → `kra1-b` **14**.

2. **Reviewer Web**: Assigned Faculty → Jason Baroro → KRA Scores → Criterion B **14**, KRA I **14/100** (if no other KRA I points).

3. **Faculty Mobile** (default `http://127.0.0.1:5000`): accomplishment **14 Reviewer Assessed**; KRA dashboard and rank simulation include **14**; no “preview” footnote on KRA I.

4. Hard refresh / restart app; scores must match API.

## Rollback

1. Set `CRITERION_B_SIMULATION_ADAPTER_ENABLED=0` or remove the line from `backend/.env`.
2. Restart Flask on port 5000.
3. KRA totals revert to pre-integration behavior (Criterion B preview-only); accomplishment scores in bundles are **not** deleted.

## Safety

- No schema migration required for this flag.
- No change to official scoring formulas (`criterion_b_scoring.py` caps and contribution rules unchanged).
- Reviewer assessment remains in `bundle.reviewerProposedAssessment`; not written to `verified_points`.
- SMTP unaffected.

## One current score rule

- **Display:** `scoringContext.displayScore` / `currentScore` — Estimated until completed reviewer assessment, then **Reviewer Assessed**.
- **KRA / simulation (adapter ON):** same numeric **current score** per primary accomplishment, aggregated with dedupe and **30** pt Criterion B cap.
