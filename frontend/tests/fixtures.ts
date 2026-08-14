import { vi } from 'vitest';
import { API_BASE } from '../src/api/client';
import type { ApiErrorDetail, GridModel, PowerFlowResult } from '../src/types';

export const sampleGrid: GridModel = {
  grid_id: 'sample',
  name: '5-bus sample',
  base_mva: 100,
  buses: [
    { id: 'B1', name: 'Slack', type: 'SLACK', base_voltage: 138, voltage_magnitude: 1.06, voltage_angle: 0 },
    { id: 'B2', name: 'PV1', type: 'PV', base_voltage: 138, voltage_magnitude: 1.04, voltage_angle: 0.66 },
    { id: 'B3', name: 'PV2', type: 'PV', base_voltage: 138, voltage_magnitude: 1.02, voltage_angle: 0.94 },
    { id: 'B4', name: 'Load A', type: 'PQ', base_voltage: 138, voltage_magnitude: 1.0, voltage_angle: -2.34 },
    { id: 'B5', name: 'Load B', type: 'PQ', base_voltage: 138, voltage_magnitude: 1.0, voltage_angle: -2.3 },
  ],
  lines: [
    { id: 'L1', name: 'L1', from_bus: 'B1', to_bus: 'B2', resistance: 0.02, reactance: 0.06, susceptance: 0.03, thermal_limit: 100 },
    { id: 'L2', name: 'L2', from_bus: 'B1', to_bus: 'B4', resistance: 0.08, reactance: 0.24, susceptance: 0.025, thermal_limit: 100 },
    { id: 'L3', name: 'L3', from_bus: 'B2', to_bus: 'B3', resistance: 0.06, reactance: 0.18, susceptance: 0.02, thermal_limit: 100 },
    { id: 'L4', name: 'L4', from_bus: 'B2', to_bus: 'B5', resistance: 0.06, reactance: 0.18, susceptance: 0.02, thermal_limit: 100 },
    { id: 'L5', name: 'L5', from_bus: 'B3', to_bus: 'B4', resistance: 0.04, reactance: 0.12, susceptance: 0.015, thermal_limit: 100 },
    { id: 'L6', name: 'L6', from_bus: 'B4', to_bus: 'B5', resistance: 0.01, reactance: 0.03, susceptance: 0.01, thermal_limit: 100 },
    { id: 'L7', name: 'L7', from_bus: 'B1', to_bus: 'B3', resistance: 0.04, reactance: 0.12, susceptance: 0.015, thermal_limit: 100 },
  ],
  generators: [
    { id: 'G1', name: 'Slack Gen', bus_id: 'B1', type: 'CONVENTIONAL', active_power: 17.5, reactive_power: 66, active_power_min: 0, active_power_max: 300, reactive_power_min: -100, reactive_power_max: 100, capacity_mwh: 0 },
    { id: 'G2', name: 'PV Gen 1', bus_id: 'B2', type: 'CONVENTIONAL', active_power: 40, reactive_power: 20, active_power_min: 0, active_power_max: 200, reactive_power_min: -60, reactive_power_max: 60, capacity_mwh: 0 },
    { id: 'G3', name: 'PV Gen 2', bus_id: 'B3', type: 'CONVENTIONAL', active_power: 60, reactive_power: -20, active_power_min: 0, active_power_max: 200, reactive_power_min: -60, reactive_power_max: 60, capacity_mwh: 0 },
  ],
  loads: [
    { id: 'D1', name: 'Load A', bus_id: 'B4', active_power: 65, reactive_power: 30 },
    { id: 'D2', name: 'Load B', bus_id: 'B5', active_power: 50, reactive_power: 25 },
  ],
};

export const scenarioGrid: GridModel = {
  ...sampleGrid,
  buses: sampleGrid.buses.map((bus) => (bus.id === 'B4' ? { ...bus, type: 'PQ' } : bus)),
  loads: sampleGrid.loads.map((load) =>
    load.id === 'D1' ? { ...load, active_power: 85, reactive_power: 40 } : load,
  ),
};

export const sampleResult: PowerFlowResult = {
  grid_id: 'sample',
  engine: 'python',
  status: 'success',
  converged: true,
  iterations: 4,
  max_mismatch: 1e-11,
  execution_time_ms: 1.5,
  buses: [
    { bus_id: 'B1', voltage_magnitude: 1.06, voltage_angle: 0, active_power: 17.5, reactive_power: 66, status: 'WARNING' },
    { bus_id: 'B2', voltage_magnitude: 1.04, voltage_angle: 0.66, active_power: 60, reactive_power: 7.8, status: 'NORMAL' },
    { bus_id: 'B3', voltage_magnitude: 1.02, voltage_angle: 0.94, active_power: 40, reactive_power: -24.6, status: 'NORMAL' },
    { bus_id: 'B4', voltage_magnitude: 0.997, voltage_angle: -2.34, active_power: -65, reactive_power: -30, status: 'NORMAL' },
    { bus_id: 'B5', voltage_magnitude: 0.996, voltage_angle: -2.3, active_power: -50, reactive_power: -25, status: 'NORMAL' },
  ],
  lines: [
    { line_id: 'L1', from_bus: 'B1', to_bus: 'B2', active_power_from: -8.7, reactive_power_from: 27.6, active_power_to: 8.9, reactive_power_to: -29.2, loading_percentage: 11.6, status: 'NORMAL' },
    { line_id: 'L2', from_bus: 'B1', to_bus: 'B4', active_power_from: 28.2, reactive_power_from: 25.4, active_power_to: -27.5, reactive_power_to: -24.9, loading_percentage: 19.0, status: 'NORMAL' },
    { line_id: 'L3', from_bus: 'B2', to_bus: 'B3', active_power_from: 12.3, reactive_power_from: 3.0, active_power_to: -12.1, reactive_power_to: -2.8, loading_percentage: 8.0, status: 'NORMAL' },
    { line_id: 'L4', from_bus: 'B2', to_bus: 'B5', active_power_from: 38.0, reactive_power_from: 11.0, active_power_to: -37.4, reactive_power_to: -10.4, loading_percentage: 22.0, status: 'NORMAL' },
    { line_id: 'L5', from_bus: 'B3', to_bus: 'B4', active_power_from: 28.0, reactive_power_from: -21.0, active_power_to: -27.4, reactive_power_to: 21.6, loading_percentage: 21.5, status: 'NORMAL' },
    { line_id: 'L6', from_bus: 'B4', to_bus: 'B5', active_power_from: 5.4, reactive_power_from: 13.6, active_power_to: -5.4, reactive_power_to: -13.3, loading_percentage: 14.0, status: 'NORMAL' },
    { line_id: 'L7', from_bus: 'B1', to_bus: 'B3', active_power_from: -2.6, reactive_power_from: 13.1, active_power_to: 2.6, reactive_power_to: -12.9, loading_percentage: 11.0, status: 'NORMAL' },
  ],
  summary: {
    total_generation_mw: 117.5,
    renewable_generation_mw: 0,
    total_load_mw: 115,
    total_losses_mw: 2.5,
    minimum_voltage_pu: 0.996,
    maximum_voltage_pu: 1.06,
    maximum_line_loading: 22.0,
    overloaded_lines: 0,
  },
  impact_score: { score: 96.7, grade: 'A', categories: {}, message: 'Grid is healthy.' },
};

export const scenarioResult: PowerFlowResult = {
  ...sampleResult,
  summary: {
    ...sampleResult.summary!,
    total_generation_mw: 137.5,
    total_load_mw: 135,
    total_losses_mw: 2.5,
    maximum_voltage_pu: 1.06,
  },
  impact_score: { score: 94.2, grade: 'A', categories: {}, message: 'Grid is healthy.' },
};

export const whatIfResult: PowerFlowResult = {
  ...sampleResult,
  summary: {
    ...sampleResult.summary!,
    total_generation_mw: 137.5,
    renewable_generation_mw: 100,
    total_losses_mw: 3.1,
  },
  impact_score: { score: 97.2, grade: 'A', categories: {}, message: 'Grid is healthy.' },
};

type MockHandler = (init?: RequestInit) => { status: number; body?: unknown };

export function installFetchMock(routes: Record<string, MockHandler>) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const raw = String(input);
    const path = raw.replace(API_BASE, '');
    const method = (init?.method ?? 'GET').toUpperCase();
    const key = `${method} ${path}`;
    const handler = routes[key];
    if (!handler) {
      const detail: ApiErrorDetail = { code: 'not_found', message: `No mock for ${key}` };
      return new Response(JSON.stringify({ detail }), {
        status: 404,
        headers: { 'Content-Type': 'application/json' },
      });
    }
    const result = handler(init);
    return new Response(result.body === undefined ? null : JSON.stringify(result.body), {
      status: result.status,
      headers: { 'Content-Type': 'application/json' },
    });
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

export function baseRoutes() {
  return {
    'GET /grids': () => ({ status: 200, body: [sampleGrid] }),
    'GET /grids/sample': () => ({ status: 200, body: sampleGrid }),
    'POST /grids/sample/validate': () => ({ status: 200, body: { valid: true, errors: [] } }),
    'GET /grids/sample/scenarios': () => ({ status: 200, body: [] }),
  };
}
