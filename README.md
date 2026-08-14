# GridFlex

Interactive Renewable Energy Integration and Grid Stability Planning Tool.

Phase 1 backend: a foundational FastAPI service for representing and analyzing a
small electrical power grid — bus/line/generator/load modeling, topology
validation, Y-bus construction, an AC Newton-Raphson power-flow solver, and a
pluggable computation-engine abstraction with Scilab support.

The frontend lives separately and is **not** part of this backend repository.

## Purpose

Model a small transmission/distribution network and answer:

- Is my network topologically valid?
- What are the steady-state voltages at each bus?
- How much power flows over each line and how loaded is it?
- What does each generator (including solar/wind) contribute?

Phase 1 intentionally excludes optimization and recommendation engines.

## Architecture

```
backend/
├── app/
│   ├── main.py                  # FastAPI app, routers, exception handlers
│   ├── api/routes/
│   │   ├── grid.py              # grid create/get/validate
│   │   └── analysis.py          # power flow + engine status
│   ├── domain/
│   │   ├── models.py            # Bus, TransmissionLine, Generator, Load, GridModel
│   │   └── enums.py             # BusType, GeneratorType, status enums
│   ├── schemas/                 # API request/response DTOs
│   ├── services/
│   │   ├── grid_service.py      # in-memory grid store
│   │   ├── validation_service.py# structured topology validation
│   │   └── power_flow_service.py# engine selection + result normalization
│   ├── power_system/
│   │   ├── per_unit.py          # MW <-> pu, kV <-> pu helpers
│   │   ├── ybus.py              # build_ybus
│   │   ├── power_flow.py        # Newton-Raphson AC power flow
│   │   ├── results.py           # bus/line/summary result building
│   │   └── engines.py           # PowerFlowEngine abstraction + registry
│   ├── scilab/
│   │   ├── runner.py            # availability detection + execution
│   │   └── scripts/power_flow.sci
│   └── core/                    # config, exceptions
├── examples/sample_grid.json    # 5-bus sample network
└── tests/                       # pytest suite
```

### Engine abstraction

The API never depends on a concrete solver. `PowerFlowEngine` defines
`info()` and `run()`; `PythonPowerFlowEngine` (default, always available) and
`ScilabPowerFlowEngine` (available only when Scilab is installed) implement it.
The engine that actually executed an analysis is always reported in the
response — there is no silent fallback.

## Backend setup

Requires Python 3.12+.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Dependencies

- `fastapi` — HTTP framework
- `uvicorn` — ASGI server
- `pydantic` — domain models and schemas
- `numpy` — linear algebra for the power-flow solver
- `pytest` + `httpx` — tests

NumPy is the only computational dependency. SciPy is **not** required at
runtime (it was used only to independently cross-check the solver during
development).

## Run the FastAPI server

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

The sample grid is loaded into the in-memory store on startup as
`grid_id = "sample"`. Open `http://127.0.0.1:8000/docs` for the interactive UI.

## Run the tests

```bash
cd backend
python -m pytest
```

## Scilab integration status

- `GET /api/v1/engines` reports `scilab.available: true|false` plus version.
- The Python engine is complete and fully tested.
- The Scilab runner (`app/scilab/runner.py`) detects the executable, renders a
  Scilab input script from the grid, executes `scilab-cli -nb -e ...`, and
  parses the solver output.
- `app/scilab/scripts/power_flow.sci` implements the same Newton-Raphson
  algorithm in Scilab. It is **written but not executed/tested here** because
  Scilab is not installed in the development environment.
- If Scilab is unavailable, the engine reports `unavailable` and returns a
  clear `scilab_unavailable` error if selected — it never pretends to run.

Scilab workflow (on a machine with Scilab):

1. Confirm detection: `GET /api/v1/engines` shows `scilab: available`.
2. Run power flow with `{"engine": "scilab"}`.
3. The runner writes temporary `gridflex_inputs.sci` / `gridflex_main.sci`,
   executes the solver script, and reads `gridflex_output.txt`.

## Power flow

Newton-Raphson in polar form over the per-unit Y-bus. Supports SLACK, PV, and
PQ buses. Voltages initialized to specified values (slack/PV) or 1.0 pu (PQ);
angles start at 0. The Jacobian is built from the standard H/N/J/L submatrices
and solved with `numpy.linalg.solve`. Converges when the largest active/reactive
mismatch falls below `tolerance` (default 1e-6) or stops at
`max_iterations` (default 20).

- Non-convergence returns a **structured failure state**
  (`converged: false`, `status: "not_converged"`, empty results), never fake
  numbers.
- Line loading = `|S_from| · base_mva / thermal_limit`. Status thresholds:
  `< 80%` NORMAL, `80–100%` WARNING, `> 100%` OVERLOADED (configurable in
  `app/core/config.py`).
- Bus status is derived from the per-unit voltage band (0.95–1.05 NORMAL,
  0.90–1.10 WARNING, outside CRITICAL; configurable).
- Reactive limits of PV generators are **not enforced** in Phase 1.

## Sample API requests

```bash
# Engine status
curl http://127.0.0.1:8000/api/v1/engines

# Create a grid
curl -X POST http://127.0.0.1:8000/api/v1/grids \
  -H 'Content-Type: application/json' \
  -d @examples/sample_grid.json

# Get a grid
curl http://127.0.0.1:8000/api/v1/grids/sample

# Validate topology
curl -X POST http://127.0.0.1:8000/api/v1/grids/sample/validate

# Run power flow (python engine)
curl -X POST http://127.0.0.1:8000/api/v1/grids/sample/analyze/power-flow \
  -H 'Content-Type: application/json' -d '{}'

# Run power flow (scilab engine, if available)
curl -X POST http://127.0.0.1:8000/api/v1/grids/sample/analyze/power-flow \
  -H 'Content-Type: application/json' -d '{"engine": "scilab"}'
```

### Endpoints

| Method | Path | Purpose |
| ------ | ---- | ------- |
| POST   | `/api/v1/grids` | Create a grid (in-memory) |
| GET    | `/api/v1/grids/{grid_id}` | Retrieve a grid |
| POST   | `/api/v1/grids/{grid_id}/validate` | Validate topology |
| POST   | `/api/v1/grids/{grid_id}/analyze/power-flow` | Run AC power flow |
| GET    | `/api/v1/engines` | Engine availability and versions |

## Known limitations (Phase 1)

- In-memory persistence only (acceptable for the MVP).
- No PV reactive-power limit enforcement.
- Solar/wind generators are fixed active-power sources; no weather/forecasting.
- Line thermal limits treated as MVA ratings.
- The Scilab engine is untested against a real Scilab installation.
- Single slack bus and connected-network checks are enforced but the solver
  assumes the network is radial/balanced and small.

## Roadmap (suggested Phase 2)

1. Enforce generator reactive-power limits with a Q-limits loop.
2. Optimize the solver with NumPy vectorization for larger networks.
3. Add line/breaker contingencies and N-1 screening.
4. Renewable scenario sweeps (multi-scenario power flow).
5. Optimal power flow for capacity/placement recommendations.
6. Persistent storage and grid versioning.
