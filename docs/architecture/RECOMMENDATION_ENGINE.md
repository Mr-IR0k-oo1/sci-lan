# Recommendation Engine

The Recommendation Engine turns detected stress into prioritized, actionable
mitigations. It has two layers: a rule set that produces `Recommendation`s from
stress issues, and a candidate builder that turns the highest-value
recommendations into concrete, re-runnable mitigation scenarios with a
before/after comparison.

## Recommendations

`backend/app/power_system/recommendation_rules.py` evaluates a set of rules
against one or more `StressAnalysisResult`s (the engine accepts a list, which is
how the comparative analysis can surface renewable-impact recommendations).

### Rule model

`RecommendationRule` derives `priority` and `confidence` from a severity:

| Severity | Priority | Confidence |
| --- | --- | --- |
| CRITICAL | HIGH | HIGH |
| WARNING | MEDIUM | MEDIUM |
| NORMAL | LOW | LOW |

Rules are additive (not exclusive): one condition can produce several
recommendations (e.g. `Bus undervoltage` at three buses). Output is sorted
HIGH → MEDIUM → LOW, stable by `rec.id` within a tier.

### Rules

| Category | Recommendation | Triggers on |
| --- | --- | --- |
| voltage | Reduce reactive injection near high-voltage buses | `Bus overvoltage` |
| voltage | Add shunt compensation to support voltage | `Bus undervoltage` |
| transmission | Reduce load on overloaded transmission lines | `Transmission line overloaded` |
| transmission | Monitor transmission lines approaching limits | `Transmission line loading warning` (only when no overload) |
| generation | Increase generation capacity | `GENERATION_INSUFFICIENT` |
| generation | Curtail excess generation | `EXCESS_GENERATION` |
| generation | Redistribute generation across the system | `IMBALANCED_SYSTEM` |
| generation | Review generator operating limits | `GENERATOR_AT_LIMIT` |
| renewable | Add storage or stability controls | renewable impact `NEGATIVE` / `HIGH_RISK` |

Recommendations reference the issues that triggered them via
`related_issue_ids`, carry `suggested_actions` and `expected_effect`, and match
the canonical `Recommendation` model in
`backend/app/domain/recommendation_models.py`. **Issue titles are matched
exactly** — renaming an issue title in `stress.py` breaks the rule wiring.

## Mitigation candidates

`build_mitigation_candidates(record)` converts overvoltage and overloaded-line
issues into concrete `MitigationCandidate`s:

- **Overvoltage** — reduce the reactive-power output of the generator at the
  affected bus (`GENERATOR_SHUNT_REACTIVE`); falls back to halving the largest
  load at that bus (`LOAD_CURTAILMENT`).
- **Overloaded line** — halve the largest load at the line's `to_bus`
  (`LOAD_CURTAILMENT`).

Each candidate is a small list of `MitigationModification`s applied to a **deep
copy** of the grid.

## Mitigation tests

`run_mitigation_test` applies a candidate's modifications and re-runs the power
flow (`power_flow_service.run_power_flow`):

- If the modified case does not converge, it returns a `converged: false` result.
- Otherwise it re-runs `build_stress_analysis` with the original stress as the
  `baseline` (so renewable impact is classified comparatively) and reports:
  - `before_score` / `after_score` with classifications;
  - `resolved_issues`, `remaining_issues`, `new_issues` computed by
    title+component fingerprint comparison;
  - `metric_changes` — stress score, total losses (MW), min voltage (pu),
    max loading (%).

`run_mitigation_tests(record)` runs every candidate; the API accepts
`run_all: true` or a single `mitigation_id`
(`POST /api/v1/analyses/{analysis_id}/mitigation-tests`).

## Service orchestration

`backend/app/services/stress_analysis_service.py`:

```
grid -> power flow -> AnalysisRecord
    -> stress analysis (voltage, line, generation, renewable)
    -> recommendations (evaluate_rules)
    -> mitigation candidates -> mitigation tests (re-run power flow)
```

`run_comparative_analysis` runs a full analysis again with the original record
as `grid_id` source, letting the renewable-impact classifier compare violation
sets.

## Frontend

- `RecommendationsPanel` (`src/components/workspace/stress/RecommendationsPanel.tsx`)
  renders priority/confidence badges, suggested actions, and expected effect.
- `MitigationPanel` renders candidate lists, a "Test all" action, and a
  before/after `data-table` per tested candidate (resolved/remaining/new issues
  are summarized as colored outcome lines).

## Verification

- `tests/test_stress.py` (`test_stress_recommendations_follow_issues`,
  `test_mitigation_candidates_and_tests`) covers rule→issue linkage and the
  candidate/test lifecycle.
- `frontend/tests/stress.test.tsx` covers recommendations and mitigation
  rendering, including the run-all flow and the empty-candidates hint.
