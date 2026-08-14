# GridFlex Demo Fallback Plan

This document ensures the demonstration can proceed under adverse conditions.

---

## Fallback 1 — Scilab Unavailable

**Trigger:** Scilab is not installed on the demo machine, or `scilab-cli` is not on `PATH`.

**Behavior (automatic):**
- The backend detects Scilab absence at startup via `GET /api/v1/engines`.
- Engine selection defaults to `"auto"`, which silently uses Python.
- `GET /api/v1/health` returns `"scilab_engine": false`.
- The `EngineStatus` badge in the top bar displays **Python computational engine active**.
- All analysis runs continue without user action; the demo is unaffected.

**Display during demo:**
> "GridFlex uses a pluggable engine architecture. Today we're running with the Python solver — the same Newton-Raphson algorithm that would be handed off to Scilab if installed. Results are identical."

**No demo script changes required.**

---

## Fallback 2 — Network / Backend Unreachable

**Trigger:** The backend server is not running, or the port is firewalled.

**Frontend behavior:**
- Every API call raises `ApiRequestError` with code `network_error`.
- The error surfaces in the top bar: *"Could not reach the GridFlex backend. Is the server running?"*

**Recovery steps (< 60 seconds):**
```bash
cd /path/to/sci/backend
uvicorn app.main:app --port 8000
```
Then reload the frontend tab. The demo grid auto-loads.

**If recovery is not possible:** Pivot to walking through the code and architecture. Show `backend/examples/case_studies/renewable_integration/` to demonstrate the real data format. Show `backend/app/power_system/power_flow.py` for the Newton-Raphson implementation.

---

## Fallback 3 — Primary Case Study Fails

**Trigger:** `POST /api/v1/case-studies/renewable_integration/run` returns `"status": "FAILED"`.

**Primary fallback case study:** `normal_operation`

```bash
curl -X POST http://localhost:8000/api/v1/case-studies/normal_operation/run
```

`normal_operation` runs on a pre-validated, balanced 5-bus grid with no expected violations. It should never fail.

**If `normal_operation` also fails:**
1. Reset demo state: `POST /api/v1/demo/reset`
2. Retry `normal_operation`.
3. If still failing, run `python scripts/verify_release.py` to identify the specific stage.

**Verified fallback case studies (in priority order):**
1. `normal_operation` — always converges, no violations
2. `over_voltage` — solar spike triggers voltage issue
3. `line_overload` — load scaling triggers transmission issue

---

## Fallback 4 — Mitigation Does Not Improve the Scenario

**Trigger:** A mitigation test returns `after_score >= before_score`.

**This is correct and expected behavior.** GridFlex does not fabricate improvements.

**Display during demo:**
> "This mitigation did not meaningfully reduce the stress score — GridFlex shows you the actual outcome. In practice this tells the engineer they need a different intervention, which is more valuable than false confidence."

Show the `before_score` and `after_score` values directly. Pivot to a different mitigation candidate if available, or show the recommendation text and discuss the engineering rationale.

**Never fabricate or hide the actual result.**

---

## Fallback 5 — Power Flow Does Not Converge

**Trigger:** An aggressive scenario (e.g., extreme renewable output) causes Newton-Raphson to fail convergence within `max_iterations`.

**Behavior:** Backend returns `409 power_flow_not_converged` with `max_mismatch` and `iterations`.

**Display during demo:**
> "Power flow diverged — this is the solver telling us the operating point is physically infeasible under these extreme conditions. The system returns a structured error, never fake numbers."

**Recovery:** Reduce the renewable output parameter and re-run. The `line_overload` case study uses `load_scale: 1.5` which is designed to converge but stress the system.

---

## Pre-Demo Checklist

Run this before each demo session:

- [ ] `python scripts/verify_release.py` — all checks green
- [ ] `POST /api/v1/demo/reset` — clean state
- [ ] Browser tab loaded at `http://localhost:5173`
- [ ] Grid auto-loaded (check Top Bar shows "GridFlex Demo Network")
- [ ] Engine status badge visible (Python or Scilab)
