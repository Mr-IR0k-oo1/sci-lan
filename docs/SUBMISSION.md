# GridFlex — Hackathon Submission

## Problem Statement

### Why This Matters

Electrical power grids worldwide are undergoing a rapid and complex transformation. Renewable energy sources — solar, wind, and battery storage — are being integrated at unprecedented scale. Unlike conventional generation, renewables are intermittent, distributed, and can fundamentally alter the voltage profile and power flow distribution across a transmission network.

Engineers responsible for grid planning face a core challenge: **they cannot safely add renewable capacity without understanding the downstream effects on voltage stability, line loading, and overall grid health.** Today this analysis is done with expensive commercial software (PSS/E, PowerWorld), static offline studies, and manual iteration — a process that is slow, inaccessible, and poorly suited to interactive decision-making.

### Target Users

- Power system engineers evaluating renewable integration scenarios
- Grid planning teams performing what-if analysis
- Engineering educators demonstrating power flow concepts
- Researchers prototyping grid stability algorithms

### Existing Challenge

Commercial power flow tools cost tens of thousands of dollars per license, require weeks of training, and produce static reports rather than interactive decision-support workflows. Open-source alternatives (pandapower, MATPOWER) are powerful but require programming knowledge and lack interactive interfaces.

---

## GridFlex Solution

GridFlex is an **interactive renewable energy integration and grid stability planning tool** that combines:

- A **visual grid editor** for building and modifying electrical network models
- A **real AC power flow solver** using Newton-Raphson in polar form (no approximations)
- A **scenario engine** for renewable integration and what-if analysis
- An **automated stress analysis pipeline** that detects issues and generates explainable recommendations
- A **mitigation testing framework** that validates proposed interventions without modifying the base grid
- **Engineering case studies** that demonstrate specific grid stress conditions with real computations

---

## Technical Architecture

```
                    REACT FRONTEND
                           │
                           ▼
                        FASTAPI
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
      GRID MODEL       SCENARIOS       CASE STUDIES
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                   POWER FLOW ENGINE
                      │           │
                      ▼           ▼
                   PYTHON       SCILAB
                      │           │
                      └─────┬─────┘
                            ▼
                    NORMALIZED RESULTS
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
           STRESS       ISSUES      COMPARISON
              │
              ▼
       RECOMMENDATION ENGINE
              │
              ▼
       MITIGATION CANDIDATES
              │
              ▼
         TEMPORARY TEST
              │
              ▼
             REPORT
```

**Backend:** Python 3.12 + FastAPI + NumPy  
**Frontend:** React 19 + TypeScript + Vite  
**Computational:** Python Newton-Raphson solver + optional Scilab integration  
**Data:** JSON-based grid models and case studies; in-memory state for demo

---

## Role of Scilab

GridFlex implements a pluggable engine abstraction (`PowerFlowEngine` interface) that allows the same Newton-Raphson algorithm to be solved by either:

- **Python engine** (always available): pure NumPy implementation, Y-bus construction, full Jacobian-based Newton-Raphson, converges to 1e-6 pu tolerance
- **Scilab engine** (optional, requires installation): identical algorithm implemented in Scilab's matrix language via `power_flow.sci`, executed as a subprocess with structured I/O

The engine abstraction ensures:
1. Results are **normalized to the same schema** regardless of which engine solved the problem
2. The engine that actually ran is **always reported** — there is no silent fallback
3. Results can be **compared side-by-side** via `/api/v1/compare-engines`

---

## Engineering Methodology

### Power Flow

Newton-Raphson in polar form over the per-unit Y-bus. Standard H/N/J/L Jacobian partitioning. SLACK, PV, and PQ bus support. Non-convergence is returned as a structured failure state with `max_mismatch` and `iterations`, never as fake numbers.

### Stress Analysis

A multi-component stress score (0–100) combining:
- **Voltage stress** (40% weight): per-unit voltage deviation from nominal
- **Transmission stress** (35% weight): line loading as % of thermal limit
- **Generation balance** (15% weight): slack bus reliance, generator limits
- **Renewable impact** (10% weight): penetration percentage and violation changes

All weights and thresholds are configurable in `backend/app/config/thresholds.py`.

### Recommendations

Rules-based recommendation engine (`recommendation_rules.py`) maps detected issues to actionable engineering interventions with:
- Priority (HIGH/MEDIUM/LOW)
- Confidence level (HIGH/MEDIUM/LOW)
- Specific suggested actions
- Expected effect descriptions
- Links to the triggering issues

### Mitigation Testing

Proposed mitigations are applied as temporary grid modifications, a full stress analysis is re-run, and results are compared against the baseline. The `before_score` and `after_score` are always reported honestly — no fabrication if a mitigation doesn't help.

### Reproducibility

Every analysis is hashed with SHA-256 over the grid topology + scenario parameters + engine choice. The `input_hash` is stored in the `AnalysisRun` audit record and returned in every `PowerFlowResult`, ensuring identical inputs always produce identical outputs.

---

## Case Studies

| ID | Name | Scenario | Demonstrates |
|----|------|----------|--------------|
| `normal_operation` | Normal Grid Operation | Balanced base load | Healthy grid baseline |
| `over_voltage` | Over Voltage Condition | 200 MW solar spike | Voltage stress detection |
| `line_overload` | Line Overload | 150% load scaling | Transmission stress detection |
| `renewable_integration` | Renewable Integration | Gradual solar ramp | Penetration impact analysis |
| `battery_support` | Battery Storage Support | Battery discharge scenario | Storage as mitigation |

All case studies use real grid data and real computations. No prerecorded results.

---

## Innovation

1. **Full-stack engineering tool in a hackathon timeframe** — a working power flow solver, stress analysis engine, recommendation system, and interactive frontend, all integrated and tested
2. **Pluggable computational engines** — the same interface works for Python and Scilab, with honest fallback reporting
3. **Explainable AI-free recommendations** — purely rules-based, auditable, and deterministic
4. **Reproducible analysis** — SHA-256 input hashing means any result can be re-derived
5. **Demo reset** — deterministic state restoration for repeatable presentations

---

## Current Limitations

- In-memory persistence only (restart loses grids/analyses)
- No PV bus reactive-power limit enforcement
- Scilab engine untested against real Scilab installation (Python engine fully tested)
- Single-instant power flow only (no time-series or 24-hour dispatch)
- No transformer tap-changer modeling
- N-1 contingency analysis not implemented

---

## Future Scope

1. Persistent database (PostgreSQL) for grid versioning and audit trails
2. Enforce generator Q-limits with PV→PQ bus switching
3. Time-series renewable profiles (24-hour dispatch)
4. Optimal power flow for capacity/placement recommendations
5. N-1 contingency screening
6. WebSocket streaming for real-time solver progress
