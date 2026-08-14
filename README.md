# GridFlex

**Interactive Renewable Energy Integration and Grid Stability Planning Tool**

---

## Problem

Integrating renewable energy into electrical grids changes voltage profiles and power flow distribution in ways that are difficult to predict without computational tools. Engineers need to answer:

- Will this solar farm push voltages outside safe limits?
- Will this load growth overload transmission lines?
- Which mitigation intervention will actually help?

Commercial tools (PSS/E, PowerWorld) cost tens of thousands of dollars per license and produce static reports. GridFlex provides an interactive, open-source alternative for learning, planning, and demonstration.

---

## Solution

GridFlex combines a visual grid editor with a real AC power flow solver, automated stress analysis, explainable recommendations, and mitigation testing — all in a single interactive tool.

**No hardcoded results. No fake timers. Every result is computed.**

---

## Key Features

- 🔌 **Visual grid editor** — build buses, lines, generators, and loads interactively
- ⚡ **AC power flow** — Newton-Raphson in polar form over the per-unit Y-bus
- 🌞 **Renewable integration** — model solar, wind, and battery storage
- 🎭 **Scenario analysis** — what-if modifications without mutating the base grid
- 📊 **Grid stress score** — multi-component 0–100 score with explanations
- 🔍 **Issue detection** — voltage violations, line overloads, generation imbalance
- 💡 **Explainable recommendations** — rules-based, priority-ranked, auditable
- 🛠️ **Mitigation testing** — test interventions before committing
- 📚 **Engineering case studies** — five predefined scenarios, all computed live
- 📄 **Engineering reports** — JSON, CSV, and Markdown export
- 🔄 **Reproducible analysis** — SHA-256 input hashing for audit trails
- 🔀 **Dual engine support** — Python (always available) + Scilab (optional)

---

## Architecture

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

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite |
| Backend | Python 3.12, FastAPI, Uvicorn |
| Solver | NumPy (Python engine), Scilab (optional) |
| Validation | Pydantic v2 |
| Testing | pytest, Vitest, @testing-library/react |
| Container | Docker, docker-compose, nginx |

---

## Computational Engines

### Python Engine (default)

Pure-Python Newton-Raphson AC power flow using NumPy.

- Y-bus construction with susceptance shunts
- Full H/N/J/L Jacobian, solved with `numpy.linalg.solve`
- SLACK, PV, PQ bus support
- Default tolerance: 1e-6 pu, max iterations: 20
- Always available — no external dependencies

### Scilab Engine (optional)

The same Newton-Raphson algorithm implemented in Scilab (`backend/app/scilab/scripts/power_flow.sci`), executed as a subprocess via `scilab-cli`.

- Detected automatically at startup
- Reported honestly in `/api/v1/engines` — never faked
- Falls back to Python when unavailable (engine shown in UI)
- Results normalized to the same schema as Python

---

## How It Works

```
Grid
  ↓ (create / edit buses, lines, generators, loads)
Power Flow
  ↓ (Newton-Raphson AC solver, convergence check)
Scenario
  ↓ (apply renewable output / load overrides — non-destructive)
Stress Analysis
  ↓ (voltage, transmission, generation, renewable impact scores)
Recommendations
  ↓ (rules-based, priority-ranked, linked to issues)
Mitigation Testing
  ↓ (run temporary modification, compare before/after)
Report
  ↓ (JSON / CSV / Markdown export)
```

---

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend starts at `http://localhost:8000`. Interactive API docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend starts at `http://localhost:5173`. The Vite dev server proxies `/api` to the backend.

### Environment Configuration

```bash
cp .env.example .env
# Edit .env as needed
```

See `.env.example` for all available variables.

---

## Docker Setup

```bash
# Build and run both services
docker-compose up --build

# Frontend:  http://localhost:80
# Backend:   http://localhost:8000
# API docs:  http://localhost:8000/docs
```

> **Note:** Scilab is not included in the Docker images. The Python engine is always available. See [Scilab Setup](#scilab-setup) for optional Scilab support.

---

## Scilab Setup

Scilab is entirely optional. The Python engine provides identical results.

To enable Scilab:

1. Install Scilab: https://www.scilab.org/download/scilab-2024
2. Verify: `scilab-cli -version`
3. Set env var (optional, if not on PATH):

```bash
export GRIDFLEX_SCILAB_EXECUTABLE=/usr/bin/scilab-cli
```

4. Restart the backend. `GET /api/v1/engines` will report `scilab.available: true`.

---

## Case Studies

Five predefined engineering scenarios, all computed live:

| ID | Scenario | Demonstrates |
|----|----------|-------------|
| `normal_operation` | Balanced base load | Healthy grid baseline |
| `over_voltage` | 200 MW solar spike | Voltage stress (>1.05 pu) |
| `line_overload` | 150% load scaling | Transmission overload (>100%) |
| `renewable_integration` | Gradual solar ramp | Penetration impact |
| `battery_support` | Battery discharge | Storage as mitigation |

Access via the **Case Studies** button in the top bar, or:

```bash
curl -X POST http://localhost:8000/api/v1/case-studies/over_voltage/run
```

---

## Demo

**Duration:** 4–6 minutes. See [`docs/DEMO_FALLBACK.md`](docs/DEMO_FALLBACK.md) for the fallback plan.

**Reset demo state before each session:**
```bash
curl -X POST http://localhost:8000/api/v1/demo/reset
```

**Flow:**

1. Load the Renewable Integration case study
2. Run base grid analysis → show normal state
3. Increase solar generation → run scenario
4. Show voltage impact in the results panel
5. Open stress analysis → show issue evidence
6. Show explainable recommendation
7. Test a mitigation → show before/after comparison
8. Generate engineering report

---

## API Documentation

Interactive OpenAPI docs: `http://localhost:8000/docs`

Full API contract: [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md)

Key endpoints:

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/health` | System health + engine availability |
| `GET` | `/api/v1/grids` | List grids |
| `POST` | `/api/v1/grids` | Create grid |
| `POST` | `/api/v1/grids/{id}/validate` | Validate topology |
| `POST` | `/api/v1/grids/{id}/analyze/power-flow` | Run power flow |
| `POST` | `/api/v1/grids/{id}/what-if` | Renewable scenario (non-destructive) |
| `POST` | `/api/v1/grids/{id}/stress` | Full stress analysis |
| `POST` | `/api/v1/analyses/{id}/mitigation-tests` | Test mitigations |
| `GET` | `/api/v1/case-studies` | List case studies |
| `POST` | `/api/v1/case-studies/{id}/run` | Execute case study |
| `POST` | `/api/v1/demo/reset` | Reset demo state |

---

## Testing

```bash
# Backend tests (66 tests)
cd backend && python -m pytest tests/ -v

# E2E tests (6 tests)
cd backend && python -m pytest tests/test_e2e.py -v

# Frontend tests (41 tests across 8 suites)
cd frontend && npm test

# Frontend typecheck
cd frontend && npm run typecheck

# Release verification (requires running backend)
python scripts/verify_release.py
```

See [`docs/TEST_RESULTS.md`](docs/TEST_RESULTS.md) for full results.

---

## Limitations

- **In-memory persistence** — data is lost on server restart (acceptable for demo)
- **No PV reactive-power limit enforcement** — PV buses do not switch to PQ when Q limits are hit
- **Single-instant analysis** — no time-series or 24-hour dispatch profiles
- **No transformer modeling** — all lines are simple Pi-model branches
- **N-1 contingency not implemented** — single operating point analysis only
- **Scilab untested against real installation** — Python engine is fully validated

See [`docs/SUBMISSION.md`](docs/SUBMISSION.md) for full future scope.

---

## Project Structure

```
sci/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app, CORS, lifespan
│   │   ├── api/routes/                # HTTP endpoints
│   │   │   ├── grid.py                # Grid CRUD
│   │   │   ├── analysis.py            # Power flow + engine status
│   │   │   ├── scenarios.py           # Scenario management
│   │   │   ├── stress.py              # Stress analysis + mitigations
│   │   │   ├── case_studies.py        # Case study execution
│   │   │   ├── health.py              # Health check
│   │   │   └── demo.py                # Demo reset
│   │   ├── domain/                    # Bus, Generator, Load, GridModel
│   │   ├── power_system/              # Newton-Raphson, Y-bus, stress
│   │   ├── scilab/                    # Scilab runner + scripts
│   │   ├── services/                  # Business logic
│   │   ├── schemas/                   # Pydantic DTOs
│   │   ├── config/                    # Thresholds
│   │   └── core/                      # Config, exceptions, logging
│   ├── examples/
│   │   ├── sample_grid.json           # 5-bus sample network
│   │   ├── demo_grid.json             # Wind + battery demo network
│   │   └── case_studies/              # 5 case study directories
│   ├── tests/                         # 66 pytest tests
│   ├── scripts/                       # generate_case_studies.py, smoke_test.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/                       # HTTP clients
│   │   ├── components/workspace/      # UI panels and canvas
│   │   ├── state/                     # React context providers
│   │   ├── lib/                       # Utilities
│   │   └── types.ts                   # Shared TypeScript types
│   └── tests/                         # 41 Vitest tests
├── docs/
│   ├── API_CONTRACT.md
│   ├── RELEASE_AUDIT.md
│   ├── DEMO_FALLBACK.md
│   ├── TEST_RESULTS.md
│   └── SUBMISSION.md
├── scripts/
│   └── verify_release.py              # Release verification
├── Dockerfile.backend
├── Dockerfile.frontend
├── docker-compose.yml
├── nginx.conf
└── .env.example
```
