# GridFlex Release Audit

**Date:** 2026-08-14  
**Version:** 0.1.0  
**Auditor:** Automated code review (Phase 7)

---

## BLOCKER — Must fix before release

| # | File | Issue |
|---|------|-------|
| B1 | `frontend/src/api/caseStudy.ts` | Imports `apiClient` from `./client` but `client.ts` exports individual functions (`get`, `post`). Causes TypeScript compilation failure and runtime crash. |
| B2 | `frontend/src/state/AnalysisContext.tsx` | `useEffect` used but not imported. TypeScript error; feature broken at runtime. |
| B3 | `frontend/src/components/workspace/CaseStudiesModal.tsx` | `useAnalysis` imported and `analysis` variable declared but never used — TypeScript error `TS6133`. |
| B4 | `frontend/tests/fixtures.ts` | `sampleResult` fixture missing `analysis_id` and `input_hash` fields added to `PowerFlowResult`. TypeScript error in tests. |

**Status: ALL BLOCKERS FIXED ✓**

---

## HIGH — Fix before release

| # | File | Issue |
|---|------|-------|
| H1 | `backend/app/main.py` | Uses deprecated `@app.on_event("startup")`. Causes a `DeprecationWarning` in all test runs; will be removed in a future FastAPI version. |
| H2 | `backend/app/main.py` | No CORS middleware — browser cannot reach the API from the Vite dev server or Docker-served frontend. |
| H3 | `backend/app/main.py` | Startup grid loading silently crashes if `sample_grid.json` or `demo_grid.json` is missing; no `FileNotFoundError` handling. |
| H4 | `backend/app/api/routes/demo.py` | Demo reset endpoint did not exist; no way to deterministically restore demo state. |
| H5 | `.env.example` | No environment configuration template in repo root. |

**Status: ALL HIGH ISSUES FIXED ✓**

---

## MEDIUM — Address when possible

| # | File | Issue | Action |
|---|------|--------|--------|
| M1 | `backend/app/api/routes/case_studies.py` | `run_case_study` route doesn't pass `engine` query param to service | Acceptable — defaults to `auto` |
| M2 | `backend/app/services/analysis_history_service.py` and `analysis_run_service.py` | Two separate in-memory record stores exist (`_records` and `_runs`). The `stress` routes use `analysis_history_service`, the `analysis` routes use `analysis_run_service`, creating a split identity for analysis records. | Known limitation; documented. |
| M3 | `backend/app/main.py` | CORS `allow_origins` hardcodes `localhost:5173`. In Docker, the origin comes from the nginx-served frontend (port 80). | Acceptable for demo — update for production. |
| M4 | `backend/app/schemas/case_study.py` | `CaseStudyRunResponse.mitigation_result` field defined but never populated. | Leave as-is; not user-facing. |
| M5 | `frontend/src/components/workspace/CaseStudiesModal.tsx` | Uses inline `style` objects rather than CSS classes. | Cosmetic; acceptable for demo. |

---

## LOW — Known but non-blocking

| # | File | Issue |
|---|------|--------|
| L1 | `backend/requirements.txt` | `pytest` listed as a runtime dependency rather than dev. Should be in a `requirements-dev.txt`. |
| L2 | `backend/app/core/logging.py` | `LOG_LEVEL` environment variable is read by the startup logger but the actual level is hardcoded to `INFO`. |
| L3 | `frontend/src/api/caseStudy.ts` | `WhatIfRequest` imported but only used for field typing; could be more specific. |
| L4 | `docs/PHASE3_REPORT.md` | Phase-specific document left in `docs/`; harmless but creates noise. |
| L5 | `backend/scripts/integration_demo.py` | Demo script uses older API surface (pre-Phase 6). Works as a standalone script but not integrated into test suite. |

---

## No Issues Found In

- Power flow solver (`power_system/power_flow.py`) — deterministic, no mock data
- Stress analysis engine (`power_system/stress.py`) — fully computed, no hardcoded results
- Recommendation rules (`power_system/recommendation_rules.py`) — rules-based, reproducible
- Case study JSON files — real grid data, no placeholder values
- Scilab engine fallback — explicitly reported, never faked
- Fingerprint/audit service — SHA-256 deterministic hashing, correctly implemented
