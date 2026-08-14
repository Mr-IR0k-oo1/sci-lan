# GridFlex Grid Designer

The Grid Designer is the interactive frontend that sits in front of the GridFlex power-flow API. This document describes its architecture, the data flow, and the guarantees it provides.

## Stack

- **React 19 + TypeScript (strict)** — UI and state.
- **Vite 6** — dev server and production build.
- **Vitest + Testing Library + jsdom** — unit and integration tests (35 tests).
- **No chart library** — charts are lightweight inline SVG components.
- **No Redux** — state lives in five small React contexts.

## Layout

```
┌────────────────────────────────────────────┐
│ TopBar: grid selector, New, Save, Run      │
├──────────┬─────────────────────┬───────────┤
│ Left     │ Canvas (SVG)        │ Right     │
│ Palette  │  – drag buses       │ Properties│
│ Scenario │  – line tool        │ Validation│
│ What-if  │  – result overlays  │           │
├──────────┴─────────────────────┴───────────┤
│ Results: Summary / Voltage / Lines / Compare│
└────────────────────────────────────────────┘
```

## State contexts

All providers live in `src/components/workspace/Workspace.tsx`:

| Context | Responsibility |
| --- | --- |
| `SelectionContext` | currently selected component + line tool state |
| `GridContext` | base grid, dirty flag, positions, `GridEditor` ops |
| `ScenarioContext` | scenario list, draft editing, scenario runs |
| `AnalysisContext` | validate → power flow run for the base grid |
| `WhatIfContext` | temporary what-if overrides + result |

`GridEditor` is the single edit surface shared by the base grid and the scenario
draft. It exposes `addBus/updateBus/removeBus`, `addLine/updateLine/removeLine`,
`addGenerator/updateGenerator/removeGenerator`, `addLoad/updateLoad/removeLoad`,
and `moveBus`. The scenario draft editor implements `moveBus` as a no-op so the
scenario keeps the base layout.

## Data flow

1. On mount the workspace loads the available grids (`GET /grids`) and auto-loads
   the first one (`GET /grids/{id}`).
2. Editing goes through `GridEditor`; every mutation replaces the grid
   immutably (`src/lib/gridEdit.ts`) and marks it dirty.
3. **Run Analysis** auto-saves a dirty grid (`PUT /grids/{id}`), validates it
   (`POST /grids/{id}/validate`), then runs the power flow
   (`POST /grids/{id}/analyze/power-flow`). Validation errors are shown in the
   right panel and clickable to select the offending component.
4. Results power the Summary/Voltage/Lines tabs and the canvas overlays
   (bus voltage, line loading, status colors).
5. The **Compare** tab compares the base result with a scenario result using
   `src/lib/comparison.ts`.

## Scenarios

- A scenario is a deep copy of the grid stored server-side
  (`POST /grids/{id}/scenarios`). The returned `Scenario` carries the full grid.
- **Edit** loads that snapshot into a draft and enters **SCENARIO MODE**. All
  edits apply to the draft; the base grid is never modified. `Save Scenario`
  upserts the draft via `POST /grids/{id}/scenarios` with the original `id`.
- Running a scenario analyzes the stored snapshot
  (`POST /grids/{id}/scenarios/{sid}/analyze`); results are kept locally per
  scenario id.

## What-if

- Sliders set overrides (solar, wind, battery, load scale); after a 400 ms
  debounce the panel posts `POST /grids/{id}/what-if`.
- The backend applies the overrides to a copy of the grid and never persists
  anything. The UI marks results as **TEMPORARY**.

## Canvas

- Buses are placed from `positions` (frontend-only metadata). Missing positions
  fall back to a circle layout (`src/lib/positions.ts`).
- Drag updates positions only (not the grid model), so moving a bus never marks
  the grid dirty.
- Buses show their type and, after a run, voltage. Lines show loading
  percentage; status colors come from the result.
- Keyboard: `Delete`/`Backspace` removes the selection, `Escape` clears the line
  tool and selection.

## Editing rules

- Numeric fields (`NumberField`) only propagate **valid** values; empty,
  out-of-range, or non-numeric input shows an inline error and never reaches the
  model.
- Removing a bus cascades to its lines, generators, and loads
  (`gridEdit.removeBus`).

## Testing

- `tests/gridEdit.test.ts` — pure editing helpers.
- `tests/comparison.test.ts` — comparison builders.
- `tests/issues.test.ts` — validation issue → component mapping.
- `tests/apiClient.test.ts` — error mapping (network, convergence, HTTP).
- `tests/workspace.test.tsx` — integration: load, edit, save, analyze (success
  and non-converged), invalid-number rejection.
- `tests/scenarios.test.tsx` — create/run/edit/delete; base grid protection.
- `tests/whatif.test.tsx` — temporary isolation, request payload shape.

Run: `npm test` (vitest), `npm run typecheck` (tsc -b), `npm run build`.

## Backend contract used by the frontend

All requests go through `/api/v1` (vite proxies `/api` to `127.0.0.1:8000`).

- `GET /grids`, `POST /grids`, `GET/PUT /grids/{id}`
- `POST /grids/{id}/validate`
- `POST /grids/{id}/analyze/power-flow`
- `POST /grids/{id}/what-if`
- `GET/POST /grids/{id}/scenarios`, `GET/DELETE /grids/{id}/scenarios/{sid}`, `POST .../analyze`
- `GET /engines`
