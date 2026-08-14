# GridFlex API Contract

**Version:** 0.1.0  
**Base URL:** `http://localhost:8000/api/v1`  
**Content-Type:** `application/json`

All error responses follow the unified shape:
```json
{ "detail": { "code": "<string>", "message": "<string>" } }
```

---

## Health

### `GET /health`

Returns system health and engine availability.

**Response `200`:**
```json
{
  "status": "healthy",
  "python_engine": true,
  "scilab_engine": false
}
```

---

## Grids

### `GET /grids`
List all grids currently in memory.

**Response `200`:** `GridModel[]`

### `POST /grids`
Create a new grid.

**Request body:** `GridModel`  
**Response `201`:** `GridModel`

### `GET /grids/{grid_id}`
**Response `200`:** `GridModel`  
**Error `404`:** `grid_not_found`

### `PUT /grids/{grid_id}`
Update an existing grid.

**Request body:** `GridModel`  
**Response `200`:** `GridModel`

### `POST /grids/{grid_id}/validate`
Validate grid topology and parameters.

**Response `200`:**
```json
{
  "valid": true,
  "errors": []
}
```

---

## Analysis

### `POST /grids/{grid_id}/analyze/power-flow`
Run AC Newton-Raphson power flow.

**Request body:**
```json
{
  "engine": "auto | python | scilab",
  "tolerance": 1e-6,
  "max_iterations": 20
}
```
All fields optional.

**Response `200`:** `PowerFlowResult`
```json
{
  "grid_id": "string",
  "analysis_id": "string",
  "input_hash": "string (sha256)",
  "engine": "python",
  "engine_version": "string | null",
  "status": "success | not_converged",
  "converged": true,
  "iterations": 4,
  "max_mismatch": 1e-11,
  "execution_time_ms": 12.4,
  "buses": [ { "bus_id": "B1", "voltage_magnitude": 1.05, "voltage_angle": 0.0, "active_power": 60.0, "reactive_power": 20.0, "status": "NORMAL | WARNING | CRITICAL" } ],
  "lines": [ { "line_id": "L1", "from_bus": "B1", "to_bus": "B2", "active_power_from": 30.0, "reactive_power_from": 10.0, "active_power_to": -29.5, "reactive_power_to": -9.8, "loading_percentage": 55.0, "status": "NORMAL | WARNING | OVERLOADED" } ],
  "summary": { "total_generation_mw": 120.0, "renewable_generation_mw": 40.0, "total_load_mw": 115.0, "total_losses_mw": 5.0, "minimum_voltage_pu": 0.97, "maximum_voltage_pu": 1.05, "maximum_line_loading": 55.0, "overloaded_lines": 0 },
  "impact_score": { "score": 15.2, "grade": "A", "categories": {}, "message": "Grid operating normally." }
}
```

**Error `409`:** `power_flow_not_converged` — includes `max_mismatch`, `iterations`  
**Error `503`:** `scilab_unavailable` — if Scilab explicitly requested but unavailable

### `POST /grids/{grid_id}/what-if`
Apply a renewable scenario and run power flow without modifying the stored grid.

**Request body:**
```json
{
  "solar_output_mw": 120.0,
  "wind_output_mw": 80.0,
  "battery_output_mw": null,
  "load_scale": 1.0,
  "engine": "auto"
}
```

**Response `200`:** `PowerFlowResult` (same as power-flow)

### `GET /engines`
List available computational engines.

**Response `200`:**
```json
{
  "engines": [
    { "name": "python", "available": true, "version": "3.12", "status": "available" },
    { "name": "scilab", "available": false, "version": null, "status": "not_found" }
  ],
  "default_engine": "python"
}
```

### `GET /engines/scilab/status`
Detailed Scilab capability report.

### `POST /compare-engines`
Run power flow with both engines and compare results.

**Request body:** `{ "grid": GridModel, ... }`  
**Response `200`:** `EngineComparisonResponse`

---

## Stress Analysis

### `POST /grids/{grid_id}/stress`
Run full stress analysis: power flow → issue detection → recommendations → mitigation candidates.

**Request body:** same as power-flow (optional engine/tolerance/max_iterations)

**Response `200`:** `AnalysisRecord`
```json
{
  "id": "string",
  "grid_id": "string",
  "scenario_id": "string | null",
  "result": { /* PowerFlowResult */ },
  "stress": { /* StressAnalysisResult with score, buses, lines, generation, renewable, issues */ },
  "recommendations": [ { "id": "...", "title": "...", "priority": "HIGH | MEDIUM | LOW", "description": "...", "suggested_actions": [] } ],
  "mitigation_candidates": [ { "id": "...", "name": "...", "modifications": [] } ],
  "mitigation_tests": []
}
```

### `GET /analyses/{analysis_id}/stress`
Retrieve a stored analysis record.

### `GET /analyses/{analysis_id}/mitigation-candidates`
List mitigation candidates for an analysis.

### `POST /analyses/{analysis_id}/mitigation-tests`
Execute mitigation tests.

**Request body:** `{ "mitigation_id": "string | null", "run_all": true }`  
**Response `200`:** `MitigationTestResult[]`

### `GET /analyses/{analysis_id}/export?format=json|csv`
Export analysis results.

### `POST /stress/comparative`
Compare a modified scenario against a baseline analysis.

---

## Case Studies

### `GET /case-studies`
**Response `200`:** `CaseStudyMetadata[]`
```json
[{ "id": "normal_operation", "name": "Normal Grid Operation", "description": "...", "objective": "..." }]
```

### `GET /case-studies/{case_id}`
**Response `200`:** `CaseStudyDetails` (includes grid, scenario, expected_conditions, readme)  
**Error `404`:** Case study not found

### `POST /case-studies/{case_id}/run`
Execute a case study end-to-end.

**Response `200`:** `CaseStudyRunResponse`
```json
{
  "case_id": "over_voltage",
  "status": "SUCCESS | FAILED",
  "steps": [
    { "name": "Validate Grid", "status": "SUCCESS", "message": "Grid is valid." },
    { "name": "Apply Renewable Scenario", "status": "SUCCESS", "message": null },
    { "name": "Analyze Grid Stress", "status": "SUCCESS", "message": null },
    { "name": "Detect Issues", "status": "SUCCESS", "message": "Detected 2 issues." },
    { "name": "Generate Recommendations", "status": "SUCCESS", "message": "Generated 3 recommendations." },
    { "name": "Test Mitigation", "status": "SKIPPED", "message": null },
    { "name": "Compare Results", "status": "SKIPPED", "message": null }
  ],
  "analysis": { /* PowerFlowResult */ },
  "issues": [],
  "recommendations": []
}
```

---

## Reporting

### `POST /analysis/{analysis_id}/report`
Generate a report.

**Request body:** `{ "format": "json | csv | markdown" }`  
**Response:**
- JSON: `200` with report object
- CSV: `200` with `text/csv`, `Content-Disposition: attachment`
- Markdown: `200` with `text/plain`, `Content-Disposition: attachment`

---

## Demo

### `POST /demo/reset`
Clear all in-memory analysis records and reload bundled sample grids.

**Response `200`:**
```json
{ "status": "reset", "message": "Demo state cleared. Sample grids reloaded.", "grids_loaded": ["sample", "demo"] }
```

---

## Error Codes

| Code | HTTP | Meaning |
|------|------|---------|
| `grid_not_found` | 404 | Grid ID does not exist |
| `analysis_not_found` | 404 | Analysis ID does not exist |
| `invalid_grid` | 422 | Grid topology/parameters are invalid |
| `invalid_engine` | 422 | Unknown engine name |
| `power_flow_not_converged` | 409 | Newton-Raphson did not converge |
| `scilab_unavailable` | 503 | Scilab explicitly requested but not installed |
| `internal_error` | 500 | Unexpected server error |
| `network_error` | 0 | Frontend cannot reach backend |

---

## Enum Reference

**BusType:** `SLACK | PV | PQ`  
**BusStatus:** `NORMAL | WARNING | CRITICAL`  
**LineStatus:** `NORMAL | WARNING | OVERLOADED`  
**GeneratorType:** `CONVENTIONAL | SOLAR | WIND | STORAGE`  
**Engine names:** `python | scilab | auto`  
**Stress levels:** `LOW | MODERATE | HIGH | CRITICAL`  
**Priority:** `LOW | MEDIUM | HIGH`  
**Impact level:** `POSITIVE | NEUTRAL | NEGATIVE | HIGH_RISK`
