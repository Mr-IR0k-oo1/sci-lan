# Stress Analysis

The Stress Analysis subsystem takes a solved power-flow result and converts it
into a single, transparent grid-health assessment: per-domain stress scores, a
weighted overall score with a classification band, and a unified list of
`StressIssue`s. It is the analytical backbone for the Recommendation Engine and
Mitigation Comparison features.

## Pipeline

```
PowerFlowResult -> Constraint Analysis -> Stress Detection
    -> Issue Classification -> Stress Score
```

Each stage lives in `backend/app/power_system/`:

| Module | Responsibility |
| --- | --- |
| `voltage_analysis.py` | `analyze_voltage_stress` — per-bus voltage bands and severity |
| `line_analysis.py` | `analyze_line_stress` — per-line loading bands and severity |
| `generation_analysis.py` | `analyze_generation_balance` — slack/reserve/limit detections |
| `stress.py` | composition: renewable impact, issue classification, score, `build_stress_analysis` |

`build_stress_analysis(...)` composes everything into a
`StressAnalysisResult` and is the single entry point used by the service, the
comparative analysis, and mitigation tests (see below).

## Stress score

`compute_stress_score` produces a `StressScore` with four `StressComponentScore`s:

- **Voltage** — worst bus severity points + a capped extra per additional
  affected bus.
- **Transmission** — worst line severity points + a capped extra per additional
  affected line.
- **Generation** — fixed points per detection
  (`GENERATION_INSUFFICIENT`/`EXCESS_GENERATION` → 70, `IMBALANCED_SYSTEM` → 60,
  `GENERATOR_AT_LIMIT` → 40 + 10 × count, capped at 70).
- **Renewable Impact** — `POSITIVE` → 10, `NEUTRAL` → 0, `NEGATIVE` → 60,
  `HIGH_RISK` → 100.

The overall score is the weighted sum of the component scores using
`StressThresholds.score_weights`. The classification bands are:

| Score range | Classification |
| --- | --- |
| `< low_score_max` (20) | LOW |
| `< moderate_score_max` (50) | MODERATE |
| `< high_score_max` (75) | HIGH |
| otherwise | CRITICAL |

Thresholds live in `backend/app/config/thresholds.py` (`StressThresholds`,
default instance `stress_thresholds`). Every threshold is injectable, so tests
and callers can tune sensitivity without touching the scoring logic.

## Issues

`_build_issues` converts severity-flagged components and generation detections
into a unified `StressIssue` list. Titles are exact and drive both the
recommendation rules and the frontend (do not rename):

- `Bus overvoltage` / `Bus undervoltage` (VOLTAGE_STRESS)
- `Transmission line overloaded` / `Transmission line loading warning` (TRANSMISSION_STRESS)
- `Generation may be insufficient`, `Excess generation detected`,
  `Generation imbalance`, `Generator operating at limit` (GENERATION_BALANCE)
- `Renewable integration impact` (RENEWABLE_IMPACT)

Each issue carries `evidence` (numbers, thresholds) so the UI can render detail
without re-deriving it.

## Renewable impact

`analyze_renewable_impact` evaluates how renewable generation interacts with the
grid. In a standalone run it classifies based on penetration plus whether
voltage/line violations coexist (`POSITIVE` / `NEUTRAL` / `NEGATIVE` /
`HIGH_RISK`). When a `baseline` `StressAnalysisResult` is provided, it instead
compares violation **fingerprints** (`category:component_type:component`) between
the baseline and the current run to report `new_violations` and
`resolved_violations` and picks the level accordingly.

## Service + API

- `backend/app/services/stress_analysis_service.py` orchestrates the full
  record lifecycle: power flow → persist `AnalysisRecord` → stress → rules →
  mitigation candidates (see `RECOMMENDATION_ENGINE.md`).
- `backend/app/api/routes/stress.py` exposes the routes under `/api/v1`:

  | Method / path | Purpose |
  | --- | --- |
  | `POST /grids/{grid_id}/stress` | run a full stress analysis and persist an `AnalysisRecord` |
  | `POST /stress/comparative` | re-run with a renewable-impact baseline (`analysis_id` in body) |
  | `GET /analyses/{analysis_id}/stress` | fetch a persisted stress record |
  | `GET /analyses/{analysis_id}/mitigation-candidates` | list candidates |
  | `POST /analyses/{analysis_id}/mitigation-tests` | run mitigation tests (`run_all` or `mitigation_id`) |

## Frontend

`frontend/src/components/workspace/StressResultsPanel.tsx` hosts four tabs:
**Grid Health**, **Issues**, **Recommendations**, **Mitigations**. The `Stress`
button in the top bar triggers `POST /grids/{grid_id}/stress` through
`src/api/stress.ts`; results live in the `StressProvider`
(`src/state/StressContext.tsx`). Types are in `src/types.ts`, label/class
helpers in `src/lib/stress.ts`.

## Verification

- Backend: `python -m pytest tests -q` from `backend/` (60 tests), including
  `tests/test_stress.py` (7 tests).
- Frontend: `npm test`, `npm run typecheck`, `npm run build` from `frontend/`
  (41 tests), including `tests/stress.test.tsx` (6 tests).
- End-to-end: `python -m scripts.integration_demo` from `backend/` exercises
  stress → recommendations → mitigations → comparative against the TestClient.
